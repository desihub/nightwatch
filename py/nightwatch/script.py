"""
nightwatch command line script
"""

import os, sys, time, glob
import argparse
import traceback
import subprocess
from desimodel.io import load_tiles
import desispec.io

from . import run, plots, io
from .run import timestamp, get_ncpu
from .qa.runner import QARunner
from desiutil.log import get_logger

import tempfile
import shutil
import contextlib

import multiprocessing as mp

def print_help():
    print("""USAGE: nightwatch <command> [options]

Supported commands are:
    monitor    Monitor input directory and run qproc, qa, and generate plots
    run        Run qproc, qa, and generate plots for a single exposure
    preproc    Run only preprocessing on an input raw data file
    qproc      Run qproc (includes preproc) on an input raw data file
    qa         Run QA analysis on qproc outputs
    plot       Generate webpages with plots of QA output
    tables     Generate webpages with tables of nights and exposures
    webapp     Run a nightwatch Flask webapp server
    surveyqa   Generate surveyqa webpages
Run "nightwatch <command> --help" for details options about each command
""")

def main():
    if len(sys.argv) == 1 or sys.argv[1] in ('-h', '--help', '-help', 'help'):
        print_help()
        return 0

    command = sys.argv[1]
    if command == 'monitor':
        main_monitor()
    if command == 'run':
        main_run()
    elif command == 'preproc':
        main_preproc()
    elif command == 'qproc':
        main_qproc()
    elif command == 'qa':
        main_qa()
    elif command in ('plot', 'plots'):
        main_plot()
    elif command == 'tables':
        main_tables()
    elif command == 'webapp':
        from .webapp import main_webapp
        main_webapp()
    elif command == 'summary':
        main_summary()
    elif command == 'threshold':
        main_threshold()
    elif command == 'surveyqa':
        main_surveyqa()
    else:
        print('ERROR: unrecognized command "{}"'.format(command))
        print_help()
        return 1

