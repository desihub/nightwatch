# calculates nominal read noise for zero and dark
# outputs FITS with all fields to [outdir]

import numpy as np
import os
import fitsio
import json 

def calcnominalnoise(nightwatchdir, nightexpids, outfile):
    """
    Calculate nominal readnoise for each amp given an input set of example exps

    Args:
        nightwatchdir: base directory with nightwatch output
        nightexpids: list of (night,expid) tuples to load
        outfile: output JSON thresholds file to write

    Output:
        writes json files containing the nominal (median) thresholds per amp,
    """

    # extract (sorted) readnoises for ZEROs and DARKs
    readnoise = []
    for night, expid in nightexpids:
        qadir = os.path.join(nightwatchdir, str(night), '{:08d}'.format(expid))
        qafile = os.path.join(qadir, 'qa-{:08d}.fits'.format(int(expid)))
        amp = fitsio.read(qafile, "PER_AMP")
        amp.sort(order=["CAM", "SPECTRO", "AMP"]) # https://numpy.org/doc/stable/reference/generated/numpy.recarray.sort.html
        readnoise.append(amp["READNOISE"])

    # calculate nominal values
    noms = np.median(readnoise, axis=0)

    # create thresholds files
    thresholds = dict()
    all_amps = [cam+spec+amp for cam in ['B', 'R', 'Z'] for spec in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'] for amp in ['A', 'B', 'C', 'D']]

    for i, amp in enumerate(all_amps):
        ampnom = noms[i]
        thresholds[amp] = dict(upper_err=ampnom+1, upper=ampnom+0.5,
                               nominal=ampnom,
                               lower=ampnom-0.5, lower_err=ampnom-1)

    # for the record, include nightexpids in output
    thresholds['inputs'] = dict()
    thresholds['inputs']['comment'] = '(night,expid) used to calc thresholds'
    thresholds['inputs']['nightexpids'] = nightexpids

    # write threshold file
    with open(outfile, 'w') as json_file:
        json.dump(thresholds, json_file, indent=4)
    print('Wrote {}'.format(outfile))
    
if __name__ == "__main__":
    """
    e.g.
    python calcnominalreadnoise.py \
        --indir /global/cfs/cdirs/desi/spectro/nightwatch/nersc \
        --nightexpids 20210128-ZERO.txt \
        --outfile READNOISE-20210128-ZERO.json

    python calcnominalreadnoise.py \
        --indir /global/cfs/cdirs/desi/spectro/nightwatch/nersc \
        --nightexpids 20210128-DARK.txt \
        --outfile READNOISE-20210128-DARK.json
    """
    import argparse

    parser = argparse.ArgumentParser(usage = "{prog} [options]")
    parser.add_argument("--indir", type=str,  help="base directory with nightwatch processed data")
    parser.add_argument("--nightexpids", type=str, help="text file containing input night expids to use for readnoise")
    parser.add_argument("--outfile", type=str,  help="output json threshold file to write designation)")
    args = parser.parse_args()

    #- convert input nightexpids file to list of (night,expid) tuples
    tmp = np.loadtxt(args.nightexpids, dtype=int, unpack=True)
    nightexpids = [(int(a), int(b)) for a,b in zip(tmp[0], tmp[1])]

    calcnominalnoise(args.indir, nightexpids, args.outfile)
