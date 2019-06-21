# # !/bin/sh
# # SBATCH -N 1            # nodes requested
# # SBATCH -n 1            # tasks requested
# # SBATCH -C haswell      # constraint requested
# # SBATCH -q interactive  # quality of service requested
# # SBATCH -t 0:05:00      # time requested in hour:minute:second

from qqa.run import run_qproc
import argparse

def run(options=None):
    parser = argparse.ArgumentParser(usage = "{prog} qproc [options]")
    parser.add_argument("--rawfile", type=str, required=True,
        help="input raw data file")
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
