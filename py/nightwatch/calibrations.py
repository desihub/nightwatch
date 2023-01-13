import os
import re
import json
import numpy as np

from glob import glob

from pkg_resources import resource_filename


def get_outdir():
    """Retrieve the path to the calibration files in the Nightwatch installation.
    """
    return resource_filename('nightwatch', 'calib_files')


def pick_calib_file(name, night, outdir=None, in_nightwatch=True):
    """Pick the right calibration file to use for a given calibration exposure
    type and night. If no file is found, pick the earliest file.

    Arguments:
        name : type of calibration exposure, arc or flat (str).
        night : night the calibrations are needed, in YYYYMMDD format (int).
    Options:
        outdir : specify where to look for calibration files (str). 
        in_nightwatch : if true, look in nightwatch folder for files (bool).
    Output:
        filepath : path to the correct calibration file.
    """
    # Set up the correct search folder.
    if not in_nightwatch and outdir is not None:
        calib_dir = outdir
    else:
        calib_dir = get_outdir()

    # Search for the most recent calibration files.
    file_pattern = f'{name}-*.json'
    calib_files = sorted(glob(os.path.join(calib_dir, file_pattern)), reverse=True)
    for filepath in calib_files:
        zero_nightid = int(re.findall(r'\d{8}', os.path.basename(filepath))[0])
        if zero_nightid <= night:
            print(f'Chose calibration file {filepath}')
            return filepath

    # Raise an exception if no suitable calibrations were found.
    raise RuntimeError(f'No suitable {name} file found for {night} in {calib_dir}.')


def get_calibrations(filepath, program):
    """Unpack calibration data for validating fluxes.
    
    Arguments:
        filepath : path to the calibration file being unpacked (str).
        program : name of the program used to run the exposure (str).
    Output:
        linewidths : pseudo-equivalent widths of lines for this exposure (dict).
    """
    with open(filepath, 'r') as json_file:
        calib_data = json.load(json_file)

    if program not in calib_data:
        raise ValueError(f'{program} data not found in {filepath}')

    return calib_data[program]

