"""Generate reference levels for arc line fluxes, fitting and
correcting for the temperature dependence of the flux.

The output is written to a JSON file used by Nightwatch to compare the daily
calibrations against these temperature-corrected references.
"""

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

from scipy.optimize import minimize

from glob import glob
import os

import json
from astropy.table import Table, vstack

from configparser import ConfigParser
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

from tqdm import tqdm


def l2norm_linear(x, y, dy):
    """Standard least-squares regression.
    
    Parameters
    ----------
    x, y, dy: list or ndarray
        Independent and dependent variables + uncertainties. 
    
    Returns
    -------
    a, b: float
        Best-fit intercept and slope.
    """
    A = np.vander(x, 2)
    C = np.diag(dy * dy)
    ATA = np.dot(A.T, A / (dy**2)[:,None])
    cov = np.linalg.inv(ATA)
    w = np.linalg.solve(ATA, np.dot(A.T, y / dy ** 2))
    a, b = w[::-1]
    return a, b


def l1norm_linear(pars, x, y, dy):
    """L1-norm regression (reduced sensitivity to outliers).
    
    Parameters
    ----------
    pars : list or tuple
        Fit parameters.
    x, y, dy: list or ndarray
        Independent and dependent variables + uncertainties. 
    
    Returns
    -------
    l1: float
        The l1 norm.
    """
    a, b = pars
    return np.sum(np.abs((y - (a + b*x)) / dy))


def linear_fit(x, y, dy):
    """Try a quick linear fit.
    Start with a standard least-squares fit and use the result to seed
    an l1-norm fit. If the l1-norm converges, use it as the best fit.
    """
    a, b = l2norm_linear(x, y, dy)
    fitres = minimize(l1norm_linear, [a,b], args=(x, y, dy), method='Nelder-Mead')
    if fitres.success:
        a, b = fitres.x
        
    return a, b, fitres.success


if __name__ == '__main__':
    p = ArgumentParser(usage='{prog} [options]',
                       formatter_class=ArgumentDefaultsHelpFormatter)
    p.add_argument('-c', '--configfile', type=str,
                   help='INI file of inputs for cals')
    p.add_argument('-o', '--outfile', type=str,
                   help='Output JSON file with cal info',
                   default='test.json')
    p.add_argument('-v', '--verbose', action='store_true',
                   help='Verbose output during processing')
    args = p.parse_args()
    
    # Load the configuration.
    conf = ConfigParser()
    conf.read(args.configfile)
    
    # Storage for a list of temperature detrending constants for each spectrograph.
    # - Correction constants will be the best-fit slope and median T in the measurement.
    # - References will be mean corrected flux + warning and error levels.
    arcrefs = {
        'CALIB short Arcs all': {
            'wavelength' : {
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

    for cal in conf.sections():
        
        # Extract configuration and file data.
        program = conf[cal]['program']
        caltab = Table.read(conf[cal]['infile'])
        nights = np.asarray(caltab['NIGHT']).astype(int)
        night0 = int(conf[cal]['startdate'])
        night1 = int(conf[cal]['enddate'])
        
        # Grab data only from the specified time range.
        select_nights = (nights >= night0) & (nights <= night1)
        
        fiberlo = 240       # ID of lowest fiber used in extracting spectrum.
        fiberhi = 260       # ID of highest fiber used in extracting spectrum.
        npix = 12           # Number of pixels around the line center for computing pEW
        arcrefs[program]['area'] = {
            'spectrograph' : {
                'settings' : {
                    'fiberlo'   : fiberlo,
                    'fiberhi'   : fiberhi,
                    'npix'      : npix,
                    'comment'   : 'Fiber range used in spectrum; number of pixels used around line center.',
                    'startdate' : night0,
                    'enddate'   : night1
                }
            }
        }
        
        # Pull out comma-separated list of dates and/or ranges to mask.
        if 'maskdates' in conf[cal]:
            arcrefs[program]['area']['spectrograph']['settings']['maskdates'] = conf[cal]['maskdates']
            
            # Remove masked dates from the QA time selection.
            maskdates = conf[cal]['maskdates'].split(',')
            for maskdate in maskdates:
                if '-' in maskdate:
                    # Check for a range of masked dates.
                    d1, d2 = [int(_) for _ in maskdate.split('-')]
                    select_nights = select_nights & ~((nights >= d1) & (nights <= d2))
                else:
                    select_nights = select_nights & ~(nights == int(maskdate))
        
        # Loop over spectrographs:
        print(f'Computing fits and references for {program}...')
        for spec in tqdm(np.arange(10)):
            arcrefs[program]['area']['spectrograph'][str(spec)] = { 
                'B' : { 'slope':[], 'Tmedian':[], 'upper_err':[], 'upper':[], 'nominal':[], 'lower':[], 'lower_err':[] }, 
                'R' : { 'slope':[], 'Tmedian':[], 'upper_err':[], 'upper':[], 'nominal':[], 'lower':[], 'lower_err':[] },
                'Z' : { 'slope':[], 'Tmedian':[], 'upper_err':[], 'upper':[], 'nominal':[], 'lower':[], 'lower_err':[] }
            }
                        
            # Loop over bands:
            for band in 'BRZ':
                wavelengths = arcrefs[program]['wavelength'][band]
                
                # Loop over all wavelengths in this band, in this program.
                for wave in wavelengths:
                    quantity = f'{band}{wave:g}_sp{spec}'
                    T = caltab['TAIRTEMP']
                    f = caltab[quantity]
                    df = np.ones_like(f)

                    # Quality selection.
                    nonzero = f > 0
                    select = select_nights & nonzero

                    # Fit a linear function to the temperature dependence and zero it out.
                    Tmed = np.median(T[select])
                    a, b, fitstatus = linear_fit(T[select], f[select], df[select])
                    fcorr = f[select] - b*(T[select] - Tmed)

                    # Store best fit slope and median for temperature corrections.
                    arcrefs[program]['area']['spectrograph'][str(spec)][band]['slope'].append(b)
                    arcrefs[program]['area']['spectrograph'][str(spec)][band]['Tmedian'].append(Tmed)
                
                    # Compute corrected flux distributions and write reference levels.
                    favg = np.mean(fcorr)
                    fstd = np.std(fcorr)
                    
                    arcrefs[program]['area']['spectrograph'][str(spec)][band]['upper_err'].append(favg + 3*fstd)
                    arcrefs[program]['area']['spectrograph'][str(spec)][band]['upper'].append(favg + 1.5*fstd)
                    arcrefs[program]['area']['spectrograph'][str(spec)][band]['nominal'].append(favg)
                    arcrefs[program]['area']['spectrograph'][str(spec)][band]['lower'].append(favg - 1.5*fstd)
                    arcrefs[program]['area']['spectrograph'][str(spec)][band]['lower_err'].append(favg - 3*fstd)
    
    # Write output to JSON.
    with open(args.outfile, 'w') as json_file:
        json.dump(arcrefs, json_file, indent=4)
