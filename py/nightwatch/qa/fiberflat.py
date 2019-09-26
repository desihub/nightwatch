from .base import QA
import glob
import os
import collections

import numpy as np
import fitsio

from astropy.table import Table

import desiutil.log
from desispec.qproc.io import read_qframe
from desispec.io import read_fiberflat
from desispec.calibfinder import CalibFinder

class QAFiberflat(QA):
    """docstring """
    def __init__(self):
        self.output_type = "PER_CAMFIBER"
        pass

    def valid_flavor(self, flavor):
        return ( flavor.upper() == "FLAT" )

    def run(self, indir):
        '''TODO: document'''

        log = desiutil.log.get_logger()

        results = list()

        infiles = glob.glob(os.path.join(indir, 'qframe-*.fits'))
        if len(infiles) == 0 :
            log.error("no qframe in {}".format(indir))
            return None
    
        for filename in infiles:
            qframe = read_qframe(filename)
            night = int(qframe.meta['NIGHT'])
            expid = int(qframe.meta['EXPID'])
            cam = qframe.meta['CAMERA'][0].upper()
            spectro = int(qframe.meta['CAMERA'][1])

            try : 
                cfinder = CalibFinder([qframe.meta])
            except :
                log.error("failed to find calib for qframe {}".format(filename))
                continue
            if not cfinder.haskey("FIBERFLAT") :
                log.warning("no known fiberflat for qframe {}".format(filename))
                continue
            fflat = read_fiberflat(cfinder.findfile("FIBERFLAT"))
            tmp = np.median(fflat.fiberflat,axis=1)
            reference_fflat = tmp/np.median(tmp)
            
            tmp = np.median(qframe.flux,axis=1)
            this_fflat = tmp/np.median(tmp)

            for f,fiber in enumerate(qframe.fibermap["FIBER"]) :
                results.append(collections.OrderedDict(
                    NIGHT=night, EXPID=expid, SPECTRO=spectro, CAM=cam, FIBER=fiber,FIBERFLAT=this_fflat[f],REF_FIBERFLAT=reference_fflat[f]))

        if len(results)==0 :
            return None
        return Table(results, names=results[0].keys())
