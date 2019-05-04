"""
Placeholder code for the concept of raising warnings and errors on metrics
"""

import numpy as np

from astropy.table import Table

from .base import QA

import enum
class Status(enum.IntEnum):
    ok = 0
    warning = 1
    error = 2

def get_status(qadata):
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
    warn = (data['READNOISE'] < 1.5) | (data['READNOISE'] > 4)
    error = (data['READNOISE'] < 1) | (data['READNOISE'] > 5)
    status['PER_AMP']['READNOISE'][warn] = Status.warning
    status['PER_AMP']['READNOISE'][error] = Status.error
    
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