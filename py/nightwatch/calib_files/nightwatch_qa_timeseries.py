# coding: utf-8
from nightwatch.calib_files.calc_arclines import calarcs

from glob import glob
import fitsio
import itertools
import json
import os

from tqdm import tqdm

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

mpl.rc('font', size=14)

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)

caldata = {}

for program in calarcs:
#for program in [ 'CALIB long Arcs Cd+Xe' ]:
    caldata[program] = { }
#    for quantity in [ 'B3612', 'B4679' ]:
#        caldata[program][quantity] = None
    for band in 'BRZ':
        for wl in calarcs[program]['wavelength'][band]:
            quantity = f'{band}{wl:g}'
            caldata[program][quantity] = None

nw_path = '/global/cfs/cdirs/desi/spectro/nightwatch/nersc/'
months = ['202302', '202303', '202304', '202305', '202306']
#months = ['202302']
nightfolders = [sorted(glob(os.path.join(nw_path, f'{m}*'))) for m in months]
nightfolders = list(itertools.chain.from_iterable(nightfolders))

for nightfolder in tqdm(nightfolders):
    night = os.path.basename(nightfolder)
    tempdata = { }
    nightdata = { }

    for program in caldata:
        nightdata[program] = { }
        tempdata[program] = None
        for quantity in caldata[program]:
            nightdata[program][quantity] = None

    exposures = sorted(glob(os.path.join(nightfolder, '00*')))
    for exposure in exposures:
        expid = os.path.basename(exposure)
        qafile = os.path.join(exposure, f'qa-{expid}.fits')
        if not os.path.exists(qafile):
            continue

        # Skip files that are not part of a calibration program.
        h = fitsio.read_header(qafile)
        program = h['PROGRAM']
        if program not in caldata:
            continue

        # Open the FITS data and read the calibration output.
        with fitsio.FITS(qafile) as fits:
            if not 'PER_SPECTRO' in fits:
                continue
                
            for quantity in caldata[program]:
                if quantity not in fits['PER_SPECTRO'].get_colnames():
                    continue

                data = fits['PER_SPECTRO'][quantity][:]

                if nightdata[program][quantity] is None:
                    nightdata[program][quantity] = data
                else:
                    nightdata[program][quantity] = np.vstack((nightdata[program][quantity], data))

            if tempdata[program] is None:
                tempdata[program] = [h['TAIRTEMP']]
            else:
                tempdata[program].append(h['TAIRTEMP'])

    # Accumulate night averages for each calibration feature in each calibration program.
    for program in nightdata:
        if tempdata[program] is None:
            continue

        tavg = np.average(tempdata[program])

        for quantity in nightdata[program]:
            avg = np.average(nightdata[program][quantity], axis=0)
            std = np.std(nightdata[program][quantity], axis=0)

            if caldata[program][quantity] is None:
                caldata[program][quantity] = { 'NIGHT' : [night], 'TAIRTEMP' : [tavg], 'AVG' : avg, 'STD' : std }
            else:
                caldata[program][quantity]['NIGHT'].append(night)
                caldata[program][quantity]['TAIRTEMP'].append(tavg)
                caldata[program][quantity]['AVG'] = np.vstack((caldata[program][quantity]['AVG'], avg))
                caldata[program][quantity]['STD'] = np.vstack((caldata[program][quantity]['STD'], std))

with open('caldata.json', 'w') as caldata_file:
    caldata_file.write(json.dumps(caldata, cls=NumpyEncoder))

colors = { 'B':'C0', 'R':'C3', 'Z':'C6' }

for program in caldata:
    for quantity in caldata[program]:

        n = 10
        ncol = 5
        nrow = int(np.ceil(n / ncol))
        fig, axes = plt.subplots(nrow, ncol, figsize=(4*ncol, 3*nrow), sharex=True)
        axes = axes.flatten()
        for i in np.arange(10, nrow*ncol):
            axes[i].axis('off')

        for spec in np.arange(10):
            ax = axes[spec]
            t = np.asarray(caldata[program][quantity]['TAIRTEMP'])
            f = caldata[program][quantity]['AVG'][:,spec]
            df = caldata[program][quantity]['STD'][:,spec]

            # Bit of cleanup:
            nonzero = f > 0

            ax.errorbar(t[nonzero], f[nonzero], yerr=df[nonzero], fmt='.', color=colors[quantity[0]])
            ax.set_title(f'{quantity}: Spectrograph {spec}', fontsize=14)

            # Quick linear fit.
            A = np.vander(t[nonzero], 2)
            C = np.diag(df[nonzero] * df[nonzero])
            ATA = np.dot(A.T, A / (df[nonzero]**2)[:,None])
            cov = np.linalg.inv(ATA)
            w = np.linalg.solve(ATA, np.dot(A.T, f[nonzero] / df[nonzero] ** 2))
            a, b = w[::-1]

            x2 = np.sum(((f[nonzero] - a - b*t[nonzero]) / df[nonzero])**2)
            ndf = np.sum(nonzero) - 2

            # Plot results.
            T = np.arange(0.9*np.min(t[nonzero]), 1.1*np.max(t[nonzero]), 0.1)
            ax.plot(T, a + b*T, ls='--', lw=1, color='k',
                    label=f'{a:.1f} - {np.abs(b):.1f}$\cdot$T\n$\chi^2 = {x2:.1f}$ / {ndf:d}')
            ax.legend(loc='upper right', fontsize=10)

            if spec >= 5:
                ax.set(xlabel='air temperature [C]')

        fig.tight_layout()
        fig.savefig(f'temp_dependence_{program.replace(" ", "_")}_{quantity}.png', dpi=150);
        plt.close(fig)