def main_monitor(options=None):
    parser = argparse.ArgumentParser(usage = "{prog} monitor [options]")
    parser.add_argument("-i", "--indir", type=str,  help="watch indir/YEARMMDD/EXPID/ for new raw data")
    parser.add_argument("-o", "--outdir", type=str,  help="write output to outdir/YEARMMDD/EXPID/")
    # parser.add_argument("--qprocdir", type=str,  help="qproc output directory")
    # parser.add_argument("--qadir", type=str,  help="QA output directory")
    parser.add_argument("--plotdir", type=str, help="QA plot output directory")
    parser.add_argument("--cameras", type=str, help="comma separated list of cameras (for debugging)")
    parser.add_argument("--catchup", action="store_true", help="Catch up on processing all unprocessed data")
    parser.add_argument("--waittime", type=int, default=10, help="Seconds to wait between checks for new data")
    parser.add_argument("--startdate", type=int, default=None, help="Earliest startdate to check for unprocessed nights (YYYYMMDD)")
    parser.add_argument("--batch", "-b", action='store_true', help="spawn qproc data processing to batch job")
    parser.add_argument("--batch-queue", "-q", type=str, default="realtime", help="batch queue to use")
    parser.add_argument("--batch-time", "-t", type=int, default=10, help="batch job time limit [minutes]")
    parser.add_argument("--batch-opts", type=str, default="-N 1 -C haswell -A desi", help="Additional batch options")

    if options is None:
        options = sys.argv[2:]

    args = parser.parse_args(options)

    if args.cameras is not None:
        cameras = args.cameras.split(',')
    else:
        cameras = None

    if args.plotdir is None :
        args.plotdir = args.outdir

    log = get_logger()
    tmp = os.path.join(args.indir, 'YEARMMDD', 'EXPID')
    log.info('Monitoring {}/ for new raw data'.format(tmp))

    qarunner = QARunner()
    processed = set()

    #- TODO: figure out a way to print how many nights are being skipped before startdate
    while True:        

        if os.path.exists('stop.nightwatch'):
            print("Found stop.nightwatch file; exiting now")
            sys.exit(0)

        if args.catchup:
            expdir = run.find_unprocessed_expdir(args.indir, args.outdir, processed, startdate=args.startdate)
        else:
            expdir = run.find_latest_expdir(args.indir, processed, startdate=args.startdate)

        if expdir is None:
            print('{} No new exposures found; sleeping {} sec'.format(
                    timestamp(), args.waittime))
            sys.stdout.flush()
            time.sleep(args.waittime)
            continue

        night, expid = expdir.split('/')[-2:]
        night = int(night)
        rawfile = os.path.join(expdir, 'desi-{}.fits.fz'.format(expid))
        if expdir not in processed and os.path.exists(rawfile):
            processed.add(expdir)
            outdir = '{}/{}/{}'.format(args.outdir, night, expid)
            if os.path.exists(outdir) and len(glob.glob(outdir+'/qa-*.fits'))>0:
                print('Skipping previously processed {}/{}'.format(night, expid))
                processed.add(expdir)
                continue
            else:
                os.makedirs(outdir, exist_ok=True)

            time_start = time.time()
            print('\n{} Found new exposure {}/{}'.format(timestamp(), night, expid))
            sys.stdout.flush()
            try :
                if args.batch:
                    print('{} Submitting batch job for {}'.format(time.strftime('%H:%M'), rawfile))
                    batch_run(rawfile, args.outdir, cameras, args.batch_queue, args.batch_time, args.batch_opts)
                else:
                    print('{} Running qproc on {}'.format(time.strftime('%H:%M'), rawfile))
                    sys.stdout.flush()
                    header = run.run_qproc(rawfile, outdir, cameras=cameras)

                    print('{} Running QA on {}/{}'.format(timestamp(), night, expid))
                    sys.stdout.flush()
                    qafile = "{}/qa-{}.fits".format(outdir,expid)

                    caldir = os.path.join(args.plotdir, "static")
                    jsonfile = os.path.join(caldir, "timeseries_dropdown.json")

                    if not os.path.isdir(caldir):
                        os.makedirs(caldir)
                    qarunner.run(indir=outdir, outfile=qafile, jsonfile=jsonfile)

                    print('Generating plots for {}/{}'.format(night, expid))
                    tmpdir = '{}/{}/{}'.format(args.plotdir, night, expid)
                    if not os.path.isdir(tmpdir) :
                        os.makedirs(tmpdir)
                    run.make_plots(infile=qafile, basedir=args.plotdir, preprocdir=outdir, logdir=outdir,
                                   cameras=cameras)

                    run.write_tables(args.outdir, args.plotdir, expnights=[night,])

                    time_end = time.time()
                    dt = (time_end - time_start) / 60
                    print('{} Finished exposure {}/{} ({:.1f} min)'.format(
                        timestamp(), night, expid, dt))

            except Exception as e :
                print("Failed to process or QA or plot exposure {}".format(expid))
                print("Error message: {}".format(str(e)))
                exc_info = sys.exc_info()
                traceback.print_exception(*exc_info)
                del exc_info
                print("Now moving on ...")
                sys.stdout.flush()

            processed.add(expdir)

        else:
            sys.stdout.flush()
            time.sleep(args.waittime)
        
