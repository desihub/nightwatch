from .base import QA
import glob
import os
import collections

import numpy as np
import fitsio

from astropy.table import Table
from astropy import units

import desiutil.log
from desispec.qproc.io import read_qframe
from desispec.calibfinder import CalibFinder
from desispec.interpolation import resample_flux
from desispec.io.filters import load_filter

from desitarget import targets


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

        

        filters = None

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
                    night = int(qframe.meta['NIGHT'])
                    expid = int(qframe.meta['EXPID'])
                    
                    if filters is None : # load filters
                        filters = dict()
                        
                        if 'S' in fmap['PHOTSYS']:
                            for b in ["G","R","Z"] :
                                filters[b] = load_filter("DECAM_"+b)
                                
                        if 'N' in fmap['PHOTSYS']:
                            for b in ["G","R","Z"] :
                                filters[b] = load_filter("BASS_"+b)

                        if len(filters) == 0:
                            raise ValueError("No filters loaded; neither 'N' nor 'S' in PHOTSYS?")
                        
                        min_filter_wave = 100000
                        max_filter_wave = 0
                        for k in filters.keys() :
                            min_filter_wave = min(min_filter_wave,np.min(filters[k].wavelength))-0.1
                            max_filter_wave = max(max_filter_wave,np.max(filters[k].wavelength))+0.1
                        log.debug("min max wavelength for filters= {:d} , {:d}".format(int(min_filter_wave),int(max_filter_wave)))
                        rwave=np.linspace(min_filter_wave,max_filter_wave,int(max_filter_wave-min_filter_wave))
                   

            # need to decode fibermap
            columns , masks, survey = targets.main_cmx_or_sv(fmap)
            print("columns=",columns)
            print("masks=",masks)
            print("survey=",survey)
            desi_target = fmap[columns[0]]  # (SV1_)DESI_TARGET
            desi_mask   = masks[0]                 # (sv1) desi_mask
            
            stars = (desi_target & desi_mask.mask('STD_WD|STD_FAINT|STD_BRIGHT')) != 0
            qsos  = (desi_target & desi_mask.QSO) != 0
            
            for f,fiber in enumerate(fmap["FIBER"]) :
                
                dico={"NIGHT":night,"EXPID":expid,"SPECTRO":spectro,"FIBER":fiber}
                for k in ["FLUX_G","FLUX_R","FLUX_Z"] :
                    dico[k]=fmap[k][f]
                
                sw  = np.zeros(rwave.size)
                swf = np.zeros(rwave.size)
                
                for c in ["B","R","Z"] :
                    
                    if c in qframes :
                        qframe=qframes[c]
                        dico["SNR_"+c] = np.median(qframe.flux[f] * np.sqrt(qframe.ivar[f]))
                        cf , cw = resample_flux(rwave,qframe.wave[f],qframe.flux[f],qframe.ivar[f])
                        sw  += cw
                        swf += cw*cf
                    else :
                        dico["SNR_"+c] = 0.
                
                rflux = swf/(sw+(sw==0))
                # interpolate over masked pixels
                rflux[sw==0] = np.interp(rwave[sw==0],rwave[sw>0],rflux[sw>0],left=0,right=0)

                fluxunits = 1e-17 * units.erg / units.s / units.cm**2 / units.Angstrom
                for c in ["G","R","Z"] :
                    dico["SPECFLUX_"+c]=filters[c].get_ab_maggies(rflux*fluxunits,rwave)*1e9 # nano maggies 


                dico["MORPHTYPE"] = fmap["MORPHTYPE"][f]
                if fmap["OBJTYPE"][f] == "SKY" :
                    dico["MORPHTYPE"] = b"SKY"
                elif dico["MORPHTYPE"] == "" : # not filled in some sims
                    if stars[f] or qsos[f] :
                        dico["MORPHTYPE"] = b"PSF"
                    else :
                        dico["MORPHTYPE"] = b"OTHER"
                
                results.append(collections.OrderedDict(**dico))
            

        if len(results)==0 :
            return None
        return Table(results, names=results[0].keys())
