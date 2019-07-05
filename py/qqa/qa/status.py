"""
Placeholder code for the concept of raising warnings and errors on metrics
"""

import numpy as np
import json

from astropy.table import Table

from .base import QA
from ..thresholds import pick_threshold_file

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
    #- Set thresholds for readnoise suspiciously low or high
    data = qadata['PER_AMP']
    for metric in ['READNOISE', 'BIAS']:
        filepath = pick_threshold_file(metric, night)
        with open(filepath, 'r') as json_file:
            thresholds = json.load(json_file)
        for cam in [b'B', b'R', b'Z']:
            for spec in range(0, 10):
                for amp in [b'A', b'B', b'C', b'D']:
                    key = cam.decode('utf-8')+str(spec)+amp.decode('utf-8')
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
    
    for metric in ['COSMICS_RATE']:
        filepath = pick_threshold_file(metric, night)
        with open(filepath, 'r') as json_file:
            thresholds = json.load(json_file)
        key = cam.decode('utf-8')+str(spec)+amp.decode('utf-8')
        if thresholds['lower'] != None and thresholds['upper'] != None:
            warn = (data[metric] < thresholds['lower']) | (data[metric] > thresholds['upper'])
            error = (data[metric] < thresholds['lower_err']) | (data[metric] > thresholds['upper_err']) 
            status['PER_AMP'][metric][warn] = Status.warning
            status['PER_AMP'][metric][error] = Status.error
        else:
            continue
    
    #- TODO: add more threshold checks here
    
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