class TempDirManager():
    '''Custom context manager that creates a temporary directory, and upon exiting the context copies all files (regardless if the code written inside the context runs properly or exits with some error) into a specified output directory.'''
    def __init__(self, outdir):
        '''Initializes TempDirManager with the directory specified to copy all files written.'''
        self.outdir = outdir
        self.tempdir = None
    def __enter__(self):
        self.tempdir = tempfile.TemporaryDirectory().name
        return self.tempdir
    def __exit__(self, *exc):
        '''Copies files over when context is exited.'''
        outdir = self.outdir
        tempdir = self.tempdir
        
        print('{} Copying files from temporary directory to {}'.format(
            time.strftime('%H:%M'), outdir))

        src = []
        for dirpath, dirnames, files in os.walk(tempdir, topdown=True):
            for file_name in files:
                src.append(os.path.join(dirpath, file_name))
        dest = [file.replace(tempdir, outdir) for file in src]
        argslist = list(zip(src, dest))

        #- Check what output directories need to be made, but cache list
        #- so that we don't check existence for the same dir N>>1 times
        fullpath_outdirs = set()
        for (src, dest) in argslist:
            dirpath = os.path.dirname(dest)
            if dirpath not in fullpath_outdirs:
                if not os.path.exists(dirpath):
                    os.makedirs(dirpath)
        
        #- using shutil.move in place of shutil.copytree, for instance, because copytree requires that the directory/file being copied to does not exist prior to the copying (option to supress this requirement only available in python 3.8+)
        #- parallel copying performs better than copying serially
        ncpu = get_ncpu(None)
        if ncpu > 1:
            pool = mp.Pool(ncpu)
            pool.starmap(shutil.move, argslist)
            pool.close()
            pool.join()
        else:
            for args in argslist:
                shutil.move(**args)
        
        print('{} Done copying {} files'.format(
            time.strftime('%H:%M'), len(argslist)))

def batch_run(infile, outdir, cameras, queue, batchtime, batchopts):
    """Submits batch job to `nightwatch run infile outdir ...`

    Args:
        infile (str): input DESI raw data file
        outdir (str): base output directory
        cameras (list or None): None, or list of cameras to include
        queue (str): slurm queue name
        batchtime (int): batch job time limit [minutes]
        batchopts (str): additional batch options

    Returns error code from sbatch submission

    Note: this is a non-blocking call and will return before the batch
    processing is finished
    """
    night, expid = io.get_night_expid(infile)
    expdir = io.findfile('expdir', night=night, expid=expid, basedir=outdir)

    infile = os.path.abspath(infile)
    expdir = os.path.abspath(expdir)
    outdir = os.path.abspath(outdir)

    if cameras is None:
        camera_options = ""
    elif isinstance(cameras, (list, tuple)):
        camera_options = "--cameras {}".format(','.join(cameras))
    elif isinstance(cameras, str):
        camera_options = f"--cameras {cameras}"
    else:
        raise ValueError('Unable to parse cameras {}'.format(cameras))

    jobname = f'nightwatch-{expid:08d}'
    batchfile = f'{expdir}/{jobname}.slurm'
    with open(batchfile, 'w') as fx:
        fx.write(f"""#!/bin/bash -l

#SBATCH {batchopts}
#SBATCH --qos {queue}
#SBATCH --time {batchtime}
#SBATCH --job-name {jobname}
#SBATCH --output {expdir}/{jobname}-%j.joblog
#SBATCH --exclusive

nightwatch run --infile {infile} --outdir {outdir} {camera_options}
""")

    err = subprocess.call(["sbatch", batchfile])

    return err

