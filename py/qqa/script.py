"""
qqa command line script
"""

import os, sys, time, glob
import argparse
import traceback
from . import run, plots
from .qa.runner import QARunner
from desiutil.log import get_logger

def print_help():
    print("""USAGE: qqa <command> [options]

Supported commands are:
    monitor  Monitor input directory and run qproc, qa, and generate plots
    run      Run qproc, qa, and generate plots for a single exposure
    preproc  Run only preprocessing on an input raw data file
    qproc    Run qproc (includes preproc) on an input raw data file
    qa       Run QA analysis on qproc outputs
    plot     Generate webpages with plots of QA output
    tables   Generate webpages with tables of nights and exposures
    summary  Generate summary.json for every night available
Run "qqa <command> --help" for details options about each command
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
    elif command == 'summary':
        main_summary()
    else:
        print('ERROR: unrecognized command "{}"'.format(command))
        print_help()
        return 1

def main_monitor(options=None):
    parser = argparse.ArgumentParser(usage = "{prog} run [options]")
    parser.add_argument("-i", "--indir", type=str,  help="watch indir/YEARMMDD/EXPID/ for new raw data")
    parser.add_argument("-o", "--outdir", type=str,  help="write output to outdir/YEARMMDD/EXPID/")
    # parser.add_argument("--qprocdir", type=str,  help="qproc output directory")
    # parser.add_argument("--qadir", type=str,  help="QA output directory")
    parser.add_argument("--plotdir", type=str, help="QA plot output directory")
    parser.add_argument("--cameras", type=str, help="comma separated list of cameras (for debugging)")
    parser.add_argument("--catchup", action="store_true", help="Catch up on processing all unprocessed data")
    parser.add_argument("--waittime", type=int, default=5, help="Seconds to wait between checks for new data")

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
    while True:
        if args.catchup:
            expdir = run.find_unprocessed_expdir(args.indir, args.outdir)
        else:
            expdir = run.find_latest_expdir(args.indir, processed)

        if expdir is None:
            time.sleep(args.waittime)
            continue

        night, expid = expdir.split('/')[-2:]
        rawfile = os.path.join(expdir, 'desi-{}.fits.fz'.format(expid))
        if expdir not in processed and os.path.exists(rawfile):
            outdir = '{}/{}/{}'.format(args.outdir, night, expid)
            if os.path.exists(outdir) and len(glob.glob(outdir+'/*.fits'))>0:
                print('Skipping previously processed {}/{}'.format(night, expid))
                processed.add(expdir)
                continue
            else:
                os.makedirs(outdir, exist_ok=True)

            time_start = time.time()
            print('\n{} Found new exposure {}/{}'.format(
                time.strftime('%H:%M'), night, expid))
            try :
                print('Running qproc on {}'.format(rawfile))
                header = run.run_qproc(rawfile, outdir, cameras=cameras)

                print('Running QA on {}/{}'.format(night, expid))
                qafile = "{}/qa-{}.fits".format(outdir,expid)

                caldir = os.path.join(args.plotdir, "cal_files")
                jsonfile = os.path.join(caldir, "timeseries_dropdown.json")

                if not os.path.isdir(caldir):
                    os.makedirs(caldir)
                qarunner.run(indir=outdir, outfile=qafile, jsonfile=jsonfile)

                print('Generating plots for {}/{}'.format(night, expid))
                plotdir = '{}/{}/{}'.format(args.plotdir, night, expid)
                if not os.path.isdir(plotdir) :
                    os.makedirs(plotdir)
                run.make_plots(infile=qafile, outdir=plotdir, preprocdir=outdir, cameras=cameras)

                run.write_tables(args.outdir, args.plotdir)

                time_end = time.time()
                dt = (time_end - time_start) / 60
                print('{} Finished exposure {}/{} ({:.1f} min)'.format(
                    time.strftime('%H:%M'), night, expid, dt))

            except Exception as e :
                print("Failed to process or QA or plot exposure {}".format(expid))
                print("Error message: {}".format(str(e)))
                exc_info = sys.exc_info()
                traceback.print_exception(*exc_info)
                del exc_info
                print("Now moving on ...")

            processed.add(expdir)

        time.sleep(args.waittime)

def main_run(options=None):
    parser = argparse.ArgumentParser(usage = "{prog} run [options]")
    parser.add_argument("-i", "--infile", type=str, required=True,
        help="input raw data file")
    parser.add_argument("-o", "--outdir", type=str, required=True,
        help="output directory (including YEARMMDD/EXPID/)")
    parser.add_argument("--cameras", type=str, help="comma separated list of cameras (for debugging)")

    if options is None:
        options = sys.argv[2:]

    args = parser.parse_args(options)

    if args.cameras is not None:
        cameras = args.cameras.split(',')
    else:
        cameras = None

    time_start = time.time()
    print('{} Running qproc'.format(time.strftime('%H:%M')))
    header = run.run_qproc(args.infile, args.outdir, cameras=cameras)

    print('{} Running QA analysis'.format(time.strftime('%H:%M')))
    expid = header['EXPID']
    qafile = os.path.join(args.outdir, 'qa-{:08d}.fits'.format(expid))
    qaresults = run.run_qa(args.outdir, outfile=qafile)

    print('{} Making plots'.format(time.strftime('%H:%M')))
    run.make_plots(qafile, args.outdir, preprocdir=args.outdir, cameras=cameras)

    dt = (time.time() - time_start) / 60.0
    print('{} Done ({:.1f} min)'.format(time.strftime('%H:%M'), dt))

def main_preproc(options=None):
    parser = argparse.ArgumentParser(usage = "{prog} preproc [options]")
    parser.add_argument("-i", "--infile", type=str, required=True,
        help="input raw data file")
    parser.add_argument("-o", "--outdir", type=str, required=True,
        help="output directory (without appending YEARMMDD/EXPID/)")
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
        help="output directory (without appending YEARMMDD/EXPID/)")
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
    parser.add_argument("-i", "--infile", type=str, nargs='*', required=True, help="input fits file name with qa outputs")
    parser.add_argument("-o", "--outdir", type=str, help="output directory (including YEARMMDD/EXPID/)")

    if options is None:
        options = sys.argv[2:]

    args = parser.parse_args(options)

    for infile in args.infile:
        if args.outdir is None:
            outdir = os.path.dirname(infile)
        else:
            outdir = args.outdir

        run.make_plots(infile, outdir, preprocdir=outdir)
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
