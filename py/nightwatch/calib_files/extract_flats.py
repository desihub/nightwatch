"""This program extracts the flat exposure fluxes computed by Nightwatch and
saved to FITS format in the qa-00NNNNNN.fits QA files produced for each
exposure. The fluxes correspond to the sum of the light in fibers 240..260
in each CCD. Here we dump the fluxes to flat ECSV files for later processing.

Help is available by running

$> python extract_flats.py -h

An example command to process one month of data from one particular flat
program on NERSC is:

$> python extract_flats.py extract -y YYYY -m MM -s N

To quickly spin through a year of data, you can use GNU parallel on
NERSC (see https://docs.nersc.gov/jobs/workflow/gnuparallel/). E.g.,

$> seq 1 12 | parallel python extract_flats.py extract -y YYYY -m {} -s 4

To merge the data, run something like this:

$> python extract_flats.py merge -i qa_LED03_flat_for_CTE_check_YYYY*ecsv -f -o qa_LED03_flat_for_CTE_check.ecsv 

python 
"""

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

from glob import glob

import fitsio
import itertools
import os

from astropy.table import Table, vstack
from astropy.time import Time

import numpy as np

from tqdm import tqdm

nw_path = '/global/cfs/cdirs/desi/spectro/nightwatch/nersc/'


def get_program_data(night, program, qtty):
    """Extract QA data from Nightwatch files.

    Parameters
    ----------
    night : str
        Absolute or relative path to night of reductions.
    program : str
        Name of ICS program (i.e., exposure type).
    qtty: str or list
        List of quantities to extract from QA files.
    """
    yyyymmdd = os.path.basename(night)
    quantities = qtty if isinstance(qtty, (list, np.ndarray)) else [qtty]

    tempdata = []
    expids = []
    nights = []
    datetimes = []
    nightdata = {}
    exposures = sorted(glob(os.path.join(night, '00*')))

    for exposure in exposures:
        expid = os.path.basename(exposure)
        qafile = os.path.join(exposure, f'qa-{expid}.fits')
        if not os.path.exists(qafile):
            continue

        h = fitsio.read_header(qafile)
        if h['PROGRAM'] != program:
            continue

        with fitsio.FITS(qafile) as fits:
            if not 'PER_SPECTRO' in fits:
                continue
                
            for quantity in quantities:
                data = fits['PER_SPECTRO'][quantity][:]
                if quantity in nightdata:
                    nightdata[quantity] = np.vstack((nightdata[quantity], data))
                else:
                    nightdata[quantity] = data

            tempdata.append(h['TAIRTEMP'])
            expids.append(h['EXPID'])
            nights.append(yyyymmdd)
            datetimes.append(Time(h['DATE-OBS'], scale='utc'))

    tab = None
    
    if bool(nightdata):
        tab = Table()
        tab['NIGHT'] = nights
        tab['DATEOBS'] = datetimes
        tab['EXPID'] = expids
        tab['TAIRTEMP'] = tempdata
        for quantity in quantities:
            names = [f'{quantity}_sp{s}' for s in range(0,10)]
            for i, name in enumerate(names):
                if quantity in nightdata:
                    if nightdata[quantity].ndim > 1:
                        tab[names[i]] = nightdata[quantity][:,i]
                    else:
                        tab[names[i]] = nightdata[quantity][i]
        
    return tab


def extract_qa_data(args):
    """Extract QA data from FITS files for a given year, month, and obstype.
    """
    
    # Set up search parameters.
    if args.sequence == 4:
        program = 'LED03 flat for CTE check'
    else:
        program = f'CALIB DESI-CALIB-{args.sequence:02d} LEDs only'

    yyyymm = f'{args.year}{args.month:02d}'
    nights = sorted(glob(os.path.join(nw_path, f'{yyyymm}*')))

    tabs = None
    for night in tqdm(nights):
        nighttab = get_program_data(night, program, ['B_INTEG_FLUX', 'R_INTEG_FLUX', 'Z_INTEG_FLUX'])
        if nighttab is None:
            continue
            
        if tabs is None:
            tabs = nighttab
        else:
            tabs = vstack([tabs, nighttab])

    if tabs is not None:
        of = f'qa_{program.replace(" ", "_")}_{yyyymm}.ecsv'
        print(f'Writing output to {of}...')
        tabs.write(f'qa_{program.replace(" ", "_")}_{yyyymm}.ecsv', format='ascii.ecsv', overwrite=True)


def merge_qa_data(args):
    """Merge QA data extracted from FITS files.
    """
    caltabs = None
    
    for ifile in tqdm(args.infiles):
        tab = Table.read(ifile)
        caltabs = tab if caltabs is None else vstack([caltabs, tab])
    
    caltabs.write(args.output, format='ascii.ecsv', overwrite=args.force)

        
if __name__ == '__main__':
    p = ArgumentParser(description='Extract NW LED fluxes',
                       formatter_class=ArgumentDefaultsHelpFormatter)
    sp = p.add_subparsers(help='commands')
    
    # Extraction of data from QA files.
    qap = sp.add_parser('extract', help='Extract flat exposure QA data')
    qap.add_argument('-p', '--path', default=nw_path,
                     help='Abs. path to NW data')
    qap.add_argument('-y', '--year', default=2023, type=int,
                     help='year [YYYY]')
    qap.add_argument('-m', '--month', default=1, type=int,
                     help='month')
    qap.add_argument('-s', '--sequence', choices=range(0,5), default=0, type=int,
                     help='LED sequence')
    qap.set_defaults(func=extract_qa_data)
    
    # Merger of QA data into a single flat file.
    mp = sp.add_parser('merge', help='Merge extracted QA data into one file')
    mp.add_argument('-f', '--force', action='store_true',
                    help='Force overwrite of output file')
    mp.add_argument('-i', '--infiles', nargs='+',
                    help='List of input files to merge')
    mp.add_argument('-o', '--output', default='test.ecsv',
                    help='Merged output [ECSV format]')
    mp.set_defaults(func=merge_qa_data)

    args = p.parse_args()
    args.func(args)