def main_run(options=None):
    parser = argparse.ArgumentParser(usage = "{prog} run [options]")
    parser.add_argument("-i", "--infile", type=str, required=False,
        help="input raw data file")
    parser.add_argument("-o", "--outdir", type=str, required=True,
        help="output base directory")
    parser.add_argument("--cameras", type=str, help="comma separated list of cameras (for debugging)")
    parser.add_argument('-n', '--night', type=int,
        help="YEARMMDD night")
    parser.add_argument('-e', '--expid', type=int,
        help="Exposure ID")

    if options is None:
        options = sys.argv[2:]

    args = parser.parse_args(options)

    if args.cameras is not None:
        cameras = args.cameras.split(',')
    else:
        cameras = None

    if args.infile is None:
        if args.night is None or args.expid is None:
            print('ERROR: must provide --infile or --night AND --expid')
            sys.exit(2)

        args.infile = desispec.io.findfile('raw', args.night, args.expid)
        
    night, expid = io.get_night_expid(args.infile)
    rawdir = os.path.dirname(os.path.dirname(os.path.dirname(args.infile)))

    #- Using a tempdir sometimes is better, and sometimes is way worse;
    #- turn off for now
    # with TempDirManager(args.outdir) as tempdir:
    tempdir = args.outdir
    if True:
        expdir = io.findfile('expdir', night=night, expid=expid, basedir=tempdir)

        time_start = time.time()
        print('{} Running qproc'.format(time.strftime('%H:%M')))
        header = run.run_qproc(args.infile, expdir, cameras=cameras)

        print('{} Running QA analysis'.format(time.strftime('%H:%M')))
        qafile = io.findfile('qa', night=night, expid=expid, basedir=tempdir)
        qaresults = run.run_qa(expdir, outfile=qafile)

        print('{} Making plots'.format(time.strftime('%H:%M')))
        run.make_plots(qafile, tempdir, preprocdir=expdir, logdir=expdir, rawdir=rawdir, cameras=cameras)
        
    print('{} Updating night/exposure summary tables'.format(time.strftime('%H:%M')))
    run.write_tables(args.outdir, args.outdir, expnights=[night,])

    dt = (time.time() - time_start) / 60.0
    print('{} Done ({:.1f} min)'.format(time.strftime('%H:%M'), dt))
        
def main_preproc(options=None):
    parser = argparse.ArgumentParser(usage = "{prog} preproc [options]")
    parser.add_argument("-i", "--infile", type=str, required=True,
        help="input raw data file")
    parser.add_argument("-o", "--outdir", type=str, required=True,
        help="output directory")
    parser.add_argument("--cameras", type=str, help="comma separated list of cameras (for debugging)")

    if options is None:
        options = sys.argv[2:]

    args = parser.parse_args(options)

    if args.cameras is not None:
        cameras = args.cameras.split(',')
    else:
        cameras = None

    header = run.run_preproc(args.infile, args.outdir, cameras=cameras)
    print("Done running preproc on {}; wrote outputs to {}".format(args.infile, args.outdir))

def main_qproc(options=None):
    parser = argparse.ArgumentParser(usage = "{prog} qproc [options]")
    parser.add_argument("-i", "--infile", type=str, required=True,
        help="input raw data file")
    parser.add_argument("-o", "--outdir", type=str, required=True,
        help="output directory")
    parser.add_argument("--cameras", type=str, help="comma separated list of cameras (for debugging)")

    if options is None:
        options = sys.argv[2:]

    args = parser.parse_args(options)

    if args.cameras is not None:
        cameras = args.cameras.split(',')
    else:
        cameras = None

    header = run.run_qproc(args.infile, args.outdir, cameras=cameras)
    print("Done running qproc on {}; wrote outputs to {}".format(args.infile, args.outdir))

def main_qa(options=None):
    parser = argparse.ArgumentParser(usage = "{prog} qa [options]")
    parser.add_argument("-i", "--indir", type=str, required=True, help="input directory with qproc outputs")
    parser.add_argument("-o", "--outfile", type=str, required=True, help="output qa fits file name")

    if options is None:
        options = sys.argv[2:]

    args = parser.parse_args(options)

    qaresults = run.run_qa(args.indir, outfile=args.outfile)
    print("Done running QA on {}; wrote outputs to {}".format(args.indir, args.outfile))

def main_plot(options=None):
    parser = argparse.ArgumentParser(usage = "{prog} plot [options]")
    parser.add_argument("-i", "--infile", type=str, nargs='*', required=True, help="input QA fits file")
    parser.add_argument("-o", "--outdir", type=str, help="output base directory (not including YEARMMDD/EXPID/)")
    parser.add_argument("-r", "--rawdir", type=str, help="directory containing raw data (not including YEARMMDD/EXPID/)")

    if options is None:
        options = sys.argv[2:]

    args = parser.parse_args(options)

    for infile in args.infile:
        if args.outdir is None:
            outdir = os.path.dirname(infile)
        else:
            outdir = args.outdir
        
        rawdir = args.rawdir
        
        run.make_plots(infile, outdir, preprocdir=os.path.dirname(infile), logdir=os.path.dirname(infile), rawdir=rawdir)
        print("Done making plots for {}; wrote outputs to {}".format(args.infile, args.outdir))

