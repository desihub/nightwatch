'''
I/O routines for QA
'''

import os
import glob
import numpy as np
import fitsio
import json
from astropy.io import fits
from astropy.table import Table

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
        night: int
        expid: int (no padding zeros)
        basedir: directory of where to look for centroids-*.json files (without YYYYMMDD/EXPID)
    returns dictionary object.'''
    guidedir = os.path.join(basedir, '{night}/{expid:08d}'.format(night=night, expid=expid)) 
    infile = os.path.join(guidedir, 'centroids-{expid:08d}.json'.format(night=night, expid=expid))

    with open(infile) as fx:
        guidedata = json.load(fx)
    
    return guidedata

def get_guide_images(night, expid, basedir, rot=False):
    '''Given a night and exposure, return file containing raw guide images.
    Args:
        night: int
        expid: int (no padding zeros)
        basedir: directory of where raw data is kept
    returns path to file.'''
    guidedir = os.path.join(basedir, '{night}/{expid:08d}'.format(night=night, expid=expid))
    infile = os.path.join(guidedir, 'guide-rois-{expid:08d}.fits.fz'.format(night=night, expid=expid))
    print(infile)
    
    image_data = dict()
    
    gfa_file = os.path.expandvars('$DESIMODEL/data/focalplane/gfa.ecsv')
    rotdict = rot_dict(gfa_file)
    
    for cam in [0, 2, 3, 5, 7, 8]:
        name0 = 'GUIDE{cam}_{star}'.format(cam=cam, star=0)
        name1 = 'GUIDE{cam}_{star}'.format(cam=cam, star=1)
        name2 = 'GUIDE{cam}_{star}'.format(cam=cam, star=2)
        name3 = 'GUIDE{cam}_{star}'.format(cam=cam, star=3)
        #name = 'GUIDE{cam}'.format(cam=cam)
        
        angle = rotdict[str(cam)]
        
        with fitsio.FITS(infile) as f:
            try:
                data = f[name0].read()
                if rot == True:
                    data = rotate(data, angle, axes=(1, 2), reshape=False, mode='nearest')
                image_dict = dict()
                for idx in range(len(data)):
                    image_dict[idx] = data[idx]
                image_data[name0] = image_dict
            except IOError:
                print('no images for {name}'.format(name=name0))
            try:
                data = f[name1].read()
                if rot == True:
                    data = rotate(data, angle, axes=(1, 2), reshape=False, mode='nearest')
                image_dict = dict()
                for idx in range(len(data)):
                    image_dict[idx] = data[idx]
                image_data[name1] = image_dict
            except IOError:
                print('no images for {name}'.format(name=name1))
            try:
                data = f[name2].read()
                if rot == True:
                    data = rotate(data, angle, axes=(1, 2), reshape=False, mode='nearest')
                image_dict = dict()
                for idx in range(len(data)):
                    image_dict[idx] = data[idx]
                image_data[name2] = image_dict
            except IOError:
                print('no images for {name}'.format(name=name2))
            try:
                data = f[name3].read()
                if rot == True:
                    data = rotate(data, angle, axes=(1, 2), reshape=False, mode='nearest')
                image_dict = dict()
                for idx in range(len(data)):
                    image_dict[idx] = data[idx]
                image_data[name3] = image_dict
            except IOError:
                print('no images for {name}'.format(name=name3))

    return image_data
    
def rot_dict(gfa_file):
    '''returns dictionary of angles to rotate gfas to global X, Y coord system.'''
    
    table = Table.read(gfa_file, format='ascii.ecsv')
    
    rot_dict = {
        '0': -table['Q'][1],
        '2': -table['Q'][9],
        '3': -table['Q'][13],
        '5': -table['Q'][21],
        '7': -table['Q'][29],
        '8': -table['Q'][33]
        }

    return rot_dict