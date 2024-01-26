"""
Placeholder code for the concept of raising warnings and errors on metrics
"""
import os
import re
import json
import numpy as np

from astropy.table import Table

from .base import QA
from ..thresholds import pick_threshold_file
from ..calibrations import pick_calib_file, get_calibrations

import enum


class Status(enum.IntEnum):
    ok = 0
    warning = 1
    error = 2


def get_status(qadata, night):
    '''
    Placeholder for determining status of input qadata.
    Currently hardcoded; need to move to config file(s).

    TODO: document
    
    qadata[qatype] = Table(NIGHT, EXPID, ... METRIC1, METRIC2, ...)
    
    status[qatype] = Table(NIGHT, EXPID, ... QASTATUS, METRIC1, METRIC2, ...)
    '''
    
    #- mirror input structure with everything ok
    status = dict()
    for qatype, data in qadata.items():
        if not qatype.startswith('PER_'):
            continue

        n = len(data)
        status[qatype] = Table()
        for col in data.dtype.names:
            if col in QA.metacols[qatype]:
                status[qatype][col] = data[col]
            else:
                status[qatype][col] = np.full(n, Status.ok, dtype=np.int16)

    #- QA header.
    header = qadata['HEADER']

    #- Amp QA: check if readnoise, bias, or cosmics rate too low or high
    data = qadata['PER_AMP']
    exptime = header['EXPTIME']
    for metric in ['READNOISE', 'BIAS', 'COSMICS_RATE']:
        filepath = pick_threshold_file(metric, night, exptime=exptime)
        with open(filepath, 'r') as json_file:
            thresholds = json.load(json_file)
        for cam in ['B', 'R', 'Z']:
            for spec in range(0, 10):
                for amp in ['A', 'B', 'C', 'D']:
                    if metric == 'READNOISE' or metric == 'BIAS':
                        key = cam+str(spec)+amp
                    if metric == 'COSMICS_RATE':
                        key = cam
                    status_loc = (status['PER_AMP']['AMP'] == amp) & (status['PER_AMP']['SPECTRO']==spec) & (status['PER_AMP']['CAM']==cam)
                    data_loc = (data['AMP'] == amp) & (data['SPECTRO']==spec) & (data['CAM']==cam)
                    if thresholds[key]['lower'] != None and thresholds[key]['upper'] != None:
                        warn = (data[data_loc][metric] < thresholds[key]['lower']) | (data[data_loc][metric] > thresholds[key]['upper'])
                        error = (data[data_loc][metric] <= thresholds[key]['lower_err']) | (data[data_loc][metric] >= thresholds[key]['upper_err'])
                        if warn: 
                            status['PER_AMP'][metric][status_loc] = Status.warning
                        if error:
                            status['PER_AMP'][metric][status_loc] = Status.error
                    else:
                        continue
    
    #- Camera QA: check the traceshifts (wavelength and fiber fits).
    for metric in ['DX', 'DY']:
        try:
            cam_data = qadata['PER_CAMERA']
        except:
            continue
        filepath = pick_threshold_file(metric, night)
        with open(filepath, 'r') as json_file:
            thresholds = json.load(json_file)
        for cam in 'BRZ':
            for spec in range(0, 10):
                key = cam
                status_loc = (status['PER_CAMERA']['CAM'] == cam) & (status['PER_CAMERA']['SPECTRO']==spec)
                data_loc = (cam_data['CAM'] == cam) & (cam_data['SPECTRO']==spec)
                if thresholds[key]['lower'] != None and thresholds[key]['upper'] != None:
                    warn_mean = (abs(cam_data[data_loc]['MEAN'+metric]) >= abs(thresholds[key]['lower'])) | (abs(cam_data[data_loc]['MEAN'+metric]) >= abs(thresholds[key]['upper'])) 
                    error_mean = (abs(cam_data[data_loc]['MEAN'+metric]) >= (abs(thresholds[key]['lower_err']))) | (abs(cam_data[data_loc]['MEAN'+metric]) >= abs(thresholds[key]['upper_err']))
                    if warn_mean: 
                        status['PER_CAMERA']['MEAN'+metric][status_loc] = Status.warning
                    if error_mean:
                        status['PER_CAMERA']['MEAN'+metric][status_loc] = Status.error
                else:
                    continue
    
    # Camera QA: PSFs
    for metric in ['XSIG', 'YSIG']:
        try:
            cam_data = qadata['PER_CAMERA']
        except:
            continue
        filepath = pick_threshold_file(metric, night)
        with open(filepath, 'r') as json_file:
            thresholds = json.load(json_file)
        for cam in [b'B', b'R', b'Z']:
            for spec in range(0, 10):
                key = cam.decode('utf-8')
                status_loc = (status['PER_CAMERA']['CAM'] == cam) & (status['PER_CAMERA']['SPECTRO']==spec)
                data_loc = (cam_data['CAM'] == cam) & (cam_data['SPECTRO']==spec)
                try:
                    if thresholds[key]['lower'] != None and thresholds[key]['upper'] != None:
                        warn_mean = (abs(cam_data[data_loc]['MEAN'+metric]) >= abs(thresholds[key]['lower'])) | (abs(cam_data[data_loc]['MEAN'+metric]) >= abs(thresholds[key]['upper'])) 
                        error_mean = (abs(cam_data[data_loc]['MEAN'+metric]) >= (abs(thresholds[key]['lower'])+abs(thresholds[key]['lower_err']))) | (abs(cam_data[data_loc]['MEAN'+metric]) >= (abs(thresholds[key]['upper'])+abs(thresholds[key]['upper_err'])))
                        if warn_mean: 
                            status['PER_CAMERA']['MEAN'+metric][status_loc] = Status.warning
                        if error_mean:
                            status['PER_CAMERA']['MEAN'+metric][status_loc] = Status.error
                    else:
                        continue
                except ValueError:
                    continue

    # Spectro QA: check to see if calibrations match standard levels.
    if 'PER_SPECTRO' in qadata:
        try:
            sp_data = qadata['PER_SPECTRO']
            program = sp_data['PROGRAM'][0]

            # Handle flat calibrations.
            if 'LED' in program:
                spectrographs = sp_data['SPECTRO']

                filepath = pick_calib_file('CALIB-FLATS', night)
                calstandards = get_calibrations(filepath, program)

                for cam in 'BRZ':
                    fluxname = f'{cam}_INTEG_FLUX'

                    for sp in spectrographs:
                        select = sp_data['SPECTRO'] == sp
                        j = np.argwhere(select).flatten()[0]

                        spcam = f'{cam}{sp}'
                        cals = calstandards[spcam]

                        # Check integrated flux. Negative means no data; skip.
                        integ_flux = sp_data[fluxname][j]
                        if integ_flux < 0:
                            continue

                        # Apply temperature correction to flux.
                        T = header['TAIRTEMP']
                        b = cals['tempfit']['slope']
                        Tmed = cals['tempfit']['Tmedian']
                        integ_flux = integ_flux - b*(T - Tmed)

                        # Compare line area to cal standard warning/err ranges.
                        upper_err = cals['refs']['upper_err']
                        upper_warn = cals['refs']['upper']
                        nominal = cals['refs']['nominal']
                        lower_warn = cals['refs']['lower']
                        lower_err = cals['refs']['lower_err']

                        warn_integ_flux = (integ_flux > lower_err and integ_flux <= lower_warn) or (integ_flux < upper_err and integ_flux >= upper_warn)
                        err_integ_flux  = (integ_flux < lower_err) | (integ_flux > upper_err)

                        if warn_integ_flux:
                            status['PER_SPECTRO'][fluxname][j] = Status.warning

                        if err_integ_flux:
                            status['PER_SPECTRO'][fluxname][j] = Status.error

            # Handle arc calibrations.
            if 'Arcs' in program:
                spectrographs = sp_data['SPECTRO']
                arcnames = [n for n in sp_data.dtype.names if re.match('[BRZ][0-9]{4}', n)]

                filepath = pick_calib_file('CALIB-ARCS', night)
                calstandards = get_calibrations(filepath, program)
                calwaves = calstandards['wavelength']

                for arcname in arcnames:
                    cam = arcname[0]
                    wave = int(arcname[1:])
                    camwaves = np.asarray(calwaves[cam])
                    iwave = np.argmin(np.abs(camwaves - wave))

                    for j, sp in enumerate(spectrographs):
                        cals = calstandards['area']['spectrograph'][f'{sp}'][cam]
                        # Check line area. Negative area means no data; skip.
                        area = sp_data[arcname][j]
                        if area < 0:
                            continue

                        # Compare line area to cal standard warning/err ranges.
                        upper_err = cals['upper_err'][iwave]
                        upper_warn = cals['upper'][iwave]
                        nominal = cals['nominal'][iwave]
                        lower_warn = cals['lower'][iwave]
                        lower_err = cals['lower_err'][iwave]

                        warn_area = (area > lower_err and area <= lower_warn) or (area < upper_err and area >= upper_warn)
                        err_area  = (area < lower_err) | (area > upper_err)

                        if warn_area:
                            status['PER_SPECTRO'][arcname][j] = Status.warning

                        if err_area:
                            status['PER_SPECTRO'][arcname][j] = Status.error
        except Exception as err:
            print(err)

    #- Update global QASTATUS for all QA types
    for qatype, data in status.items():
        n = len(data)
        data['QASTATUS'] = np.full(n, Status.ok, dtype=np.int16)
        warnvec = np.full(n, Status.warning, dtype=np.int16)
        errvec = np.full(n, Status.error, dtype=np.int16)
        for colname in data.dtype.names:
            if colname in QA.metacols[qatype]:
                continue

            metric_status = data[colname]
            if np.any(metric_status):                    
                status[qatype]['QASTATUS'] = np.maximum(metric_status, status[qatype]['QASTATUS'])
    
    return status
