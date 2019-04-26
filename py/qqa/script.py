"""
qqa command line script
"""

import os, sys, time
import argparse
from . import run, plots
from .qa import QARunner
from desiutil.log import get_logger

def print_help():
    print("""USAGE: qqa <command> [options]
    
Supported commands are:
    run      Monitor input directory and run qproc, qa, and generate plots
    preproc  Run only preprocessing on an input raw data file
    qproc    Run qproc (includes preproc) on an input raw data file
    qa       Run QA analysis on qproc outputs
    plot     Generate plots of QA output

Run "qqa <command> --help" for details options about each command
""")

def main():
    if len(sys.argv) == 1 or sys.argv[1] in ('-h', '--help', '-help', 'help'):
        print_help()
        return 0

    command = sys.argv[1]
    if command == 'run':
        main_run()
    elif command == 'preproc':
        main_preproc()
    elif command == 'qproc':
        main_qproc()
    elif command == 'qa':
        main_qa()
    elif command == 'plot':
        main_plot()
    else:
        print('ERROR: unrecognized command "{}"'.format(command))
        print_help()
        return 1

def main_run(options=None):
    parser = argparse.ArgumentParser(usage = "{prog} run [options]")
    parser.add_argument("-i", "--indir", type=str,  help="watch indir/YEARMMDD/EXPID/ for new raw data")
    parser.add_argument("-o", "--outdir", type=str,  help="write output to outdir/YEARMMDD/EXPID/")
    # parser.add_argument("--qprocdir", type=str,  help="qproc output directory")
    # parser.add_argument("--qadir", type=str,  help="QA output directory")
    # parser.add_argument("--plotdir", type=str,  help="QA plot output directory")

    if options is None:
        options = sys.argv[2:]

    args = parser.parse_args(options)
    
    log = get_logger()
    tmp = os.path.join(args.indir, 'YEARMMDD', 'EXPID')
    log.info('Monitoring {}/ for new raw data'.format(tmp))
    
    qarunner = QARunner()

    processed = set()
    while True:
        expdir = run.find_latest_expdir(args.indir)
        if expdir is None:
            continue

        night, expid = expdir.split('/')[-2:]
        rawfile = os.path.join(expdir, 'desi-{}.fits.fz'.format(expid))
        if expdir not in processed and os.path.exists(rawfile):
            outdir = '{}/{}/{}'.format(args.outdir, night, expid)
            if os.path.exists(outdir):
                print('Skipping previously processed {}/{}'.format(night, expid))
                processed.add(expdir)
                continue
            else:
                os.makedirs(outdir)

            print('Running qproc on {}'.format(rawfile))
            # header = run_preproc(rawfile, outdir)
            header = run.run_qproc(rawfile, outdir)

            print('Running QA on {}/{}'.format(night, expid))
            qadata = qarunner.run(indir=outdir, outdir=outdir)

            print('Generating plots for {}/{}'.format(night, expid))
            run.make_plots(qadata, header, outdir)

            processed.add(expdir)

        time.sleep(2)

def main_preproc(options=None):
    parser = argparse.ArgumentParser(usage = "{prog} preproc [options]")
    parser.add_argument("-i", "--infile", type=str, required=True,
        help="input raw data file")
    parser.add_argument("-o", "--outdir", type=str, required=True,
        help="output directory (without appending YEARMMDD/EXPID/)")

    if options is None:
        options = sys.argv[2:]

    args = parser.parse_args(options)
    
    header = run.run_preproc(args.infile, args.outdir)

def main_qproc(options=None):
    parser = argparse.ArgumentParser(usage = "{prog} qproc [options]")
    parser.add_argument("-i", "--infile", type=str, required=True,
        help="input raw data file")
    parser.add_argument("-o", "--outdir", type=str, required=True,
        help="output directory (without appending YEARMMDD/EXPID/)")

    if options is None:
        options = sys.argv[2:]

    args = parser.parse_args(options)
    
    header = run.run_qproc(args.infile, args.outdir)

def main_qa(options=None):
    parser = argparse.ArgumentParser(usage = "{prog} qa [options]")
    parser.add_argument("-i", "--indir", type=str, required=True, help="input directory with qproc outputs")
    parser.add_argument("-o", "--outdir", type=str, required=True, help="output directory (without appending YEARMMDD/EXPID/)")

    if options is None:
        options = sys.argv[2:]

    args = parser.parse_args(options)
    
    from . import qa
    qa.run(args.indir, outdir=args.outdir)

def main_plot(options=None):
    parser = argparse.ArgumentParser(usage = "{prog} plot [options]")
    parser.add_argument("-i", "--indir", type=str,  help="input directory with qa outputs")
    parser.add_argument("-o", "--outdir", type=str,  help="output directory (without appending YEARMMDD/EXPID/)")

    if options is None:
        options = sys.argv[2:]
    
    args = parser.parse_args(options)

    print('qqa plot: Not yet implemented')
    
    # header = run.make_plots(args.infile, args.outdir)

    
    
