from .base import QA
import glob
import os
import collections

import numpy as np
import fitsio


from astropy.table import Table

import desiutil.log
from desispec.preproc import _overscan
from .amp import _fix_amp_names

def corr(img,d0=4,d1=4,nrand=50000) :
    """
    Computes the correlation function of an image.

    Args:
      img : 2D numpy array
      d0  : size of output correlation along axis 0
      d1  : size of output correlation along axis 1
      
    return correlation function as a 2D array of shape (d0,d1)
    """
    log = desiutil.log.get_logger()
    mean,rms = _overscan(img, nsigma=5, niter=3)
    tmp = (img-mean)/rms
    log.debug("mean={:3.2f} rms={:3.2f}".format(mean,rms))
    n0=tmp.shape[0]
    n1=tmp.shape[1]
    
    if nrand>=n0*n1 :
        ii0 = np.arange(n0-d0)
        ii1 = np.arange(n1-d1)
    else : # random subsampling to run faster
        ii0=np.random.choice(n0-d0,size=nrand)
        ii1=np.random.choice(n1-d1,size=nrand)
        
    corrimg = np.zeros((d0,d1))
    
    for i0 in range(d0) :
        for i1 in range(d1) :
            corrimg[i0,i1] = np.median(tmp[ii0,ii1]*tmp[ii0+i0,ii1+i1])
            #log.debug("corr[{},{}] = {:4.3f}".format(i0,i1,corrimg[i0,i1]))
    corrimg /= corrimg[0,0]
    return corrimg

class QANoiseCorr(QA):
    """docstring for QANoiseCorr"""
    def __init__(self):
        self.output_type = "PER_AMP"
        pass

    def valid_flavor(self, flavor):
        # can only reliably compute noise correlation with zero images
        return flavor.upper() == "ZERO"

    def run(self, indir):
        '''TODO: document'''
        log = desiutil.log.get_logger()
        infiles = glob.glob(os.path.join(indir, 'preproc-*.fits'))
        results = list()
        for filename in infiles:
            img,hdr = fitsio.read(filename, 'IMAGE',header=True) 
            _fix_amp_names(hdr)
            night = hdr['NIGHT']
            expid = hdr['EXPID']
            cam = hdr['CAMERA'][0].upper()
            spectro = int(hdr['CAMERA'][1])

            ny, nx = img.shape
            npix_amp = nx*ny//4
            for amp in ['A', 'B', 'C', 'D']:
                #- Subregion of mask covered by this amp
                if amp == 'A':
                    subimg  = img[0:ny//2, 0:nx//2].astype(float)
                elif amp == 'B':
                    subimg  = img[0:ny//2, nx//2:].astype(float)
                elif amp == 'C':
                    subimg  = img[ny//2:, 0:nx//2].astype(float)
                else:
                    subimg  = img[ny//2:, nx//2:].astype(float)
                
                n0=4
                n1=4
                corrimg = corr(subimg,n0,n1)

                dico={"NIGHT":night,"EXPID":expid,"SPECTRO":spectro,"CAM":cam,"AMP":amp}
                for i0 in range(n0) :
                    for i1 in range(n1) :
                        dico["CORR-{}-{}".format(i0,i1)]=corrimg[i0,i1]
                
                results.append(collections.OrderedDict(**dico))

        return Table(results, names=results[0].keys())

            
            
        
