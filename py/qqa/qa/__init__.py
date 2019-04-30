import glob

import numpy as np
import fitsio
from astropy.table import join, Table

import desiutil.log

from .amp import QAAmp
from .specscore import QASpecscore

# from .fibersnr import QAFiberSNR

def run(indir, outfile=None, qalist=None):
    qarunner = QARunner(qalist)
    return qarunner.run(indir, outfile=outfile)

class QARunner():
    def __init__(self, qalist=None):
        '''TODO: document'''
        if qalist is None:
            qalist = [QAAmp,QASpecscore,]

        #- Runner keeps instances, not just their classes
        self.qalist = [X() for X in qalist]


    def run(self, indir, outfile=None):
        '''TODO: document'''
        log = desiutil.log.get_logger()
        log.debug('Running QA in {}'.format(indir))
        
        preprocfiles = sorted(glob.glob('{}/preproc-*.fits'.format(indir)))
        if len(preprocfiles) == 0:
            log.error('No preproc files found in {}'.format(indir))
            raise RuntimeError
            
        hdr = fitsio.read_header(preprocfiles[0], 0)
        flavor = hdr['FLAVOR'].strip()
        log.debug('Found FLAVOR={} files'.format(flavor))

        results = dict()
        for qa in self.qalist:
            if qa.valid_flavor(flavor):
                log.debug('Running {} {}'.format(qa, qa.output_type))
                qa_results = None
                try:
                    qa_results = qa.run(indir)
                except Exception as err:
                    log.warning('{} failed on {} because {}; skipping'.format(qa, indir,str(err)))
                    #raise(err)
                    #- TODO: print traceback somewhere useful

                if qa_results is not None :
                    if qa.output_type not in results:
                        results[qa.output_type] = list()
                    results[qa.output_type].append(qa_results)

            else :
                log.debug('Skip {} {} for {}'.format(qa, qa.output_type, flavor))
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

        if outfile is not None:
            for tx in results.values():
                night = tx['NIGHT'][0]
                expid = tx['EXPID'][0]
                break

            #- To do: consider propagating header from indir/desi*.fits.fz
            with fitsio.FITS(outfile, 'rw', clobber=True) as fx:
                fx.write(np.zeros(3, dtype=float), extname='PRIMARY', header=hdr)
                for qatype, qatable in results.items():
                    fx.write_table(qatable.as_array(), extname=qatype, header=hdr)

        return results









