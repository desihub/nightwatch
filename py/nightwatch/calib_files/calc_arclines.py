import os
import json
import fitsio

import numpy as np

from glob import glob
from tqdm import tqdm
from configparser import ConfigParser
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter


calarcs = {
    'CALIB short Arcs all': {
        'wavelength' : {
#            'B': [4048.0, 4360.0, 4679.0, 4801.0, 5087.0, 5462.0],
#            'R': [6145.0, 6385.0, 6404.0, 6508.0, 6680.0, 6931.0, 7034.0, 7247.0, 7604.0],
            'B': [4048.0, 4679.0, 4801.0, 5087.0, 5462.0],
            'R': [6145.0, 6385.0, 6404.0, 6508.0, 6680.0, 6931.0, 7034.0, 7247.0],
            'Z': [7604.0, 8115.0, 8192.0, 8266.0, 8301.0, 8779.0, 8822.0, 8931.0]
        }
    },
    'CALIB long Arcs Cd+Xe': {
        'wavelength' : {
            'B': [3612.0, 4679.0, 4801.0, 5087.0],
            'R': [6440.0],
            'Z': [8234.0, 8283.0, 8822.0, 8955.0, 9048.0, 9165.0, 9802.0],
        }
    }
}


def calc_arc_lines(datadir, night, expids, prog, wavelengths, warnlevel=0.075, errlevel=0.1):
    """Compute pseudo-equivalent widths of bright lines from the arc lamps.

    Parameters
    ----------
    datadir : str
        Path to Nightwatch qframe outputs (datadir/YYYYMMDD/EXPID).
    night : int
        Observing night in format YYYYMMDD.
    expids : list
        List of integer exposure IDs for a particular calibration program.
    prog : str
        Calibration program, e.g., 'CALIB short Arcs all'
    wavelengths : dict
        Calibration wavelengths for this program (for the B, R, Z cameras).
    warnlevel : float
        Fractional deviation from nominal level for warnings [0-1].
    errlevel : float
        Fractional deviation from nominal level for errors [0-1].

    Returns
    -------
    lineareas : dict
        Dictionary of pseudo-equivalent widths for calibration lines.
    """
    fiberlo = 240       # ID of lowest fiber used in extracting spectrum.
    fiberhi = 260       # ID of highest fiber used in extracting spectrum.
    npix = 12           # Number of pixels around the line center for computing pEW
    lineareas = {
        'settings' : {
            'fiberlo' : fiberlo,
            'fiberhi' : fiberhi,
            'npix' : npix,
            'comment' : 'Fiber range used in spectrum; number of pixels used around line center.'
        }
    }

    # Loop over all spectrographs.
    for sp in tqdm(range(10)):
        lineareas[sp] = { 'B' : {}, 'R' : {}, 'Z' : {} }

        # Loop over exposure IDs specified on input.
        for expid in expids:
            for cam in 'BRZ':
                # Extract qframe data.
                qframe = os.path.join(datadir, f'{night}', f'{expid:08d}', f'qframe-{cam.lower()}{sp}-{expid:08d}.fits')

                if not os.path.exists(qframe):
                    raise FileNotFoundError(qframe)

                # Sanity check to make sure the input program matches the exposure.
                h = fitsio.read_header(qframe, ext='FIBERMAP')
                hprog = h['PROGRAM']
                if prog != hprog:
                    raise ValueError(f'Program "{prog}" does not match "{hprog}"')

                arclines = wavelengths[cam]
                nlines = len(arclines)

                # Extract spectra from the central 20 fibers in each camera.
                fits = fitsio.FITS(qframe)
                wave = np.median(fits['WAVELENGTH'][fiberlo:fiberhi, :], axis=0)
                flux = np.median(fits['FLUX'][fiberlo:fiberhi, :], axis=0)

                # Pseudo-equivalent width calculation. For each line:
                # - Select a window +/-n pixels around the line center.
                # - Integrate CCD counts vs wavelength.
                for arcline in arclines:
                    pk = np.argmin(np.abs(wave - arcline))
                    i = np.maximum(pk-npix, 0)
                    j = np.minimum(pk+npix, len(wave)-1)
                    area = np.trapz(flux[i:j], wave[i:j])

                    if arcline in lineareas[sp][cam]:
                        lineareas[sp][cam][arcline].append(area)
                    else:
                        lineareas[sp][cam][arcline] = [area]

        # Compute mean and uncertainty for each line.
        for cam in 'BRZ':
            for arcline in lineareas[sp][cam]:
                area  = np.average(lineareas[sp][cam][arcline])
                darea = np.std(lineareas[sp][cam][arcline])
                if np.abs(darea / area) > 0.1:
                    print(f'Warning: large uncertainty in {arcline} line area: {area:.1f} +- {darea:.1f}')
                lineareas[sp][cam][arcline] = np.round(area)

            # Store only the list of areas for all lines in the camera.
            nominal = [v for v in lineareas[sp][cam].values()]
            upper_err = [(1 + errlevel)*n for n in nominal]
            upper = [(1 + warnlevel)*n for n in nominal]
            lower = [(1 - warnlevel)*n for n in nominal]
            lower_err = [(1 - errlevel)*n for n in nominal]

            lineareas[sp][cam] =      { 'upper_err' : list(upper_err) }
            lineareas[sp][cam].update({ 'upper' : list(upper) })
            lineareas[sp][cam].update({ 'nominal' : list(nominal) })
            lineareas[sp][cam].update({ 'lower' : list(lower) })
            lineareas[sp][cam].update({ 'lower_err' : list(lower_err) })

        # Store inputs.
        inputs = { 'comment' : '(night,expid) used to compute arc lamp lines' }
        inputs['nightexpids'] = [[night, expid] for expid in expids]

    return lineareas, inputs


