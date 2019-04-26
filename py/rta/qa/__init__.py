import glob

import numpy as np
import fitsio
from astropy.table import join, Table

import desiutil.log

from .amp import QAAmp
# from .fibersnr import QAFiberSNR

def run(indir, qalist=None):
    qarunner = QARunner(qalist)
    return qarunner.run(indir)

class QARunner():
    def __init__(self, qalist=None):
        '''TODO: document'''
        if qalist is None:
            qalist = [QAAmp,]

        #- Runner keeps instances, not just their classes
        self.qalist = [X() for X in qalist]


    def run(self, indir, outdir=None, flavor=None):
        '''TODO: document'''
        log = desiutil.log.get_logger()
        log.debug('Running QA in {}'.format(indir))
        
        if flavor is None:
            for prefix in ('preproc', 'desi', 'qframe', 'frame'):
                datafiles = glob.glob('{}/{}*.fits'.format(indir, prefix))
                if len(datafiles) > 0:
                    break

            else:  #- else of for loop, in case we didn't break out
                log.error('No preproc, desi, or (q)frame files found to derive FLAVOR')
                raise RuntimeError
            
            hdr = fitsio.read_header(datafiles[0], 0)
            flavor = hdr['FLAVOR'].strip()
            log.debug('Found FLAVOR={} files'.format(flavor))

        results = dict()
        for qa in self.qalist:
            if qa.valid_flavor(flavor):
                log.debug('Running {} {}'.format(qa, qa.output_type))
                try:
                    qa_results = qa.run(indir)
                except Exception as err:
                    log.warning('{} failed on {}; skipping'.format(qa, indir))
                    ### raise(err)
                    #- TODO: print traceback somewhere useful

                if qa.output_type not in results:
                    results[qa.output_type] = list()
                
                results[qa.output_type].append(qa_results)

        #- Combine results for different types of QA
        join_keys = dict(
            PER_AMP = ['NIGHT', 'EXPID', 'SPECTRO', 'CAM', 'AMP'],
            PER_CAMERA = ['NIGHT', 'EXPID', 'SPECTRO', 'CAM'],
            PER_FIBER = ['NIGHT', 'EXPID', 'SPECTRO', 'FIBER'],
            PER_CAMFIBER = ['NIGHT', 'EXPID', 'SPECTRO', 'CAM', 'FIBER'],
            PER_SPECTRO = ['NIGHT', 'EXPID', 'SPECTRO'],
            PER_EXP = ['NIGHT', 'EXPID'],
        )
        for qatype in list(results.keys()):
            if len(results[qatype]) == 1:
                results[qatype] = results[qatype][0]
            else:
                tx = results[qatype][0]
                for i in range(1, len(results[qatype])):
                    tx = join(tx, results[qatype][i], keys=join_keys[qatype], join_type='outer')
                results[qatype] = tx
            
            #- convert python string to bytes for FITS format compatibility
            if 'AMP' in results[qatype].colnames:
                results[qatype]['AMP'] = results[qatype]['AMP'].astype('S1')
            if 'CAM' in results[qatype].colnames:
                results[qatype]['CAM'] = results[qatype]['CAM'].astype('S1')

            #- TODO: NIGHT/EXPID/SPECTRO/FIBER int64 -> int32 or int16
            #- TODO: metrics from float64 -> float32

        if outdir is not None:
            for tx in results.values():
                night = tx['NIGHT'][0]
                expid = tx['EXPID'][0]
                break

            #- To do: consider propagating header from indir/desi*.fits.fz
            outfile = '{}/qa-{:08d}.fits'.format(outdir, expid)
            hdr = dict(NIGHT=night, EXPID=expid)
            with fitsio.FITS(outfile, 'rw', clobber=True) as fx:
                fx.write(np.zeros(3, dtype=float), extname='PRIMARY', header=hdr)
                for qatype, qatable in results.items():
                    fx.write_table(qatable.as_array(), extname=qatype, header=hdr)

        return results









