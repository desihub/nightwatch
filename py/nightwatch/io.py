'''
I/O routines for QA
'''

import os, sys, shutil
import re
from os import walk
import glob
import numpy as np
import fitsio
import json
from astropy.io import fits
from astropy.table import Table
import bokeh
import urllib.request
from pathlib import PurePath


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

def get_surveyqa_data(infile, name_dict, rawdir, program=True):
    '''Given surveyqa data file, file of tile data, and dictionary containing equivalent columns, returns
    two tables of data to feed into surveyqa code.
    Args:
        infile: (str) path to file containing surveyqa data
        name_dict: dictionary with column equivalents
            Must have equivalents for AIRMASS, SKY, SEEING, TRANSP, RA, DEC, MJD, NIGHT, EXPID.
        rawdir: directory containing raw data files
    Options:
        program: whether or not to use hardcoded information to assign programs to tileids, default=True
    Returns: two tables, one with aggregated data by exposure, and one with the finer scaled data.'''
    
    table = Table.read(infile, hdu=1)
    
    new_table = Table()
    for key in name_dict.keys():
        new_table[key] = table[name_dict[key]]
    
    D = new_table["MJD"] - 51544.5
    LST = (168.86072948111115 + 360.98564736628623 * D) % 360
    new_table["HOURANGLE"] = LST - new_table["RA"]
    
    def change_range(i):
        if i > 180:
            return i - 360
        if i < -180:
            return 360 + i
        return i

    new_table["HOURANGLE"] = [change_range(i) for i in new_table["HOURANGLE"]]
    
    table_by_expid = new_table.group_by('EXPID')
    
    table_med = table_by_expid.groups.aggregate(np.nanmedian)
    table_min = table_by_expid.groups.aggregate(np.nanmin)

    exposures = Table()
    for attr in ["AIRMASS", "SKY", "SEEING", "TRANSP"]:
        exposures[attr] = table_med[attr]
    for attr in ['RA', "DEC", "MJD", "NIGHT", "EXPID", "HOURANGLE"]:
        exposures[attr] = table_min[attr]
        
    flavors = []
    tiles = []
    exptimes = []

    for idx in range(len(exposures['EXPID'])):

        night = exposures["NIGHT"][idx]
        #print(night)
        expid = exposures['EXPID'][idx]
        raw_file = os.path.join(rawdir, '{night}/{expid:08d}/desi-{expid:08d}.fits.fz'.format(night=night, expid=expid))

        try:
            hdul = fits.open(raw_file)
            header = hdul[1].header
            hdul.close()
            try:
                tiles.append(header['TILEID'])
            except KeyError:
                tiles.append(-1)
            try:
                flavors.append(header["OBSTYPE"])
            except KeyError:
                flavors.append('None')
            try:
                exptimes.append(header['EXPTIME'])
            except:
                exptimes.append(-1)
        except:
            flavors.append('None')
            exptimes.append(-1)
            tiles.append(-1)

    exposures["FLAVOR"] = flavors
    exposures['TILEID'] = tiles
    exposures['EXPTIME'] = exptimes

    if program:
        programs = []
        for row_ in exposures:
            tileid = row_["TILEID"]
            if (tileid >= 65000 and tileid < 67000):
                programs.append('BRIGHT')
                continue
            if (tileid >= 67000 and tileid < 68000):
                programs.append('GRAY')
                continue
            if (tileid >= 68000 and tileid < 69000):
                programs.append("DARK")
                continue
            if (tileid >= 70000 and tileid < 70500):
                programs.append('DARK')
                continue
            if (tileid >= 70500 and tileid < 71000):
                programs.append("BRIGHT")
                continue
            if (tileid >= 71000 and tileid < 71100):
                programs.append("DARK")
                continue
            if (tileid >= 72000 and tileid < 72100):
                programs.append("DARK")
                continue
            if (tileid >= 73000 and tileid < 73100):
                programs.append("GRAY")
                continue
            if (tileid >= 74000 and tileid < 74100):
                programs.append("DARK")
                continue
            if (tileid >= 75000 and tileid < 75100):
                programs.append("BRIGHT")
                continue
            if tileid == -1:
                programs.append('CALIB')
                continue
            else:
                programs.append('OTHER')

        exposures['PROGRAM'] = programs
    
    return exposures, table_by_expid

