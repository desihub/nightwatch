from nightwatch.run import run_qproc
import argparse
import sys

def run(options=None):
    parser = argparse.ArgumentParser(usage = "{prog} wrap_qproc [options]")
    parser.add_argument("--rawfile", type=str, required=True, help="input raw data file")
    parser.add_argument("--outdir", type=str, required=True, 
                        help="output directory (without appending YEARMMDD/EXPID/)")
    parser.add_argument("--cameras", type=str, help="comma separated list of cameras (for debugging)")

    if options is None:
        options = sys.argv[2:]

    args = parser.parse_args(options)
    
    if args.cameras is not None:
        cameras = args.cameras.split(',')
    else:
        cameras = None
    
    run_qproc(args.rawfile, args.outdir, cameras=cameras)

if __name__ == '__main__':   
    run()
