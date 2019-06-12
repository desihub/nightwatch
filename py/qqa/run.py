import os, re, time
import multiprocessing as mp
import subprocess

import fitsio

from astropy.table import Table

import desiutil.log

import desispec.scripts.preproc

def get_ncpu(ncpu):
    """
    Get number of CPU cores to use, throttling to 8 for NERSC login nodes

    Args:
        ncpu : number you would like to use, or None to auto-derive

    Returns:
        number of CPU cores to use
    """
    if ncpu is None:
        ncpu = max(1, mp.cpu_count()//2)  #- no hyperthreading

    if ('NERSC_HOST' in os.environ) and ('SLURM_JOBID' not in os.environ):
        ncpu = min(8, ncpu)

    return ncpu

def find_unprocessed_expdir(datadir, outdir):
    '''
    Returns the earliest basedir/YEARMMDD/EXPID that has not yet been processed
    in outdir/YEARMMDD/EXPID.

    Returns directory, of None if no unprocessed directories were found
    (either because no inputs exist, or because all inputs have been processed)

    Warning: traverses the whole tree every time.
    TODO: cache previously identified already-processed data and don't rescan.
    '''
    for night in sorted(os.listdir(datadir)):
        nightdir = os.path.join(datadir, night)
        if re.match('20\d{6}', night) and os.path.isdir(nightdir):
            for expid in sorted(os.listdir(nightdir)):
                expdir = os.path.join(nightdir, expid)
                if re.match('\d{8}', expid) and os.path.isdir(expdir):
                    qafile = os.path.join(outdir, night, expid, 'qa-{}.fits'.format(expid))
                    if not os.path.exists(qafile):
                        return expdir

    return None

def find_latest_expdir(basedir, processed):
    '''
    finds the earliest unprocessed basedir/YEARMMDD/EXPID from the latest
    YEARMMDD without traversing the whole tree

    processed: set of exposure directories already processed

    Returns directory, or None if no matching directories are found
    '''
    #- Search for most recent basedir/YEARMMDD
    for dirname in sorted(os.listdir(basedir), reverse=True):
        nightdir = os.path.join(basedir, dirname)
        if re.match('20\d{6}', dirname) and os.path.isdir(nightdir):
            break
    else:
        return None  #- no basename/YEARMMDD directory was found

    for dirname in sorted(os.listdir(nightdir)):
        expdir = os.path.join(nightdir, dirname)
        if expdir in processed:
            continue
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

def runcmd(command, logfile, msg):
    args = command.split()
    print('Logging {} to {}'.format(msg, logfile))
    with open(logfile, 'w') as logfx:
        t0 = time.time()
        print('Starting at {}'.format(time.asctime()), file=logfx)
        print('RUNNING {}'.format(command), file=logfx)
        err = subprocess.call(args, stdout=logfx, stderr=logfx)
        dt = time.time() - t0
        print('Done at {} ({:0f} sec)'.format(time.asctime(), dt), file=logfx)

    if err == 0:
        print('SUCCESS {}'.format(msg))
    if err != 0:
        print('ERROR {} while running {}'.format(err, msg))
        print('See {}'.format(logfile))

def run_preproc(rawfile, outdir, ncpu=None, cameras=None):
    '''Runs preproc on the input raw data file, outputting to outdir

    Args:
        rawfile: input desi-EXPID.fits.fz raw data file
        outdir: directory to write preproc-CAM-EXPID.fits files

    Options:
        ncpu: number of CPU cores to use for parallelism; serial if ncpu<=1
        cameras: list of cameras to process; default all found in rawfile

    Returns header of HDU 0 of the input raw data file
    '''
    if not os.path.exists(rawfile):
        raise ValueError("{} doesn't exist".format(rawfile))

    log = desiutil.log.get_logger()

    if not os.path.isdir(outdir):
        log.info('Creating {}'.format(outdir))
        os.makedirs(outdir, exist_ok=True)

    if cameras is None:
        cameras = which_cameras(rawfile)

    header = fitsio.read_header(rawfile, 0)

    arglist = list()
    for camera in cameras:
        args = ['--infile', rawfile, '--outdir', outdir, '--cameras', camera]
        arglist.append(args)

    ncpu = min(len(arglist), get_ncpu(ncpu))

    if ncpu > 1:
        log.info('Running preproc in parallel on {} cores for {} cameras'.format(
            ncpu, len(cameras) ))
        pool = mp.Pool(ncpu)
        pool.map(desispec.scripts.preproc.main, arglist)
    else:
        log.info('Running preproc serially for {} cameras'.format(ncpu))
        for args in arglist:
            desispec.scripts.preproc.main(args)

    return header

def run_qproc(rawfile, outdir, ncpu=None, cameras=None):
    '''
    Determine the flavor of the rawfile, and run qproc with appropriate options

    cameras can be a list

    returns header of HDU 0 of the input rawfile
    '''
    log = desiutil.log.get_logger()

    if not os.path.isdir(outdir):
        log.info('Creating {}'.format(outdir))
        os.makedirs(outdir, exist_ok=True)

    hdr = fitsio.read_header(rawfile, 0)
    if 'FLAVOR' not in hdr :
        log.warning("no flavor keyword in first hdu header, moving to the next one")
        hdr = fitsio.read_header(rawfile, 1)
    try :
        flavor = hdr['FLAVOR'].rstrip().upper()
        night = hdr['NIGHT']
        expid = hdr['EXPID']
    except KeyError as e :
        log.error(str(e))
        raise(e)
    indir = os.path.abspath(os.path.dirname(rawfile))

    cmdlist = list()
    loglist = list()
    msglist = list()
    rawcameras = which_cameras(rawfile)
    if cameras is None :
        cameras = rawcameras
    elif len(set(cameras) - set(rawcameras)) > 0:
        missing_cameras = set(cameras) - set(rawcameras)
        for cam in sorted(missing_cameras):
            log.error('{} missing camera {}'.format(os.path.basename(rawfile), cam))
        cameras = sorted(set(cameras) & set(rawcameras))


    for camera in cameras:
        outfiles = dict(
            rawfile = rawfile,
            fibermap = '{}/fibermap-{:08d}.fits'.format(indir, expid),
            logfile = '{}/qproc-{}-{:08d}.log'.format(outdir, camera, expid),
            outdir = outdir,
            camera = camera
        )
        cmd = "desi_qproc -i {rawfile} --fibermap {fibermap} --auto --auto-output-dir {outdir} --cam {camera}".format(**outfiles)
        cmdlist.append(cmd)
        loglist.append(outfiles['logfile'])
        msglist.append('qproc {}/{} {}'.format(night, expid, camera))

    ncpu = min(len(cmdlist), get_ncpu(ncpu))

    if ncpu > 1:
        log.info('Running qproc in parallel on {} cores for {} cameras'.format(
            ncpu, len(cameras) ))
        pool = mp.Pool(ncpu)
        pool.starmap(runcmd, zip(cmdlist, loglist, msglist))
    else:
        log.info('Running qproc serially for {} cameras'.format(ncpu))
        for cmd, logfile in zip(cmdlist, loglist, msglist):
            runcmd(cmd, logfile)

    return hdr

def run_qa(indir, outfile=None, qalist=None):
    """
    Run QA analysis of qproc files in indir, writing output to outfile

    Args:
        indir: directory containing qproc outputs (qframe, etc.)

    Options:
        outfile: write QA output to this FITS file
        qalist: list of QA objects to include; default QARunner.qalist

    Returns dictionary of QA results, keyed by PER_AMP, PER_CCD, PER_FIBER, ...
    """
    from .qa import QARunner
    qarunner = QARunner(qalist)
    return qarunner.run(indir, outfile=outfile)

def make_plots(infile, outdir, preprocdir=None, cameras=None):
    '''Make plots for a single exposure

    Args:
        infile: input QA fits file with HDUs like PER_AMP, PER_FIBER, ...
        outdir: write output HTML files to this directory

    Options:
        preprocdir: directory to where the "preproc-*-*.fits" are located. If
            not provided, function will NOT generate any image files from any
            preproc fits file.
        cameras: list of cameras (strings) to generate image files of. If not
            provided, will generate a cameras list from parcing through the
            preproc fits files in the preprocdir

    '''

    from . import webpages
    from . import io

    log = desiutil.log.get_logger()
    if not os.path.isdir(outdir):
        log.info('Creating {}'.format(outdir))
        os.makedirs(outdir, exist_ok=True)

    qadata = io.read_qa(infile)
    header = qadata['HEADER']

    night = header['NIGHT']
    expid = header['EXPID']

    #- Early data have wrong NIGHT in header; check by hand
    #- YEARMMDD/EXPID/infile
    dirnight = os.path.basename(os.path.dirname(os.path.dirname(infile)))
    if re.match('20\d{6}', dirnight) and dirnight != str(night):
        log.warning('Correcting {} header night {} to {}'.format(infile, night, dirnight))
        night = int(dirnight)
        header['NIGHT'] = night

    plot_components = dict()
    if 'PER_AMP' in qadata:
        htmlfile = '{}/qa-amp-{:08d}.html'.format(outdir, expid)
        pc = webpages.amp.write_amp_html(htmlfile, qadata['PER_AMP'], header)
        plot_components.update(pc)
        print('Wrote {}'.format(htmlfile))

    if 'PER_CAMFIBER' in qadata:
        htmlfile = '{}/qa-camfiber-{:08d}.html'.format(outdir, expid)
        pc = webpages.camfiber.write_camfiber_html(htmlfile, qadata['PER_CAMFIBER'], header)
        plot_components.update(pc)
        print('Wrote {}'.format(htmlfile))

    htmlfile = '{}/qa-summary-{:08d}.html'.format(outdir, expid)
    webpages.summary.write_summary_html(htmlfile, plot_components)
    print('Wrote {}'.format(htmlfile))

    from qqa.webpages import plotimage
    if (preprocdir is not None):
        if cameras is None:
            cameras = []
            import glob
            for preprocfile in glob.glob(os.path.join(preprocdir, 'preproc-*-*.fits')):
                cameras += [os.path.basename(preprocfile).split('-')[1]]
        for camera in cameras:
            input = os.path.join(preprocdir, "preproc-{}-{:08d}.fits".format(camera, expid))
            output = os.path.join(outdir, "preproc-{}-{:08d}-4x.html".format(camera, expid))
            plotimage.write_image_html(input, output, 4)

def write_tables(indir, outdir):
    import re
    from astropy.table import Table
    from . import webpages
    from pkg_resources import resource_filename
    from shutil import copyfile

    #- Hack: parse the directory structure to learn nights
    rows = list()
    for dirname in sorted(os.listdir(indir)):
        nightdir = os.path.join(indir, dirname)
        if re.match('20\d{6}', dirname) and os.path.isdir(nightdir):
            night = int(dirname)
            for dirname in sorted(os.listdir(nightdir), reverse=True):
                expdir = os.path.join(nightdir, dirname)
                if re.match('\d{8}', dirname) and os.path.isdir(expdir):
                    expid = int(dirname)
                    rows.append(dict(NIGHT=night, EXPID=expid))

    if len(rows) == 0:
        msg = "No exp dirs found in {}/NIGHT/EXPID".format(indir)
        raise RuntimeError(msg)

    exposures = Table(rows)

    caldir = os.path.join(outdir, 'cal_files')
    if not os.path.isdir(caldir):
        os.makedirs(caldir)

    files = ['bootstrap.js', 'bootstrap.css', 'bootstrap-year-calendar.css', 'bootstrap-year-calendar.js', 'jquery_min.js', 'popper_min.js']
    for f in files:
        outfile = os.path.join(outdir, 'cal_files', f)
        if not os.path.exists(outfile):
            infile = resource_filename('qqa', os.path.join('cal_files', f))
            copyfile(infile, outfile)

    nightsfile = os.path.join(outdir, 'nights.html')
    webpages.tables.write_nights_table(nightsfile, exposures)

    webpages.tables.write_exposures_tables(indir,outdir, exposures)
