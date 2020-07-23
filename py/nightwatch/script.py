"""
nightwatch command line script
"""

import os, sys, time, glob
import argparse
import traceback
import subprocess
from desimodel.io import load_tiles
from desispec.io import meta

from . import run, plots, io
from .run import timestamp, get_ncpu
from .qa.runner import QARunner
from desiutil.log import get_logger

import tempfile
import shutil

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
    parser.add_argument("--batch", "-b", type=bool, default=False, help="Bool, qproc data processing to batch job")
    parser.add_argument("--nodes", "-N", type=int, default=1, help="Number of nodes for qproc batch job, batch=True")
    parser.add_argument("--ntasks", "-n", type=int, default=1, help="Number of tasks per node for qproc batch job, batch=True")
    parser.add_argument("--constraint", "-C", type=str, default="haswell", help="Constraint for qproc batch job, batch=True")
    parser.add_argument("--qos", "-q", type=str, default="interactive", help="Qos for qproc batch job, batch=True")
    parser.add_argument("--time", "-t", type=int, default=5, help="time for qproc batch job, batch=True")

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
                run_batch_qproc=args.batch

                if run_batch_qproc:
                    print('{} Spawning qproc of {} to batch processes'.format(
                        timestamp(), rawfile))

                    sep = os.path.sep
                    dirfile = sep.join(['..', 'code', 'nightwatch', 'py', 'nightwatch', 'wrap_qproc.py'])

                    batch_dict = dict(
                        nodes=args.nodes,
                        ntasks=args.ntasks,
                        constraint=args.constraint,
                        qos=args.qos,
                        time=args.time,
                        dirfile=dirfile,
                        rawfile=rawfile,
                        outdir=outdir,
                        cameras=cameras,
                    )

                    batchcmd = 'srun -N {nodes} -n {ntasks} -C {constraint} -q {qos} -t {time} '
                    runfile = 'python {dirfile} wrap_qproc --rawfile {rawfile} --outdir {outdir}'
                    if cameras:
                        runfile += ' --cameras {cameras}'

                    cmd = (batchcmd + runfile).format(**batch_dict)
                    err = subprocess.call(cmd.split())

                    if err == 0:
                        print('SUCCESS {}'.format('running qproc as batch process'))
                    if err != 0:
                        print('ERROR {} while running {}'.format(err, 'qproc as batch process'))
                        print('Failed to run qproc as batch process, switching to run locally')
                        run_batch_qproc = False


                if not run_batch_qproc:
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

        sys.stdout.flush()
        time.sleep(args.waittime)

def main_run(options=None):
    parser = argparse.ArgumentParser(usage = "{prog} run [options]")
    parser.add_argument("-i", "--infile", type=str, required=True,
        help="input raw data file")
    parser.add_argument("-o", "--outdir", type=str, required=True,
        help="output base directory")
    parser.add_argument("--cameras", type=str, help="comma separated list of cameras (for debugging)")

    if options is None:
        options = sys.argv[2:]

    args = parser.parse_args(options)

    if args.cameras is not None:
        cameras = args.cameras.split(',')
    else:
        cameras = None
        
    with tempfile.TemporaryDirectory() as tmpdr:

        night, expid = io.get_night_expid(args.infile)
        expdir = io.findfile('expdir', night=night, expid=expid, basedir=tmpdr)
        rawdir = os.path.dirname(os.path.dirname(os.path.dirname(args.infile)))

        time_start = time.time()
        print('{} Running qproc'.format(time.strftime('%H:%M')))
        header = run.run_qproc(args.infile, expdir, cameras=cameras)

        print('{} Running QA analysis'.format(time.strftime('%H:%M')))
        qafile = io.findfile('qa', night=night, expid=expid, basedir=tmpdr)
        qaresults = run.run_qa(expdir, outfile=qafile)

        print('{} Making plots'.format(time.strftime('%H:%M')))
        run.make_plots(qafile, tmpdr, preprocdir=expdir, logdir=expdir, rawdir=rawdir, cameras=cameras)

        print('{} Updating night/exposure summary tables'.format(time.strftime('%H:%M')))
        run.write_tables(tmpdr, tmpdr, expnights=[night,])
        
        print('Copying files from temporary directory.')
        shutil.move(os.path.join(tmpdr, 'nights.html'), os.path.join(args.outdir, 'nights.html'))
        shutil.move(os.path.join(tmpdr, '{}/exposures.html'.format(night)), os.path.join(args.outdir, '{}/exposures.html'.format(night)))
        
        
        argslist = []
        for file in os.listdir(os.path.join(tmpdr, '{}/{:08d}'.format(night, expid))):
            filename = os.path.basename(file)
            src = os.path.join(tmpdr, '{}/{:08d}/{}'.format(night, expid, filename))
            dest = os.path.join(args.outdir, '{}/{:08d}/{}'.format(night, expid, filename))
            argslist.append((src, dest))
        
        ncpu = get_ncpu(None)
        if ncpu > 1:
            pool = mp.Pool(ncpu)
            pool.starmap(shutil.move, argslist)
            pool.close()
            pool.join()
        else:
            for args in argslist:
                shutil.move(**args)

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
    parser.add_argument("-r", "--rawdir", type=str, help="directory conatining raw data (not including YEARMMDD/EXPID/)")

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

    if options is None:
        options = sys.argv[2:]

    args = parser.parse_args(options)
    if args.outdir is None:
        args.outdir = args.indir

    run.write_tables(args.indir, args.outdir)
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
        args.rawdir = meta.rawdata_root()
    
    name_dict = {"EXPID": "EXPID", "MJD": "MJD", 
             "AIRMASS": "AIRMASS", "TRANSP": "TRANSPARENCY", "NIGHT": "NIGHT", 
             "MOONSEP": "MOON_SEP_DEG", "RA": "SKYRA", "DEC": "SKYDEC",
             "SKY": "SKY_MAG_AB", "SEEING": "FWHM_ASEC"}

    run.write_summaryqa(args.infile, name_dict, tiles, args.rawdir, args.outdir)