from .base import QA
import glob
import os
import collections

import numpy as np
import fitsio

from astropy.table import Table

import desiutil.log
from desispec.maskbits import ccdmask

def _fix_amp_names(hdr):
    '''In-place fix of header `hdr` amp names 1-4 to A-D if needed.'''
    #- Assume that if any are right, all are right
    if 'DATASECA' in hdr:
        return

    log = desiutil.get_logger()
    log.debug('Correcting AMP 1-4 to A-D for night {} expid {}'.format(
        hdr['NIGHT'], hdr['EXPID']))

    for prefix in [
        'GAIN', 'RDNOISE', 'PRESEC', 'PRRSEC', 'DATASEC', 'TRIMSEC', 'BIASSEC',
        'ORSEC', 'CCDSEC', 'DETSEC', 'AMPSEC',
        ]:
        for ampnum, ampname in [('1','A'), ('2','B'), ('3','C'), ('4','D')]:
            if prefix+ampnum in hdr:
                hdr[prefix+ampname] = hdr[prefix+ampnum]
                del hdr[prefix+ampnum]


class QAAmp(QA):
    """docstring for QAAmp"""
    def __init__(self):
        self.output_type = "PER_AMP"
        pass

    def valid_flavor(self, flavor):
        '''PER_AMP QA metrics work for all flavors of exposures'''
        return True

    def run(self, indir):
        '''TODO: document'''
        infiles = glob.glob(os.path.join(indir, 'preproc-*.fits'))
        results = list()
        for filename in infiles:
            hdr = fitsio.read_header(filename, 'IMAGE') #- for readnoise, bias
            mask = fitsio.read(filename, 'MASK')        #- for cosmics
            _fix_amp_names(hdr)
            night = hdr['NIGHT']
            expid = hdr['EXPID']
            cam = hdr['CAMERA'][0].upper()
            spectro = int(hdr['CAMERA'][1])

            #- for cosmics, use exposure time + half of readout time
            exptime = hdr['EXPTIME']
            if 'DIGITIME' in hdr:
                exptime += hdr['DIGITIME']/2
            else:
                exptime += 30.0

            ny, nx = mask.shape
            npix_amp = nx*ny//4
            for amp in ['A', 'B', 'C', 'D']:
                #- CCD read noise and overscan offset (bias) level
                readnoise = hdr['OBSRDN'+amp]
                biaslevel = hdr['OVERSCN'+amp]
                    
                #- Subregion of mask covered by this amp
                if amp == 'A':
                    submask = mask[0:ny//2, 0:nx//2]
                elif amp == 'B':
                    submask = mask[0:ny//2, nx//2:]
                elif amp == 'C':
                    submask = mask[ny//2:, 0:nx//2]
                else:
                    submask = mask[ny//2:, nx//2:]
        
                #- Pixels hit by cosmics per second of exposure time
                npix_cosmics = np.count_nonzero(submask & ccdmask.COSMIC)
                cosmics_rate = (npix_cosmics / npix_amp) / exptime

                results.append(collections.OrderedDict(
                    NIGHT=night, EXPID=expid, SPECTRO=spectro, CAM=cam, AMP=amp,
                    READNOISE=readnoise,
                    BIAS=biaslevel,
                    COSMICS_RATE=cosmics_rate)
                    )

        return Table(results, names=results[0].keys())

            
            
        