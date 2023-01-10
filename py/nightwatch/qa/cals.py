from .base import QA
from glob import glob
import os
import collections

import numpy as np
import fitsio
import json

from astropy.table import Table

from ..calibrations import pick_calib_file, get_calibrations


class QACalibArcs(QA):
    """Class representing arc lamp QA, tracking identified bright lines.
    
    Methods:
        valid_obstype(self, obstype): Given the obstype of an exposure, returns whether QACalibArcs is a valid QA metric. QACalibArcs is currently valid for all exposures.
        run(self, indir): Given path to directory containing qproc logfiles + errorcodes.txt file, returns Astropy table with QPROCStatus data.
    """
    
    def __init__(self):
        self.output_type = 'PER_SPECTRO'
    
    def valid_obstype(self, obstype):
        """Obstype must be an ARC exposure.
        """
        return obstype.upper() == 'ARC'
    
    def run(self, indir):
        """Loop through ARC qframes and identify the pseudo-equivalent widths of prominent lines.

        Returns Table object with columns:
    
        NIGHT  EXPID  SPECTRO  LINE1  LINE2  LINE3 ...
                               [arc line pseudo-eq widths in these columns]
        """
        # get night, expid data
        qframes = sorted(glob(os.path.join(indir, 'qframe-*.fits')))
        hdr = fitsio.read_header(qframes[0], ext='FIBERMAP')
        night = hdr['NIGHT']
        expid = hdr['EXPID']
        program = hdr['PROGRAM']

        # get arc line calibration data. 
        calibfile = pick_calib_file('CALIB-ARCS', night)
        cals = get_calibrations(calibfile, program)
        settings = cals['area']['spectrograph']['settings']

        fiberlo = settings['fiberlo']
        fiberhi = settings['fiberhi']
        npix = settings['npix']

        wavelengths = cals['wavelength']

        results = []
        # Loop through spectrographs.
        for spectro in range(10):
            dico = dict()
            dico['NIGHT'] = night
            dico['EXPID'] = expid
            dico['PROGRAM'] = program
            dico['SPECTRO'] = spectro

            # Loop over cameras.
            for cam in 'BRZ':
                qframe = os.path.join(indir, f'qframe-{cam}{spectro}-{expid:08d}.fits')

                # Loop over the brightest arc lines in each camera.
                if os.path.exists(qframe):
                    fits = fitsio.FITS(qframe)
                    wave = np.median(fits['WAVELENGTH'][fiberlo:fiberhi, :], axis=0)
                    flux = np.median(fits['FLUX'][fiberlo:fiberhi, :], axis=0)

                    for arcline in wavelengths[cam]:
                        linelabel = f'{cam}{arcline:g}'

                        # Measure the pEqW by computing the flux integral in a
                        # small window around the line's central wavelength.
                        pk = np.argmin(np.abs(wave - arcline))
                        i = np.maximum(pk-npix, 0)
                        j = np.minimum(pk+npix, len(wave)-1)
                        area = np.trapz(flux[i:j], wave[i:j])
                        dico[linelabel] = area
                else:
                    for arcline in wavelengths[cam]:
                        linelabel = f'{cam}{arcline:g}'
                        dico[linelabel] = -1

            results.append(collections.OrderedDict(**dico))

        return Table(results, names=results[0].keys())

