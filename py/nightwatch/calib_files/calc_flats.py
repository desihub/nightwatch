import os
import json
import fitsio

import numpy as np

from glob import glob
from tqdm import tqdm
from configparser import ConfigParser
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

from warnings import warn

calflats = {
    'CALIB DESI-CALIB-00 LEDs only' : None,
    'CALIB DESI-CALIB-01 LEDs only' : None,
    'CALIB DESI-CALIB-02 LEDs only' : None,
    'CALIB DESI-CALIB-03 LEDs only' : None,
    'LED03 flat for CTE check' : None
}


def calc_flats(datadir, night, expids, prog, warnlevel=0.01, errlevel=0.02):
    """Compute integrated flux in all spectrographs and cameras.

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
    warnlevel : float
        Fractional deviation from nominal level for warnings [0-1].
    errlevel : float
        Fractional deviation from nominal level for errors [0-1].

    Returns
    -------
    integ_flux : dict
        Dictionary of integrated fluxes in each camera.
    """
    fiberlo = 240       # ID of lowest fiber used in extracting spectrum.
    fiberhi = 260       # ID of highest fiber used in extracting spectrum.

    integ_flux = {
        'settings' : {
            'fiberlo' : fiberlo,
            'fiberhi' : fiberhi,
            'comment' : 'Fiber range used in integrated fluxes.'
        }
    }

    # Loop over all spectrographs.
    for sp in tqdm(range(10)):

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

                spcam = f'{cam}{sp}'
                if spcam not in integ_flux:
                    integ_flux[spcam] = []

                # Extract spectra from the central 20 fibers in each camera.
                fits = fitsio.FITS(qframe)
                wave = np.median(fits['WAVELENGTH'][fiberlo:fiberhi, :], axis=0)
                flux = np.median(fits['FLUX'][fiberlo:fiberhi, :], axis=0)
                integ_flux[spcam].append(np.trapz(flux, wave))

        # Compute mean and uncertainty for each line.
        for cam in 'BRZ':
            spcam = f'{cam}{sp}'
            flavg = np.mean(integ_flux[spcam])
            flstd = np.std(integ_flux[spcam])
            fracerr = flstd / flavg

            warnlev = warnlevel if warnlevel > fracerr else fracerr
            errlev = errlevel if errlevel > 2*fracerr else 2*fracerr

            integ_flux[spcam] = {
                'upper_err' : (1 + errlev)*flavg,
                'upper' : (1 + warnlev)*flavg,
                'nominal' : flavg,
                'lower' : (1 - warnlev)*flavg,
                'lower_err' : (1 - errlev)*flavg
            }

        # Store inputs.
        inputs = { 'comment' : '(night,expid) used to compute flats' }
        inputs['nightexpids'] = [[night, expid] for expid in expids]

    return integ_flux, inputs


if __name__ == '__main__':
    print('\n** WARNING ** This program is deprecated; use gen_flats.py\n')

    p = ArgumentParser(usage='{prog} [options]',
                       formatter_class=ArgumentDefaultsHelpFormatter)
    p.add_argument('-n', '--nightexpids', type=str,
                   help='INI file of input night + expids to use for arc lines')
    p.add_argument('-i', '--indir', type=str,
                   help='Base folder with Nightwatch processed data.',
                   default='/global/cfs/cdirs/desi/spectro/nightwatch/nersc')
    p.add_argument('--level-warn', dest='levwarn', type=float, default=0.05,
                   help='Deviation from nominal area: warnings.')
    p.add_argument('--level-error', dest='leverr', type=float, default=0.10,
                   help='Deviation from nominal area: errors.')
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
        level_wrn = args.levwarn
        level_err = args.leverr

        print(program, level_wrn, level_err)

        intflux, inputs = calc_flats(args.indir, night, expids, program,
                                warnlevel = level_wrn, errlevel = level_err)
        calflats[program] = intflux
        calflats[program].update(inputs)

    # Output to JSON.
    with open(args.outfile, 'w') as json_file:
        json.dump(calflats, json_file, indent=4)

