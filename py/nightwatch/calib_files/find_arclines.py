import os
import json
import fitsio

import numpy as np

from glob import glob
from scipy.signal import find_peaks
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter


def find_spectral_lines(basedir, night, program, verbose=False):
    """Compute positions of arc lamp lines in calibration exposures. Uses the
    central 20 fibers from each camera.

    Parameters
    ----------
    basedir : str
        Path to Nightwatch qframe exposures (basedir/YYYYMMDD)
    night : str or int
        Date in format YYYYMMDD
    program : str
        Arc lamp calibration program name.
    verbose : bool
        Print output if true.

    Returns
    -------
    """
    lines = { 'B':[], 'R':[], 'Z':[] }
    nightexpids = []

    # Loop over spectrographs.
    for sp in np.arange(10):
        wave  = { 'B':None, 'R':None, 'Z':None }
        flux  = { 'B':None, 'R':None, 'Z':None }
        flux2 = { 'B':None, 'R':None, 'Z':None }
        n     = { 'B':0,    'R':0,    'Z':0    }

        # Loop over cameras.
        for cam in 'BRZ':
            # Find all exposures from this night matching the camera and spectrograph.
            qframes = sorted(glob(os.path.join(basedir, f'{night}', '*', f'qframe-{cam.lower()}{sp}*.fits')))

            for qframe in qframes:
                h = fitsio.read_header(qframe, ext='FIBERMAP')
                if h['PROGRAM'] == program:

                    night, expid = h['NIGHT'], h['EXPID']
                    if [night, expid] not in nightexpids:
                        nightexpids.append([night, expid])

                    # Grab the middle 20 fibers in the qframe, covering all four amps in each camera.
                    fits = fitsio.FITS(qframe)
                    wl = np.median(fits['WAVELENGTH'][240:260, :], axis=0)
                    fl = np.median(fits['FLUX'][240:260, :], axis=0)

                    if wave[cam] is None and flux[cam] is None:
                        wave[cam]  = wl
                        flux[cam]  = fl
                        flux2[cam] = fl**2
                    else:
                        flux[cam]  += fl
                        flux2[cam] += fl**2

                    n[cam] += 1

            if n[cam] == 0:
                continue

            wl = wave[cam]
            fl = flux[cam]/n[cam]
            flstd = np.sqrt(flux2[cam]/n[cam] - fl**2)
            fluxthr = np.maximum(500, np.percentile(fl, 99.5))
            peaks, _ = find_peaks(fl, height=fluxthr, distance=20)

            if verbose:
                for i, pk in enumerate(peaks):
                    print(f'{i+1:2} {pk:6} {wl[pk]:10.1f} {np.round(wl[pk]):6g} {fl[pk]:8.1f} +- {flstd[pk]:5.1f}')
                    lines[cam].append(wl[pk])
                print('    ------')

    # Go through the list of lines and pick out the best ones.
    arc_lines = { 'B':[], 'R':[], 'Z':[] }

    for cam in 'BRZ':
        print(cam)
        lines[cam] = sorted(lines[cam])

        # Loop through the sorted list of line wavelengths.
        i = 0
        line = []
        for l in lines[cam]:
            if not line:
                line = [l]
            else:
                # When finding a gap of >10 angstrom, assume we have a new
                # cluster of lines.
                if (l - line[-1] > 10 or l == lines[cam][-1]):
                    if len(line) > 1:
                        i += 1
                        if verbose:
                            print(f'{i:2} {np.average(line):6.1f} +- {np.std(line):3.1f} ({len(line):2})  -->  {np.round(np.average(line)):g}')
                        arc_lines[cam].append(np.round(np.average(line)))
                    line = [l]
                else:
                    line.append(l)

    arc_lines['inputs'] = {
        'comment' : '(night,expid) used to compute arc lamp lines',
        'nightexpids' : nightexpids
    }

    return arc_lines


if __name__ == '__main__':
    p = ArgumentParser(usage='{prog} [options]',
                       formatter_class=ArgumentDefaultsHelpFormatter)
    p.add_argument('-n', '--night', type=int,
                   help='Night containing arc lamp exposures [YYYYMMDD]',
                   default='20220101')
    p.add_argument('-i', '--indir', type=str,
                   help='Base folder with Nightwatch processed data.')
    p.add_argument('-o', '--outfile', type=str,
                   help='Output json file with line info.')
    p.add_argument('-v', '--verbose', action='store_true',
                   help='Verbose output during processing.')
    args = p.parse_args()

    # First find short arcs.
    short_arcs = find_spectral_lines(args.indir, args.night, 'CALIB short Arcs all', args.verbose)
    if args.verbose:
        print(short_arcs)

    # Next find long arcs.
    long_arcs = find_spectral_lines(args.indir, args.night, 'CALIB long Arcs Cd+Xe', args.verbose)
    if args.verbose:
        print(long_arcs)

    # Output to JSON.
    arc_lines = { 'CALIB short Arcs all' : short_arcs }
    arc_lines['CALIB long Arcs Cd+Xe'] = long_arcs

    with open(args.outfile, 'w') as json_file:
        json.dump(arc_lines, json_file, indent=4)

