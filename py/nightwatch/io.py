'''
I/O routines for QA
'''

import os
import numpy as np
import fitsio

def read_qa(filename):
    '''
    Read QA data from qa-EXPID.fits file
    
    Returns qadata dict with keys HEADER, plus any PER_XYZ EXTNAMEs in the
    input file, and FIBERMAP if it is in the input file
    '''
    qadata = dict()
    with fitsio.FITS(filename) as fx:
        qadata['HEADER'] = fx[0].read_header()
        for hdu in fx:
            extname = hdu.get_extname()
            if extname.startswith('PER_') or extname == 'FIBERMAP':
                qadata[extname] = hdu.read()
    
    return qadata

def findfile(filetype, night, expid=None, basedir=None):
    '''
    Returns standardized filepath given a type, night, exposure, basedir
    Currently supported types: qa, expdir
    '''
    filemap = dict(
        qa = '{night}/{expid:08d}/qa-{expid:08d}.fits',
        expdir = '{night}/{expid:08d}'
    )
    if filetype not in filemap:
        raise ValueError('Unknown filetype {}; known types {}'.format(
            filetype, list(filemap.keys()) ))

    filename = filemap[filetype].format(night=night, expid=expid)
    if basedir is not None:
        filename = os.path.join(basedir, filename)

    return filename

def get_night_expid(filename):
    '''
    Returns NIGHT, EXPID from input filename header keywords
    '''
    #- First try HDU 0
    hdr = fitsio.read_header(filename, 0)
    if 'NIGHT' in hdr and 'EXPID' in hdr:
        return int(hdr['NIGHT']), int(hdr['EXPID'])

    #- not found there, try HDU 1 before giving up
    hdr = fitsio.read_header(filename, 1)
    if 'NIGHT' in hdr and 'EXPID' in hdr:
        return int(hdr['NIGHT']), int(hdr['EXPID'])

    raise ValueError('NIGHT and/or EXPID not found in HDU 0 or 1 of {}'.format(filename))
