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

def findfile(filetype, night, expid=None, basedir=''):
    filemap = dict(
        qa = '{night}/{expid:08d}/qa-{expid:08d}.fits',
    )
    if filetype not in filemap:
        raise ValueError('Unknown filetype {}; known types {}'.format(
            filetype, list(filemap.keys()) ))

    qafile = filemap[filetype].format(night=night, expid=expid)
    qafile = os.path.join(basedir, qafile)
    return qafile
