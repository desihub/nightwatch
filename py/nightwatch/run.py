import os, re, time
import multiprocessing as mp
import subprocess

import fitsio
import numpy as np
import scipy as sp

from astropy.table import Table, vstack

import desiutil.log

import desispec.scripts.preproc
from nightwatch.qa.base import QA

from .thresholds import write_threshold_json, get_outdir

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


def find_unprocessed_expdir(datadir, outdir, processed, startdate=None):
    '''
    Returns the earliest outdir/YEARMMDD/EXPID that has not yet been processed
    in outdir/YEARMMDD/EXPID.

    Args:
        datadir : a directory of nights with exposures
        outdir : directory of processed nights data
    Options:
        startdate : the earliest night to consider processing YYYYMMDD

    Returns directory, of None if no unprocessed directories were found
    (either because no inputs exist, or because all inputs have been processed)

    Warning: traverses the whole tree every time.
    TODO: cache previously identified already-processed data and don't rescan.
    '''
    if startdate:
        startdate = str(startdate)
    else:
        startdate = ''
    all_nights = sorted(os.listdir(datadir))
    #- Search for the earliest unprocessed datadir/YYYYMMDD
    for night in all_nights:
        nightdir = os.path.join(datadir, night)
        if re.match('20\d{6}', night) and os.path.isdir(nightdir) and \
                night >= startdate:
            for expid in sorted(os.listdir(nightdir)):
                expdir = os.path.join(nightdir, expid)
                if re.match('\d{8}', expid) and os.path.isdir(expdir):
                    fits_fz_exists = np.any([re.match('desi-\d{8}.fits.fz', file) for file in os.listdir(expdir)])
                    if fits_fz_exists:
                        qafile = os.path.join(outdir, night, expid, 'qa-{}.fits'.format(expid))
                        if (not os.path.exists(qafile)) and (expdir not in processed):
                            return expdir
                    else:
                        print('Skipping {}/{} with no desi*.fits.fz data'.format(night, expid))

    return None

def find_latest_expdir(basedir, processed, startdate=None):
    '''
    finds the earliest unprocessed basedir/YEARMMDD/EXPID from the latest
    YEARMMDD without traversing the whole tree
    Args:
        basedir : a directory of nights with exposures
        processed : set of exposure directories already processed
    Options:
        startdate : the earliest night to consider processing YYYYMMDD

    Returns directory, or None if no matching directories are found

    Note: if you want the first unprocessed directory, use
    `find_unprocessed_expdir` instead
    '''
    if startdate:
        startdate = str(startdate)
    else:
        startdate = ''

    log = desiutil.log.get_logger()
    #- Search for most recent basedir/YEARMMDD
    for dirname in sorted(os.listdir(basedir), reverse=True):
        nightdir = os.path.join(basedir, dirname)
        if re.match('20\d{6}', dirname) and dirname >= startdate and \
                os.path.isdir(nightdir):
            break
    #- if for loop completes without finding nightdir to break, run this else
    else:
        log.debug('No YEARMMDD dirs found in {}'.format(basedir))
        return None

    night = dirname
    for dirname in sorted(os.listdir(nightdir)):
        expdir = os.path.join(nightdir, dirname)
        if expdir in processed:
            continue

        expid = dirname
        datafilename = os.path.join(expdir, 'desi-{}.fits.fz'.format(expid))
        if os.path.isfile(datafilename):
            log.debug('Found {}'.format(datafilename))
            return expdir
        else:
            log.debug('Skipping {}/{} with no desi*.fits.fz'.format(night, expid))
            processed.add(expdir)  #- so that we won't check again
    else:
        log.debug('No new exposures found')
        return None  #- no basename/YEARMMDD directory was found

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
    '''Runs a given command and writes a logfile, returns a SUCCESS or ERROR message.
    
    Args:
        command: string, command you would call from the command line
        logfile: path to file where logs should be written (string)
        msg: name of the process (str)
    
    Returns: 
        nothing, prints status messages to the console
    '''
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
        pool.close()
        pool.join()
    else:
        log.info('Running preproc serially for {} cameras'.format(len(cameras)))
        for args in arglist:
            desispec.scripts.preproc.main(args)

    return header

