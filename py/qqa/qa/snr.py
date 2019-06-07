from .base import QA
import glob
import os
import collections

import numpy as np
import fitsio

from astropy.table import Table

import desiutil.log
from desispec.qproc.io import read_qframe
from desispec.calibfinder import CalibFinder

class QASNR(QA):
    """docstring """
    def __init__(self):
        self.output_type = "PER_FIBER"
        pass

    def valid_flavor(self, flavor):
        return ( flavor.upper() == "SCIENCE" )

    def run(self, indir):
        '''TODO: document'''

        log = desiutil.log.get_logger()

        results = list()

        infiles = glob.glob(os.path.join(indir, 'qcframe-*.fits'))
        if len(infiles) == 0 :
            log.error("no qcframe in {}".format(indir))
            return None

        # find number of spectros
        spectros=[]
        for filename in infiles:
            hdr=fitsio.read_header(filename)
            s=int(hdr['CAMERA'][1])
            spectros.append(s)
        spectros=np.unique(spectros)
        
        for spectro in spectros :
            infiles = glob.glob(os.path.join(indir, 'qcframe-?{}-*.fits'.format(spectro)))
            qframes={}
            fmap=None
            for infile in infiles :
                qframe=read_qframe(infile)
                cam=qframe.meta["CAMERA"][0].upper()
                qframes[cam]=qframe
                if fmap is None :
                    fmap = qframe.fibermap
            print(fmap.dtype.names)
            
            for f,fiber in enumerate(fmap["FIBER"]) :
                print("hello")
                

            
            print("FINISH THIS")
            sys.exit(12)

            """
            for f,fiber in enumerate(qframe.fibermap["FIBER"]) :
                results.append(collections.OrderedDict(
                    NIGHT=night, EXPID=expid, SPECTRO=spectro, FIBER=fiber))
            """

        if len(results)==0 :
            return None
        return Table(results, names=results[0].keys())
