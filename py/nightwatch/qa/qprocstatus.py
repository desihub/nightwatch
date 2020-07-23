from .base import QA
import glob
import os
import collections

import numpy as np
import fitsio
import json


from astropy.table import Table

class QAQPROCStatus(QA):
    """docstring for QANoiseCorr"""
    def __init__(self):
        self.output_type = "QPROC_STATUS"
    
    def valid_obstype(self, obstype):
        return True
    
    def run(self, indir):
        
        #get night, expid data
        header_file = glob.glob(os.path.join(indir, 'preproc-*.fits'))[0]
        hdr = fitsio.read_header(header_file, 'IMAGE')
        night = hdr['NIGHT']
        expid = hdr['EXPID']
        
        #get errorcodes
        jsonfile = glob.glob(os.path.join(indir, 'errorcodes-*.txt'))[0]
        with open(jsonfile, 'r') as json_file:
            errorcodes = json.load(json_file)
        
        #get qproc status data
        infiles = glob.glob(os.path.join(indir, 'qproc-*.log'))
        results = []
        
        for infile in infiles:
            dico = dict()
            
            filename = os.path.basename(infile)
            qexit = errorcodes[filename]
            spectro = int(filename[7])
            cam = filename[6].upper()
            
            dico['NIGHT'] = night
            dico['EXPID'] = expid
            dico['SPECTRO'] = spectro
            dico['CAM'] = cam
            dico['QPROC_EXIT'] = qexit
            
            results.append(collections.OrderedDict(**dico))
            
        return Table(results, names=results[0].keys())
        