def run_qproc(rawfile, outdir, ncpu=None, cameras=None):
    '''
    Determine the obstype of the rawfile, and run qproc with appropriate options

    cameras can be a list

    returns header of HDU 0 of the input rawfile
    '''
    log = desiutil.log.get_logger()

    if not os.path.isdir(outdir):
        log.info('Creating {}'.format(outdir))
        os.makedirs(outdir, exist_ok=True)

    hdr = fitsio.read_header(rawfile, 0)
    if ( 'OBSTYPE' not in hdr ) and ( 'FLAVOR' not in hdr ) :
        log.warning("no obstype nor flavor keyword in first hdu header, moving to the next one")
        hdr = fitsio.read_header(rawfile, 1)
    try :
        if 'OBSTYPE' in hdr :
            obstype = hdr['OBSTYPE'].rstrip().upper()
        else :
            log.warning('Use FLAVOR instead of missing OBSTYPE')
            obstype = hdr['FLAVOR'].rstrip().upper()
        night = hdr['NIGHT']
        expid = hdr['EXPID']
    except KeyError as e :
        log.error(str(e))
        raise(e)
    indir = os.path.abspath(os.path.dirname(rawfile))

    #- HACK: Workaround for data on 20190626/27 that have blank NIGHT keywords
    if night == '        ':
        log.error('Correcting blank NIGHT keyword based upon directory structure')
        #- /path/to/NIGHT/EXPID/rawfile.fits
        night = os.path.basename(os.path.dirname(os.path.dirname(os.path.abspath(rawfile))))
        if re.match('20\d{6}', night):
            log.info('Setting NIGHT to {}'.format(night))
        else:
            raise RuntimeError('Unable to derive NIGHT for {}'.format(rawfile))

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

    if ncpu > 1 and len(cameras)>1 :
        log.info('Running qproc in parallel on {} cores for {} cameras'.format(ncpu, len(cameras) ))
        pool = mp.Pool(ncpu)
        pool.starmap(runcmd, zip(cmdlist, loglist, msglist))
        pool.close()
        pool.join()
    else:
        log.info('Running qproc serially for {} cameras'.format(len(cameras)))
        for cmd, logfile, msg in zip(cmdlist, loglist, msglist):
            runcmd(cmd, logfile, msg)

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
    from .qa.runner import QARunner
    qarunner = QARunner(qalist)
    return qarunner.run(indir, outfile=outfile)

def make_plots(infile, basedir, preprocdir=None, logdir=None, cameras=None):
    '''Make plots for a single exposure

    Args:
        infile: input QA fits file with HDUs like PER_AMP, PER_FIBER, ...
        basedir: write output HTML to basedir/NIGHT/EXPID/

    Options:
        preprocdir: directory to where the "preproc-*-*.fits" are located. If
            not provided, function will NOT generate any image files from any
            preproc fits file.
        logdir: directory to where the "qproc-*-*.log" are located. If
            not provided, function will NOT display any logfiles.
        cameras: list of cameras (strings) to generate image files of. If not
            provided, will generate a cameras list from parcing through the
            preproc fits files in the preprocdir
    '''

    from nightwatch.webpages import amp as web_amp
    from nightwatch.webpages import camfiber as web_camfiber
    from nightwatch.webpages import camera as web_camera
    from nightwatch.webpages import summary as web_summary
    from nightwatch.webpages import lastexp as web_lastexp
    from . import io

    log = desiutil.log.get_logger()

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

    #- Create output exposures plot directory if needed
    expdir = os.path.join(basedir, str(night), '{:08d}'.format(expid))
    if not os.path.isdir(expdir):
        log.info('Creating {}'.format(expdir))
        os.makedirs(expdir, exist_ok=True)

