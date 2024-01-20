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
    p.add_argument('--level-warn', dest='levwarn', type=float, default=0.05,
                   help='Deviation from nominal area: warnings.')
    p.add_argument('--level-error', dest='leverr', type=float, default=0.10,
                   help='Deviation from nominal area: errors.')
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
                    
        # Set up reference level histogram plots if requested.
        if args.plot:
            fig_hs, axes_hs = plt.subplots(10,3, figsize=(10, 30), tight_layout=True)
        
        # Loop over cameras:
        for cam, band in enumerate('BRZ'):
            quantity = f'{band}_INTEG_FLUX'
            
            # Set up time series and reference level plots if requested.
            if args.plot:
                fig_ts, axes_ts = plt.subplots(10, 1, figsize=(10, 20), sharex=True, gridspec_kw={'hspace':0})
        
            # Loop over spectrographs:
            for spec in np.arange(10):
                
                t = caltab['DATEOBS'].datetime
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
                # Do a quick and dirty cleanup of outliers.
                favg = np.mean(fcorr)
                fstd = np.std(fcorr)
                
                clean = (fcorr > favg-3*fstd) & (fcorr < favg+3*fstd)
                nominal = np.percentile(fcorr[clean], 50)
                fstd_clean = np.std(fcorr[clean])
                
                fracerr = fstd_clean / nominal
                warnlev = args.levwarn if args.levwarn > fracerr else fracerr
                errlev = args.leverr if args.leverr > 2*fracerr else 2*fracerr
                
                upper_err = (1 + errlev)*nominal
                upper = (1 + warnlev)*nominal
                lower = (1 - warnlev)*nominal
                lower_err = (1 - errlev)*nominal
                
                # lower, upper = nominal - 1.5*fstd_clean, nominal + 1.5*fstd_clean
                # lower_err, upper_err = nominal - 3*fstd_clean, nominal + 3*fstd_clean
                                
                flatrefs[program][bandspec]['refs'] = {
                    'upper_err' : upper_err,
                    'upper'     : upper,
                    'nominal'   : nominal,
                    'lower'     : lower,
                    'lower_err' : lower_err 
                }
                
                # Plot the time series and flux distributions if requested.
                if args.plot:
                    # Time series.
                    ax = axes_ts[spec]
                    ax.scatter(t[select], f[select], label=f'{quantity}_sp{spec:d}')
                    ax.scatter(t[select], fcorr, label=f'{quantity}_sp{spec:d} ($T$-corr.)')
                    ax.legend(loc='upper left', fontsize=8)
                    if spec == 1:
                        ax.set(ylabel=f'{quantity} [$10^7$ counts]')
                    
                    # Distributions.
                    fbins = np.linspace(favg - 2*fstd, favg+2*fstd, 40)
                    ax = axes_hs[spec][cam]
                    ax.hist(f[select], bins=fbins, label=f'{band}{spec}', alpha=0.7)
                    ax.hist(fcorr, bins=fbins, label=f'{band}{spec} (corr.)', alpha=0.7)
                    for ln in (lower_err, lower, nominal, upper, upper_err):
                        ax.axvline(ln, color='k', ls=':', alpha=0.7)
                    ax.set(xlabel=f'{quantity}', ylabel='count')
                    ax.legend(loc='upper left', fontsize=8)
            
            # Save time series and histograms if requested.
            if args.plot:
                ax = axes_ts[-1]
                ax.xaxis.set_major_locator(mpl.dates.MonthLocator(bymonth=range(1,13), bymonthday=1))
                fig_ts.autofmt_xdate()
                fig_ts.tight_layout()
                fig_ts.savefig(f'qa_{program.replace(" ", "_")}_{quantity}_timeseries.png', dpi=100)
                plt.close(fig_ts)
                
        # Plot flux histograms and reference levels if requested.
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
            plt.close(fig)
            
            fig_hs.savefig(f'qa_{program.replace(" ", "_")}_hist.png', dpi=100)
            plt.close(fig_hs)

    # Write output to JSON.
    with open(args.outfile, 'w') as json_file:
        json.dump(flatrefs, json_file, indent=4)
