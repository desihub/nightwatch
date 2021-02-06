# calculates nominal read noise for zero and dark
# outputs FITS with all fields to [outdir]

import numpy as np
import os
import fitsio
import json 

from nightwatch.thresholds import get_outdir

def calcnominalnoise(nightwatchdir, nightexpids, outfile):
    """
    Calculate nominal readnoise for each amp given an input set of example exps

    Args:
        nightwatchdir: base directory with nightwatch output
        nightexpids: list of (night,expid) tuples to load
        outfile: output JSON thresholds file to write

    Output:
        writes two READNOISE-*.json files containing the nominal (median) thresholds per amp,
        calibrated on zeros and darks respectively, to the nightwatch/threshold_files directory

    TODO:
      * use all nightexpids instead of splitting by ZEROs vs. DARKs with
        hardcoded requirement that the DARK is always 2 expids after the input ZERO
    """

    #---- EXAMPLE code for using function inputs
    amps = []
    readnoise = []
    for night, expid in nightexpids:
        qadir = os.path.join(nightwatchdir, str(night), '{:08d}'.format(expid))
        qafile = os.path.join(qadir, 'qa-{:08d}.fits'.format(int(expid)))
        amp = fitsio.read(qafile, "PER_AMP")
        amp.sort(order=["CAM", "SPECTRO", "AMP"]) # https://numpy.org/doc/stable/reference/generated/numpy.recarray.sort.html
        amps.append(amp)
        readnoise.append(amp["READNOISE"])

    # extract (sorted) readnoises for ZEROs and DARKs
    zero_readnoise = []
    dark_readnoise = []
    for night, expid in nightexpids:
        zerodir = os.path.join(nightwatchdir, str(night), '{:08d}'.format(int(expid)))
        zerofile = os.path.join(zerodir, 'qa-{:08d}.fits'.format(int(expid)))
        zeroamp = fitsio.read(zerofile, "PER_AMP")
        zeroamp.sort(order=["CAM", "SPECTRO", "AMP"]) # https://numpy.org/doc/stable/reference/generated/numpy.recarray.sort.html
        zero_readnoise.append(zeroamp["READNOISE"])

        # requires DARK is always 2 expids after input ZERO (last ZERO of the night)
        darkdir = os.path.join(nightwatchdir, str(night), '{:08d}'.format(int(expid)+2))
        darkfile = os.path.join(darkdir, 'qa-{:08d}.fits'.format(int(expid)+2))
        darkamp = fitsio.read(darkfile, "PER_AMP")
        darkamp.sort(order=["CAM", "SPECTRO", "AMP"]) # https://numpy.org/doc/stable/reference/generated/numpy.recarray.sort.html
        dark_readnoise.append(darkamp["READNOISE"])        

    # calculate nominal values
    zero_noms = np.median(zero_readnoise, axis=0)
    dark_noms = np.median(dark_readnoise, axis=0)

    # create thresholds files
    zero_thresholds = dict()
    dark_thresholds = dict()
    all_amps = [cam+spec+amp for cam in ['B', 'R', 'Z'] for spec in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'] for amp in ['A', 'B', 'C', 'D']]

    for i, amp in enumerate(all_amps):
        zero_ampnom = zero_noms[i]
        zero_thresholds[amp] = dict(upper_err=zero_ampnom+1, upper=zero_ampnom+0.5,
                                    lower=zero_ampnom-0.5, lower_err=zero_ampnom-1)
        dark_ampnom = dark_noms[i]
        dark_thresholds[amp] = dict(upper_err=dark_ampnom+1, upper=dark_ampnom+0.5,
                                    lower=dark_ampnom-0.5, lower_err=dark_ampnom-1)

    # write files
    outdir = get_outdir()
    split_outfile = outfile.split(".")
    
    zero_outfile = split_outfile[0] + '-ZERO.' + split_outfile[1]
    zero_threshold_file = os.path.join(outdir, zero_outfile)
    with open(zero_threshold_file, 'w') as json_file:
             json.dump(zero_thresholds, json_file, indent=4)
    print('Wrote {}'.format(zero_threshold_file))

    dark_outfile = split_outfile[0] + '-DARK.' + split_outfile[1]
    dark_threshold_file = os.path.join(outdir, dark_outfile)
    with open(dark_threshold_file, 'w') as json_file:
             json.dump(dark_thresholds, json_file, indent=4)
    print('Wrote {}'.format(dark_threshold_file))
        
    
if __name__ == "__main__":
    """
    e.g.
    python calcnominalreadnoise.py --indir /global/cfs/cdirs/desi/spectro/nightwatch/nersc \
        --nightexpids $HOME/desi/code/nightwatch/py/nightwatch/threshold_files/ZEROS-20210111.txt \
        --outfile READNOISE-20210111.json
    """
    import argparse

    parser = argparse.ArgumentParser(usage = "{prog} [options]")
    parser.add_argument("--indir", type=str,  help="base directory with nightwatch processed data")
    parser.add_argument("--nightexpids", type=str, help="text file containing input night/expids (last ZERO of the night) to use for readnoise")
    parser.add_argument("--outfile", type=str,  help="output json threshold file to write (excluding DARK/ZERO designation)")
    args = parser.parse_args()

    f = open(args.nightexpids, "r")
    inputids = f.read().split(' ') # read each night/exp separately
    f.close()

    #- convert input nightexpids strings to list of (night,expid) tuples
    nightexpids = list()
    for tmp in inputids:
        n, e = tmp.split('/')
        nightexpid = (int(n), int(e))
        nightexpids.append(nightexpid)

    calcnominalnoise(args.indir, nightexpids, args.outfile)