#     plot_components = dict()
    if 'PER_AMP' in qadata:
        htmlfile = '{}/qa-amp-{:08d}.html'.format(expdir, expid)
        pc = web_amp.write_amp_html(htmlfile, qadata['PER_AMP'], header)
#         plot_components.update(pc)
        print('Wrote {}'.format(htmlfile))

    if 'PER_CAMFIBER' in qadata:
        htmlfile = '{}/qa-camfiber-{:08d}.html'.format(expdir, expid)
        pc = web_camfiber.write_camfiber_html(htmlfile, qadata['PER_CAMFIBER'], header)
#         plot_components.update(pc)
        print('Wrote {}'.format(htmlfile))

    if 'PER_CAMERA' in qadata:
        htmlfile = '{}/qa-camera-{:08d}.html'.format(expdir, expid)
        pc = web_camera.write_camera_html(htmlfile, qadata['PER_CAMERA'], header)
#         plot_components.update(pc)
        print('Wrote {}'.format(htmlfile))

    htmlfile = '{}/qa-summary-{:08d}.html'.format(expdir, expid)
    web_summary.write_summary_html(htmlfile, qadata, preprocdir)
    print('Wrote {}'.format(htmlfile))

    #- Note: last exposure goes in basedir, not expdir=basedir/NIGHT/EXPID
    htmlfile = '{}/qa-lastexp.html'.format(basedir)
    web_lastexp.write_lastexp_html(htmlfile, qadata, preprocdir)
    print('Wrote {}'.format(htmlfile))

    #- regardless of if logdir or preprocdir, identifying failed qprocs by comparing
    #- generated preproc files to generated logfiles
    qproc_fails = []    
    if cameras is None:
        cameras = []
        import glob
        for preprocfile in glob.glob(os.path.join(preprocdir, 'preproc-*-*.fits')):
            cameras += [os.path.basename(preprocfile).split('-')[1]]
    
    log_cams = []
    log_outputs = [i for i in os.listdir(logdir) if re.match(r'.*\.log', i)]
    for log in log_outputs:
        l_cam = log.split("-")[1]
        log_cams += [l_cam]
        if l_cam not in cameras:
            qproc_fails.append(l_cam)
        
    
    from nightwatch.webpages import plotimage as web_plotimage
    if (preprocdir is not None):
        #- plot preprocessed images
        downsample = 4

        for camera in cameras:
            input = os.path.join(preprocdir, "preproc-{}-{:08d}.fits".format(camera, expid))
            output = os.path.join(expdir, "preproc-{}-{:08d}-4x.html".format(camera, expid))
            web_plotimage.write_image_html(input, output, downsample, night)

        #- plot preproc nav table
        navtable_output = '{}/qa-amp-{:08d}-preproc_table.html'.format(expdir, expid)
        web_plotimage.write_preproc_table_html(preprocdir, night, expid, downsample, navtable_output)

    if (logdir is not None):
        #- plot logfiles        

        error_colors = dict()
        for log_cam in log_cams:
            input = os.path.join(logdir, "qproc-{}-{:08d}.log".format(log_cam, expid))
            output = os.path.join(expdir, "qproc-{}-{:08d}-logfile.html".format(log_cam, expid))
            e = web_summary.write_logfile_html(input, output, night)
            
            error_colors[log_cam] = e

        #- plot logfile nav table
        htmlfile = '{}/qa-summary-{:08d}-logfiles_table.html'.format(expdir, expid)
        web_summary.write_logtable_html(htmlfile, logdir, night, expid, available=log_cams, 
                                        error_colors=error_colors)


