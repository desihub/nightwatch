from .base import QA
import glob
import os
import collections

import numpy as np
import fitsio

from astropy.table import Table

import desiutil.log


class QATraceShift(QA):
    """docstring"""
    def __init__(self):
        self.output_type = "PER_CAM"
        pass
        
    def valid_flavor(self, flavor):
        # trace shift measured for all exposure except zero and dark
        return (flavor.upper() != "ZERO") and (flavor.upper() != "DARK")

    def run(self, indir):
        '''TODO: document'''
        log = desiutil.log.get_logger()
        infiles = glob.glob(os.path.join(indir, 'psf-*.fits'))
        results = list()
        for filename in infiles:
            log.debug(filename)
            hdr = fitsio.read_header(filename)
            night = hdr['NIGHT']
            expid = hdr['EXPID']
            cam = hdr['CAMERA'][0].upper()
            spectro = int(hdr['CAMERA'][1])
            dico={"NIGHT":night,"EXPID":expid,"SPECTRO":spectro,"CAM":cam}
            for k in ["MEANDX","MINDX","MAXDX","MEANDY","MINDX","MAXDX"] :
                dico[k]=hdr[k]
            log.debug("{} {} {} {}".format(night,expid,cam,spectro))
            results.append(collections.OrderedDict(**dico))
        return Table(results, names=results[0].keys())

            
            
        
