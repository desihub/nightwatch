from .base import QA
import glob
import os
import collections

import numpy as np
import fitsio

import multiprocessing as mp

import scipy.ndimage

from astropy.table import Table

import desiutil.log
from desispec.maskbits import ccdmask
from ..run import get_ncpu

def _fix_amp_names(hdr):
    '''In-place fix of header `hdr` amp names 1-4 to A-D if needed.'''
    #- Assume that if any are right, all are right
    if 'DATASECA' in hdr:
        return

    log = desiutil.log.get_logger()
    log.debug('Correcting AMP 1-4 to A-D for night {} expid {}'.format(
        hdr['NIGHT'], hdr['EXPID']))

    for prefix in [
        'GAIN', 'RDNOISE', 'PRESEC', 'PRRSEC', 'DATASEC', 'TRIMSEC', 'BIASSEC',
        'ORSEC', 'CCDSEC', 'DETSEC', 'AMPSEC', 'OBSRDN', 'OVERSCN'
        ]:
        for ampnum, ampname in [('1','A'), ('2','B'), ('3','C'), ('4','D')]:
            if prefix+ampnum in hdr:
                hdr[prefix+ampname] = hdr[prefix+ampnum]
                hdr.delete(prefix+ampnum)


class QAAmp(QA):
    """docstring for QAAmp"""
    def __init__(self):
        self.output_type = "PER_AMP"
        pass

    def valid_obstype(self, obstype):
        '''PER_AMP QA metrics work for all obstypes of exposures'''
        return True

    def count_cosmics(self, mask):
        '''
        Count number of cosmics in this mask; doesn't try to deblend
        overlapping cosmics
        '''
        cosmics_mask = mask & ccdmask.COSMIC

        #- Any nonzero adjacent pixels count as connected, even if diagonal
        structure=np.ones((3,3))
        num_cosmics = scipy.ndimage.label(cosmics_mask, structure=structure)[1]

        return num_cosmics

    def run(self, indir):
        '''Generates table of PER_AMP qa metrics (READNOISE, BIAS, COSMICS_RATE).
        Args:
            indir: path to directory containing preproc-*.fits files for the given exposure
        Returns an astropy Table object.'''
        infiles = glob.glob(os.path.join(indir, 'preproc-*.fits'))
        results = list()
        argslist = [(self, infile, amp) for infile in infiles for amp in ['A', 'B', 'C', 'D']]
        
        ncpu = get_ncpu(None)
        
        if ncpu > 1:
            pool = mp.Pool(ncpu)
            results = pool.starmap(get_dico, argslist)
            pool.close()
            pool.join()
            
        else:
            for args in argslist:
                results.append(get_dico(**args))

        #- remove None entries from missing amp (e.g. 2-amp readout)
        results = [r for r in results if r is not None]

        table = Table(results, names=results[0].keys())
        
        return table
           
def get_dico(self, filename, amp):
    '''Function to generate per amp metrics given a preproc file to analyze, and a specific amp.
    Args:
        filename: path to preproc file (str)
        amp: name of amp to analyze (str), either A, B, C, or D
    Returns an OrderedDict object or None if amp isn't in data.
    '''
    
    hdr = fitsio.read_header(filename, 'IMAGE') #- for readnoise, bias

    if 'BIASSEC'+amp not in hdr.keys():
        return None

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

    #- Fraction of the amp pixels masked out, for any reason.
    frmask = np.sum(submask != 0) / submask.size

    #- Number of cosmics per minute on this amplifier
    num_cosmics = self.count_cosmics(submask)
    cosmics_rate = (num_cosmics / (exptime/60) )

    dico = {'NIGHT': night, 'EXPID': expid, 'SPECTRO': spectro, 'CAM': cam, 'AMP': amp,
            'READNOISE': readnoise, 'BIAS': biaslevel, 'COSMICS_RATE': cosmics_rate,
            'FRAC_MASKED': frmask
           }
        
    return collections.OrderedDict(**dico)

        