def write_tables(indir, outdir, expnights=None):
    '''
    Parses directory for available nights, exposures to generate
    nights and exposures tables
    
    Args:
        indir : directory of nights
        outdir : directory where to write nights table

    Options:
        expnights (list) : only update exposures tables for these nights
    '''
    import re
    from astropy.table import Table
    from nightwatch.webpages import tables as web_tables
    from pkg_resources import resource_filename
    from shutil import copyfile

    log = desiutil.log.get_logger()

    #- Hack: parse the directory structure to learn nights
    rows = list()
    for dirname in sorted(os.listdir(indir)):
        nightdir = os.path.join(indir, dirname)
        if re.match('20\d{6}', dirname) and os.path.isdir(nightdir):
            night = int(dirname)
            for dirname in sorted(os.listdir(nightdir), reverse=True):
                expdir = os.path.join(nightdir, dirname)

                if re.match('\d{8}', dirname):
                    expid = int(dirname)
                    qafile = os.path.join(expdir, 'qa-{:08d}.fits'.format(expid))
                    
                    #- gets the list of failed qprocs for each expid
                    preproc_cams = [i.split("-")[1] for i in os.listdir(expdir) 
                                    if re.match(r'preproc-.*-.*.fits', i)]
                    log_cams = [i.split("-")[1] for i in os.listdir(expdir) if re.match(r'.*\.log', i)]
                    qfails = [i for i in log_cams if i not in preproc_cams]
                    
                    if os.path.exists(qafile):
                        rows.append(dict(NIGHT=night, EXPID=expid, FAIL=0, QPROC=qfails))
                    else:
                        log.error('Missing {}'.format(qafile))
                        rows.append(dict(NIGHT=night, EXPID=expid, FAIL=1, QPROC=None))

    if len(rows) == 0:
        msg = "No exp dirs found in {}/NIGHT/EXPID".format(indir)
        raise RuntimeError(msg)

    exposures = Table(rows)
    
    caldir = os.path.join(outdir, 'static')
    if not os.path.isdir(caldir):
        os.makedirs(caldir)

    files = ['bootstrap.js', 'bootstrap.css',
             'bootstrap-year-calendar.css', 'bootstrap-year-calendar.js',
             'jquery_min.js', 'popper_min.js', 'live.js']
    for f in files:
        outfile = os.path.join(outdir, 'static', f)
        if not os.path.exists(outfile):
            infile = resource_filename('nightwatch', os.path.join('static', f))
            copyfile(infile, outfile)

    nightsfile = os.path.join(outdir, 'nights.html')
    web_tables.write_nights_table(nightsfile, exposures)

    web_tables.write_exposures_tables(indir, outdir, exposures, nights=expnights)
    

