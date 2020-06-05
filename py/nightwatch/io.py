'''
I/O routines for QA
'''

import os
import glob
import numpy as np
import fitsio
import json

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

def findfibers(datadir, fibers):
    '''
    Searches fibermaps in datadir/qframe*.fits for fibers

    Args:
        datadir : directory with qframe*.fits files
        fibers : array of fiber numbers to look for

    Returns (fibergroups, missingfibers) where
        fibergroups[spectroid] = list of fibers on that spectrograph, and
        missingfibers = array of fibers not found in any of the qframe files

    We're in a state of transition for how [brz]N maps to fiber numbers,
    such that nightwatch can't apriori know which fibers will be in which
    files, so this is a brute force search.
    '''
    fibers = np.asarray(fibers)

    #- Pick one framefile per spectrograph
    #- Use sorted(glob(...)) for reproducibility of which file is picked
    framefiles = dict()
    for filename in sorted(glob.glob(os.path.join(datadir, 'qframe-*.fits'))):
        prefix, camera, suffix = os.path.basename(filename).split('-')
        spectro = int(camera[1])
        framefiles[spectro] = filename

    #- Look for fibers in those framefiles
    fibergroups = dict()
    missing = np.ones(len(fibers), dtype=bool)
    for spectro, filename in framefiles.items():
        fm = fitsio.read(filename, 'FIBERMAP', columns=['FIBER'])
        ii = np.in1d(fibers, fm['FIBER'])
        if np.any(ii):
            prefix, camera, suffix = os.path.basename(filename).split('-')
            spectro = int(camera[1])
            fibergroups[spectro] = fibers[ii]
            missing[ii] = False

    return fibergroups, fibers[missing]

def get_night_expid(filename):
    '''
    Returns NIGHT, EXPID from input filename header keywords
    '''
    #- First try HDU 0
    hdr = fitsio.read_header(filename, 0)
    if 'NIGHT' in hdr and 'EXPID' in hdr:
        return int(hdr['NIGHT']), int(hdr['EXPID'])

    #- not found there, try HDU 1 before giving up
    try:
        hdr = fitsio.read_header(filename, 1)
    except OSError:
        from desiutil.log import get_logger
        log = get_logger()
        log.error('fitsio error reading HDU 1; trying HDU 2 before giving up')
        hdr = fitsio.read_header(filename, 2)

    if 'NIGHT' in hdr and 'EXPID' in hdr:
        return int(hdr['NIGHT']), int(hdr['EXPID'])

    raise ValueError('NIGHT and/or EXPID not found in HDU 0 or 1 of {}'.format(filename))
    
def get_guide_data(night, expid, basedir):
    '''Given a night and exposure, dumps centroid-*.json file into a dictionary. Note: no padding zeros for expid argument.
    Args:
        night:
        expid:
        basedir:
    returns dictionary object.'''
    guidedir = os.path.join(basedir, '{night}/{expid:08d}'.format(night=night, expid=expid)) 
    infile = os.path.join(guidedir, 'centroids-{expid:08d}.json'.format(night=night, expid=expid))

    with open(infile) as fx:
        guidedata = json.load(fx)
    
    return guidedata

def get_guide_images(night, expid, basedir):
    '''Docstring here'''
    guidedir = os.path.join(basedir, '{night}/{expid:08d}'.format(night=night, expid=expid))
    infile = os.path.join(guidedir, 'guide-rois-{expid:08d}.fits.fz'.format(night=night, expid=expid))
    return infile
    
    
