from .base import QA
import glob
import os
import collections

import numpy as np
import fitsio

from astropy.table import Table

import desiutil.log


class QAPSF(QA):
    """docstring"""
    def __init__(self):
        self.output_type = "PER_CAMERA"
        pass
        
    def valid_flavor(self, flavor):
        return flavor.upper() == "ARC"

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
            
            xsig = fitsio.read(filename,"XSIG")
            ysig = fitsio.read(filename,"XSIG")
            dico["MEANXSIG"]=np.mean(xsig[:,0])
            dico["MINXSIG"]=np.min(xsig[:,0]) 
            dico["MAXXSIG"]=np.max(xsig[:,0])
            dico["MEANYSIG"]=np.mean(ysig[:,0])
            dico["MINYSIG"]=np.min(ysig[:,0]) 
            dico["MAXYSIG"]=np.max(ysig[:,0])
            log.debug("{} {} {} {} mean xsig={:3.2f} ysig={:3.2f}".format(night,expid,cam,spectro,dico["MEANXSIG"],dico["MEANYSIG"]))
            results.append(collections.OrderedDict(**dico))
        return Table(results, names=results[0].keys())

            
            
        