def write_night_linkage(outdir, nights, subset):
    '''
    Generates linking.js, which helps in linking all the nightly htmls together
    Args:
        outdir : directory to write linking.js and to check for previous html files
        nights : list of nights (strings) to link together
        subset : if True : nights is a subset, and we need to include all existing html files in outdir
                 if False : nights is not a subset, and we do not need to include existing html files in outdir
    Writes outdir/linking.js, which defines a javascript function
    `get_linking_json_dict` that returns a dictionary defining the first and
    last nights, and the previous/next nights for each night.
    '''
    f = []
    f += nights
    if subset:
        f_existing = []
        for (dirpath, dirnames, filenames) in walk(outdir):
            f.extend(filenames)
            break
        regex = re.compile("nightqa-[0-9]+.html")
        f_existing = [filename for filename in f if regex.match(filename)]
        f_existing = [i[6:14] for i in f_existing]
        f += f_existing
        f = list(dict.fromkeys(f))
        f.sort()
    file_js = dict()
    file_js["first"] = "nightqa-"+str(f[0])+".html"
    file_js["last"] = "nightqa-"+str(f[len(f)-1])+".html"

    for i in np.arange(len(f)):
        inner_dict = dict()
        if (len(f) == 1):
            inner_dict["prev"] = "none"
            inner_dict["next"] = "none"
        elif i == 0:
            inner_dict["prev"] = "none"
            inner_dict["next"] = "nightqa-"+str(f[i+1])+".html"
        elif i == len(f)-1:
            inner_dict["prev"] = "nightqa-"+str(f[i-1])+".html"
            inner_dict["next"] = "none"
        else:
            inner_dict["prev"] = "nightqa-"+str(f[i-1])+".html"
            inner_dict["next"] = "nightqa-"+str(f[i+1])+".html"
        file_js["n"+str(f[i])] = inner_dict

    outfile = os.path.join(outdir, 'linking.js')
    with open(outfile, 'w') as fp:
        fp.write("get_linking_json_dict({})".format(json.dumps(file_js)))

    print('Wrote {}'.format(outfile))
    
    return file_js
    
def check_offline_files(dir):
    '''
    Checks if the Bokeh .js and .css files are present (so that the page works offline).
    If they are not downloaded, they will be fetched and downloaded.
    Args:
        dir : directory of where the offline_files folder should be located.
              If not present, an offline_files folder will be genreated.
    '''
    path=(PurePath(dir) / "offline_files")
    version = bokeh.__version__
    b_js = (path / 'bokeh-{version}.js'.format(version=version)).as_posix()
    bt_js = (path / 'bokeh_tables-{version}.js'.format(version=version)).as_posix()
    b_css = (path / 'bokeh-{version}.css'.format(version=version)).as_posix()
    bt_css = (path / 'bokeh_tables-{version}.css'.format(version=version)).as_posix()

    if os.path.isfile(b_js) and os.path.isfile(bt_js) and \
       os.path.isfile(b_css) and os.path.isfile(bt_js):
        print("Offline Bokeh files found")
    else:
        shutil.rmtree(path, True)
        os.makedirs(path, exist_ok=True)

        url_js = "https://cdn.pydata.org/bokeh/release/bokeh-{version}.min.js".format(version=version)
        urllib.request.urlretrieve(url_js, b_js)

        url_tables_js = "https://cdn.pydata.org/bokeh/release/bokeh-tables-{version}.min.js".format(version=version)
        urllib.request.urlretrieve(url_tables_js, bt_js)

        url_css = "https://cdn.pydata.org/bokeh/release/bokeh-{version}.min.css".format(version=version)
        urllib.request.urlretrieve(url_css, b_css)

        url_tables_css = "https://cdn.pydata.org/bokeh/release/bokeh-tables-{version}.min.css".format(version=version)
        urllib.request.urlretrieve(url_tables_css, bt_css)

        print("Downloaded offline Bokeh files")