def main_tables(options=None):
    parser = argparse.ArgumentParser(usage = "{prog} plot [options]")
    parser.add_argument("-i", "--indir", type=str, required=True, help="QA in indir/YEARMMDD/EXPID")
    parser.add_argument("-o", "--outdir", type=str, help="write summary tables to outdir/nights.html and outdir/YEARMMDD/exposures.html")
    parser.add_argument("-n", "--nights", type=str, help="comma separated list of nights to process")

    if options is None:
        options = sys.argv[2:]

    args = parser.parse_args(options)
    if args.outdir is None:
        args.outdir = args.indir

    nights = None
    if args.nights is not None:
        nights = [int(n) for n in args.nights.split(',')]

    run.write_tables(args.indir, args.outdir, expnights=nights)
    print('Wrote summary tables to {}'.format(args.outdir))

def main_summary(options=None):
    parser = argparse.ArgumentParser(usage = "{prog} [options]")
    parser.add_argument("-i", "--indir", type=str, required=True, help="directory of night directories; write summary data to indir/night/summary.json")
    parser.add_argument("-l", "--last", type=bool, help="True if last night shown is complete and ready to summarize")

    if options is None:
        options = sys.argv[2:]

    args = parser.parse_args(options)

    last = args.last
    if last is None:
        last = False

    run.write_nights_summary(args.indir, last)
    print('Wrote summary jsons for each night to {}'.format(args.indir))
    
def main_threshold(options=None):
    parser = argparse.ArgumentParser(usage = '{prog} [options]')
    parser.add_argument('-i', '--indir', type=str, required=True, help='directory of night directories; where summary.json files can be found')
    parser.add_argument('-o', '--outdir', type=str, required=True, help='directory threshold json/html files should be written to')
    parser.add_argument('-s', '--start', type=int, required=True, help='start date for calculation range')
    parser.add_argument('-e', '--end', type=int, required=True, help='end date for calculation range')
    
    if options is None:
        options = sys.argv[2:]
    args = parser.parse_args(options)
    
    run.write_thresholds(args.indir, args.outdir, args.start, args.end)
    print('Wrote threshold jsons for each night to {}'.format('nightwatch/py/nightwatch/threshold_files'))

def main_surveyqa(options=None):
    parser = argparse.ArgumentParser(usage = '{prog} [options]')
    
    parser.add_argument('-i', '--infile', type=str, required=True, help='file containing data to feed into surveyqa')
    parser.add_argument('-o', '--outdir', type=str, required=True, help='directory threshold json/html files should be written to (will be written to outdir/surveyqa, outdir should be same location as other nightwatch files)')
    parser.add_argument('-t', '--tilefile', type=str, help='file containing data on tiles')
    parser.add_argument('-r', '--rawdir', type=str, help='directory containing raw data files (without YYYMMDD/EXPID/)')
    
    if options is None:
        options = sys.argv[2:]
    args = parser.parse_args(options)
    
    if args.tilefile is None:
        tiles = load_tiles()
    else:
        tiles = Table.read(args.tilefile, hdu=1)
        
    if args.rawdir is None:
        args.rawdir = desispec.io.meta.rawdata_root()
    
    name_dict = {"EXPID": "EXPID", "MJD": "MJD", 
             "AIRMASS": "AIRMASS", "TRANSP": "TRANSPARENCY", "NIGHT": "NIGHT", 
             "MOONSEP": "MOON_SEP_DEG", "RA": "SKYRA", "DEC": "SKYDEC",
             "SKY": "SKY_MAG_AB", "SEEING": "FWHM_ASEC"}

    run.write_summaryqa(args.infile, name_dict, tiles, args.rawdir, args.outdir)