if __name__ == '__main__':
    print('\033[91m\n** WARNING** : script eprecated. Use gen_arc_refs.py\033[0m\n')

    p = ArgumentParser(usage='{prog} [options]',
                       formatter_class=ArgumentDefaultsHelpFormatter)
    p.add_argument('-n', '--nightexpids', type=str,
                   help='INI file of input night + expids to use for arc lines')
    p.add_argument('-i', '--indir', type=str,
                   help='Base folder with Nightwatch processed data.',
                   default='/global/cfs/cdirs/desi/spectro/nightwatch/nersc')
    p.add_argument('--level-warn-long', dest='levwarnlg', type=float, default=0.06,
                   help='Deviation from nominal area: warnings (long arc).')
    p.add_argument('--level-error-long', dest='leverrlg', type=float, default=0.12,
                   help='Deviation from nominal area: errors (long arc).')
    p.add_argument('--level-warn-short', dest='levwarnsh', type=float, default=0.12,
                   help='Deviation from nominal area: warnings (short arc).')
    p.add_argument('--level-error-short', dest='leverrsh', type=float, default=0.24,
                   help='Deviation from nominal area: errors (short arc).')
    p.add_argument('-o', '--outfile', type=str,
                   help='Output json file with line info.',
                   default='test.json')
    p.add_argument('-v', '--verbose', action='store_true',
                   help='Verbose output during processing.')
    args = p.parse_args()

    # Load the configuration.
    conf = ConfigParser()
    conf.read(args.nightexpids)

    # Run through the different configurations.
    for cal in conf.sections():
        print(f'Computing arc cals for {cal}...')

        night = int(conf[cal]['night'])
        expids = [int(_) for _ in conf[cal]['expids'].split()]
        program = conf[cal]['program']
        if 'short' in program:
            level_wrn = args.levwarnsh
            level_err = args.leverrsh
        else:
            level_wrn = args.levwarnlg
            level_err = args.leverrlg

        print(program, level_wrn, level_err)

        lnarea, inputs = calc_arc_lines(args.indir, night, expids, program,
                                wavelengths = calarcs[program]['wavelength'],
                                warnlevel = level_wrn, errlevel = level_err)
        calarcs[program]['area'] = { 'spectrograph' : lnarea }
        calarcs[program]['area']['inputs'] = inputs

    # Output to JSON.
    with open(args.outfile, 'w') as json_file:
        json.dump(calarcs, json_file, indent=4)

