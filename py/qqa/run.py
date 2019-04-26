import os, re
import multiprocessing as mp
import subprocess

import fitsio

import desiutil.log

def find_latest_expdir(basedir):
    '''
    finds the latest basedir/YEARMMDD/EXPID without traversing the whole tree
    
    Returns directory, or None if no matching directories are found
    '''
    #- Search for most recent basedir/YEARMMDD
    for dirname in sorted(os.listdir(basedir), reverse=True):
        nightdir = os.path.join(basedir, dirname)
        if re.match('20\d{6}', dirname) and os.path.isdir(nightdir):
            break
    else:
        return None  #- no basename/YEARMMDD directory was found
    
    for dirname in sorted(os.listdir(nightdir), reverse=True):
        expdir = os.path.join(nightdir, dirname)
        if re.match('\d{8}', dirname) and os.path.isdir(expdir):
            break
    else:
        return None  #- no basename/YEARMMDD/EXPID directory was found
    
    return expdir    

def which_cameras(rawfile):
    '''
    Returns list of cameras found in rawfile
    '''
    cameras = list()
    with fitsio.FITS(rawfile) as fx:
        for hdu in fx:
            extname = hdu.get_extname().upper()
            if re.match('[BRZ][0-9]', extname):
                cameras.append(extname.lower())
    
    return sorted(cameras)

def run_preproc(rawfile, outdir, ncpu=None):
    '''TODO: document'''
    if not os.path.exists(datafile):
        raise ValueError("{} doesn't exist".format(datafile))
        
    cameras = which_cameras(rawfile)
    header = fitsio.read_header(rawfile, 0)
    
    arglist = list()
    for camera in cameras:
        args = ['--infile', datafile, '--outdir', outdir, '--cameras', camera]
        arglist.append(args)

    if ncpu is None:
        ncpu = max(1, mp.cpu_count()//2)  #- no hyperthreading

    pool = mp.Pool(ncpu)
    pool.map(desispec.scripts.preproc.main, arglist)
    
    return header

def run_qproc(rawfile, outdir, ncpu=None):
    '''
    Determine the flavor of the rawfile, and run qproc with appropriate options
    
    returns header of HDU 0 of the input rawfile
    '''
    log = desiutil.log.get_logger()

    hdr = fitsio.read_header(rawfile, 0)
    flavor = hdr['FLAVOR'].rstrip().upper()
    night = hdr['NIGHT']
    expid = hdr['EXPID']
    
    indir = os.path.abspath(os.path.dirname(rawfile))

    fibermap = '{}/fibermap-{:08d}.fits'.format(indir, expid)
    if flavor == 'SCIENCE' and not os.path.exists(fibermap):
        log.error('{}/{} SCIENCE exposure without a fibermap'.format(night, expid))
    
    arglist = list()
    cameras = which_cameras(rawfile)
    for camera in cameras:
        outfiles = dict(
            rawfile = rawfile,
            fibermap = '{}/fibermap-{:08d}.fits'.format(indir, expid),
            preproc = '{}/preproc-{}-{:08d}.fits'.format(outdir, camera, expid),
            psf = '{}/psf-{}-{:08d}.fits'.format(outdir, camera, expid),
            qframe = '{}/qframe-{}-{:08d}.fits'.format(outdir, camera, expid),
            qcframe = '{}/qcframe-{}-{:08d}.fits'.format(outdir, camera, expid),
            qsky = '{}/qsky-{}-{:08d}.fits'.format(outdir, camera, expid),
        )

        if flavor == "SCIENCE":
            cmd = "desi_qproc -i {rawfile} --fibermap {fibermap} --cam {camera}"
            cmd += " --output-preproc {preproc}"
            cmd += " --shift-psf --output-psf {psf}"
            cmd += " --output-rawframe {qframe}"
            cmd += " --apply-fiberflat --skysub --output-skyframe {qsky}"
            cmd += " --fluxcalib --outframe {qcframe}"
        elif flavor == "ARC":
            cmd = "desi_qproc -i {rawfile} --cam {camera}"
            cmd += " --output-preproc {preproc}"
            cmd += " --shift-psf --compute-lsf-sigma --output-psf {psf}"
            cmd += " --output-rawframe {qframe}"
        elif flavor == "FLAT":
            cmd = "desi_qproc -i {rawfile} --cam {camera}"
            cmd += " --output-preproc {preproc}"
            cmd += " --shift-psf --output-psf {psf}"
            cmd += " --output-rawframe {qframe}"
            cmd += " --compute-fiberflat --output-flatframe {qflatframe}"
        elif flavor in ("ZERO", "DARK"):
            cmd = "desi_qproc -i {rawfile} --cam {camera}"
            cmd += " --output-preproc {preproc}"
        else:
            log = desiutil.log.get_logger()
            log.error('{}/{}: unrecognized flavor {}'.format(night, expid, flavor))
            cmd = "desi_qproc -i {rawfile} --cam {camera}"
            cmd += " --output-preproc {preproc}"

        fullcmd = cmd.format(camera=camera, **outfiles)
        arglist.append(fullcmd.split())    

    if ncpu is None:
        ncpu = max(1, mp.cpu_count()//2)  #- no hyperthreading

    if ncpu > 1:
        pool = mp.Pool(ncpu)
        pool.map(subprocess.call, arglist)
    else:
        for args in arglist:
            print('\n-- RUNNING: ' + ' '.join(args) + '\n')
            subprocess.call(args)

    return hdr

def make_plots(qadata, header, outdir):
    '''TODO: Document'''
    
    from . import plots
    
    night = header['NIGHT']
    expid = header['EXPID']
    
    htmlfile = '{}/qaAmp-{}.html'.format(outdir, expid)
    plots.amp.write_amp_qa_html(qadata['PER_AMP'], htmlfile, header)
    print('Wrote {}'.format(htmlfile))

