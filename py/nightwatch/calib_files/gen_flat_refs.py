"""Generate reference levels for flat exposure fluxes, fitting and
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
    p.add_argument('-p', '--plot', action='store_true',
                   help='Plot fits and reference fluxes')
    p.add_argument('-v', '--verbose', action='store_true',
                   help='Verbose output during processing')
    args = p.parse_args()
    
    # Load the configuration.
    conf = ConfigParser()
    conf.read(args.configfile)
    
    # Storage for a list of temperature detrending constants for each spectrograph.
    # - Correction constants will be the best-fit slope and median T in the measurement.
    # - References will be mean corrected flux + warning and error levels.
    
    flatrefs = { }

    print(f'Computing calibration constants and fits...')
    for cal in tqdm(conf.sections()):
        
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
        flatrefs[program] = {
            'settings' : {
                'fiberlo'   : fiberlo,
                'fiberhi'   : fiberhi,
                'comment'   : 'Fiber range used in integrated fluxes.',
                'startdate' : night0,
                'enddate'   : night1
            }
        }
        
        # Pull out comma-separated list of dates and/or ranges to mask.
        if 'maskdates' in conf[cal]:
            flatrefs[program]['settings']['maskdates'] = conf[cal]['maskdates']
            
            # Remove masked dates from the QA time selection.
            maskdates = conf[cal]['maskdates'].split(',')
            for maskdate in maskdates:
                if '-' in maskdate:
                    # Check for a range of masked dates.
                    d1, d2 = [int(_) for _ in maskdate.split('-')]
                    select_nights = select_nights & ~((nights >= d1) & (nights <= d2))
                else:
                    select_nights = select_nights & ~(nights == int(maskdate))
        
        # Loop over cameras:
        for band in 'BRZ':
            quantity = f'{band}_INTEG_FLUX'
        
            # Loop over spectrographs:
            for spec in np.arange(10):
                
                T = caltab['TAIRTEMP']
                f = caltab[f'{quantity}_sp{spec:d}']
                df = np.ones_like(f)
                
                # Quality selection.
                nonzero = f > 0
                select = select_nights & nonzero
                
                # Fit a linear function to the temperature dependence and zero it out.
                Tmed = np.median(T[select])
                a, b, fitstatus = linear_fit(T[select], f[select], df[select])
                fcorr = f[select] - b*(T[select] - Tmed)
                
                # Store best fit slope and median for temperature corrections.
                bandspec = f'{band}{spec}'
                
                flatrefs[program][bandspec] = {
                    'tempfit' : { 
                        'slope' : b, 'Tmedian' : Tmed
                    }
                }
                
                # Compute corrected flux distributions and write reference levels.
                favg = np.mean(fcorr)
                fstd = np.std(fcorr)
                
                flatrefs[program][bandspec]['refs'] = {
                    'upper_err' : 1.10*favg,
                    'upper'     : 1.05*favg,
                    'nominal'   : favg,
                    'lower'     : 0.95*favg,
                    'lower_err' : 0.9*favg 
                }
                
        # Plot results if requested.
        if args.plot:
            fig, axes = plt.subplots(3, 1, figsize=(12,8), sharex=True, tight_layout=True)
            colors = ['#1f77b4', '#d62728', '#8c564b']

            for i, band in enumerate('BRZ'):
                quantity = f'{band}_INTEG_FLUX'
                upper_err, upper, nominal, lower, lower_err = [], [], [], [], []

                for spec in np.arange(10):
                    bandspec = f'{band}{spec}'
                    upper_err.append(flatrefs[program][bandspec]['refs']['upper_err'])
                    upper.append(flatrefs[program][bandspec]['refs']['upper'])
                    nominal.append(flatrefs[program][bandspec]['refs']['nominal'])
                    lower.append(flatrefs[program][bandspec]['refs']['lower'])
                    lower_err.append(flatrefs[program][bandspec]['refs']['lower_err'])

                ax = axes[i]
                ax.fill_between(range(10), lower_err, upper_err, color=colors[i], alpha=0.2)
                ax.fill_between(range(10), lower, upper, color=colors[i], alpha=0.2)
                ax.plot(range(10), nominal, color=colors[i])
                ax.set(xticks=range(10), xlim=(0,9), ylabel=quantity)
                if i == 2:
                    ax.set(xlabel='spectrograph')

            fig.suptitle(f'{program} flux references (detrended + cleaned) thru {night1}')
            fig.savefig(f'qa_{program.replace(" ", "_")}.png', dpi=100)

    # Write output to JSON.
    with open(args.outfile, 'w') as json_file:
        json.dump(flatrefs, json_file, indent=4)