def write_nights_summary(indir, last):
    '''
    Creates summary.json in each of the nights directory within indir

    Args:
        indir: directory where all the nights subdirectories are located. Is also
            the output directory for the summary.json files.

        last: if True, the function will process the last night

    Writes to directory and returns nothing
    '''

    nights = next(os.walk(indir))[1]
    nights = [night for night in nights if re.match(r"[0-9]{8}", night)]
    nights.sort()

    if not last:
        nights = nights[0:len(nights)-1]

    for night in nights:
        jsonfile = os.path.join(indir, night, "summary.json")
        night_qafile = '{indir}/{night}/qa-n{night}.fits'.format(indir=indir, night=night)
        if (not os.path.isfile(jsonfile)) or (not os.path.isfile(night_qafile)):
            expids = next(os.walk(os.path.join(indir, night)))[1]
            expids = [expid for expid in expids if re.match(r"[0-9]{8}", expid)]
            qadata_stacked = dict()
            for expid in expids:
                fitsfile = '{indir}/{night}/{expid}/qa-{expid}.fits'.format(indir=indir, night=night, expid=expid)
                if not os.path.isfile(fitsfile):
                    print("could not find {}".format(fitsfile))
                else:
                    for attr in QA.metacols:
                        try:
                            qadata = Table(fitsio.read(fitsfile, attr))
                        except:
                            continue

                        if (attr not in qadata_stacked):
                            hdr = fitsio.read_header(fitsfile, 0)
                            qadata_stacked[attr] = qadata
                        else:
                            qadata_stacked[attr] = vstack([qadata_stacked[attr], qadata], metadata_conflicts='silent')

                        print("processed {}".format(fitsfile))

            if len(qadata_stacked) == 0:
                print("no exposures found")
                return

            night_qafile = '{indir}/{night}/qa-n{night}.fits'.format(indir=indir, night=night)
            if not os.path.isfile(night_qafile):
                with fitsio.FITS(night_qafile, 'rw', clobber=True) as fx:
                    fx.write(np.zeros(3, dtype=float), extname='PRIMARY', header=hdr)
                    for attr in qadata_stacked:
                        fx.write_table(qadata_stacked[attr].as_array(), extname=attr, header=hdr)

            amp_qadata_stacked = qadata_stacked["PER_AMP"]
            try:
                cam_qadata_stacked = qadata_stacked["PER_CAMERA"]
            except:
                print('No PER_CAMERA data available for {}'.format(night))
                cam_qadata_stacked = [None]*len(amp_qadata_stacked)

            readnoise_sca = dict()
            bias_sca = dict()

            for c in ["R", "B", "Z"]:
                for s in range(0, 10, 1):
                    for a in ["A", "B", "C", "D"]:
                        specific = amp_qadata_stacked[(amp_qadata_stacked["CAM"]==c) & (amp_qadata_stacked["SPECTRO"]==s) & (amp_qadata_stacked["AMP"]==a)]
                        if len(specific) > 0:
                            readnoise_sca_dict = dict(
                                median=np.median(list(specific["READNOISE"])),
                                std=np.std(list(specific["READNOISE"])),
                                num_exp=len(specific)
                            )
                            readnoise_sca[c + str(s) + a] = readnoise_sca_dict

                            bias_sca_dict = dict(
                                median=np.median(list(specific["BIAS"])),
                                std=np.std(list(specific["BIAS"])),
                                num_exp=len(specific)
                            )
                            bias_sca[c + str(s) + a] = bias_sca_dict

            cosmics_rate = dict()
            dx = dict()
            dy = dict()
            xsig = dict()
            ysig = dict()
            for c in ["R", "B", "Z"]:
                specific = amp_qadata_stacked[amp_qadata_stacked["CAM"]==c]
                if len(specific) > 0:
                    cosmics_dict = dict(
                        lower_error=np.percentile(list(specific["COSMICS_RATE"]), 0.1),
                        lower=np.percentile(list(specific["COSMICS_RATE"]), 1),
                        upper=np.percentile(list(specific["COSMICS_RATE"]), 99),
                        upper_error=np.percentile(list(specific["COSMICS_RATE"]), 99.9),
                        num_exp=len(specific),
                    )
                    cosmics_rate[c] = cosmics_dict
                try:
                    cam_specific = cam_qadata_stacked[cam_qadata_stacked["CAM"]==c]
                    if len(cam_specific) > 0:
                        
                        max_diffx = np.array(cam_specific['MAXDX'])-np.array(cam_specific['MEANDX'])
                        min_diffx = np.array(cam_specific['MINDX'])-np.array(cam_specific['MEANDX'])
                        dx_dict = dict(
                            med=np.average([abs(i) for i in cam_specific["MEANDX"]]),
                            std=np.std(list(cam_specific['MEANDX'])),
                            maxd=np.average([abs(i) for i in max_diffx]),
                            mind=-np.average([abs(i) for i in min_diffx]),
                            num_exp=len(cam_specific),
                        )
                        dx[c] = dx_dict
                        
                        max_diffy = np.array(cam_specific['MAXDY'])-np.array(cam_specific['MEANDY'])
                        min_diffy = np.array(cam_specific['MINDY'])-np.array(cam_specific['MEANDY'])
                        dy_dict = dict(
                            med=np.median([abs(i) for i in cam_specific["MEANDY"]]),
                            std=np.std(list(cam_specific['MEANDY'])),
                            maxd=np.average([abs(i) for i in max_diffy]),
                            mind=-np.average([abs(i) for i in min_diffy]),
                            num_exp=len(cam_specific),
                        )
                        dy[c] = dy_dict
                        
                except KeyError:
                    print('No data for DX or DY on {}'.format(night))
                try:
                    cam_specific = cam_qadata_stacked[cam_qadata_stacked["CAM"]==c]
                    if len(cam_specific) > 0:
                
                        max_xsig = cam_specific['MAXXSIG']
                        max_xsig = np.array([i for i in max_xsig if not np.ma.is_masked(i)])
                        min_xsig = cam_specific['MINXSIG']
                        min_xsig = np.array([i for i in min_xsig if not np.ma.is_masked(i)])
                        mean_xsig = cam_specific['MEANXSIG']
                        mean_xsig = np.array([i for i in mean_xsig if not np.ma.is_masked(i)])
                        
                        max_diffx = max_xsig - mean_xsig
                        min_diffx = min_xsig - mean_xsig
                        
                        xsig_dict = dict(
                            med=np.average([float(abs(i)) for i in mean_xsig]),
                            std=np.std([float(abs(i)) for i in mean_xsig]),
                            maxd=np.average([float(abs(i)) for i in max_diffx]),
                            mind=-np.average([float(abs(i)) for i in min_diffx]),
                            num_exp=len(cam_specific),
                        )
                        xsig[c] = xsig_dict
                        
                        max_ysig = cam_specific['MAXYSIG']
                        max_ysig = np.array([i for i in max_ysig if not np.ma.is_masked(i)])
                        min_ysig = cam_specific['MINYSIG']
                        min_ysig = np.array([i for i in min_ysig if not np.ma.is_masked(i)])
                        mean_ysig = cam_specific['MEANYSIG']
                        mean_ysig = np.array([i for i in mean_ysig if not np.ma.is_masked(i)])
                        
                        max_diffy = max_ysig - mean_ysig
                        min_diffy = min_ysig - mean_ysig
                        
                        ysig_dict = dict(
                            med=np.average([float(abs(i)) for i in mean_ysig]),
                            std=np.std([float(abs(i)) for i in mean_ysig]),
                            maxd=np.average([float(abs(i)) for i in max_diffy]),
                            mind=-np.average([float(abs(i)) for i in min_diffy]),
                            num_exp=len(cam_specific),
                        )
                        ysig[c] = ysig_dict
                        
                except KeyError:
                    print('No data for XSIG, YSIG on {}'.format(night))

            data = dict(
                PER_AMP=dict(
                    READNOISE=readnoise_sca,
                    BIAS=bias_sca,
                    COSMICS_RATE=cosmics_rate
                ),
                PER_CAMERA=dict(
                    DX=dx,
                    DY=dy,
                    XSIG=xsig,
                    YSIG=ysig,
                )
            )

            import json
            with open(jsonfile, 'w') as out:
                json.dump(data, out, indent=4)
            print('Wrote {}'.format(jsonfile))
            
def write_thresholds(indir, outdir, start_date, end_date):
    '''Writes threshold files for each metric over a given date range.
    Input: 
        indir: directory that contains nightly directories (which contain summary.json files)
        outdir: directory to threshold inspector html files
        start_date: beginning of date range
        end_date: end of date range'''
    if not os.path.isdir(get_outdir()):
        os.makedirs(get_outdir(), exist_ok=True)
        print('Added threshold_files directory to nightwatch/py/nightwatch')
    
    if not os.path.isdir(outdir):
        #log.info('Creating {}'.format(outdir))
        os.makedirs(outdir, exist_ok=True)
    
    for name in ['READNOISE', 'BIAS', 'COSMICS_RATE', 'DX', 'DY', 'XSIG', 'YSIG']:
        write_threshold_json(indir, outdir, start_date, end_date, name)
    
    from nightwatch.webpages import thresholds as web_thresholds
    
    plot_components = dict()
    htmlfile = '{}/threshold-inspector-{}-{}.html'.format(outdir, start_date, end_date)
    pc = web_thresholds.write_threshold_html(htmlfile, outdir, indir, start_date, end_date)
    plot_components.update(pc)
    print('Wrote {}'.format(htmlfile))
