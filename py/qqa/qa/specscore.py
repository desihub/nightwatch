from .base import QA
import glob
import os
import collections

import numpy as np
import fitsio

from astropy.table import Table

import desiutil.log
from desispec.qproc.io import read_qframe
from desispec.specscore import compute_frame_scores

class QASpecscore(QA):
    """docstring for QASpecscore"""
    def __init__(self):
        self.output_type = "PER_CAMFIBER"
        pass

    def valid_flavor(self, flavor):
        '''PER_AMP QA metrics work for all qframe files'''
        return (flavor.upper() in ["ARC", "FLAT", "SCIENCE"])

    def run(self, indir):
        '''TODO: document'''

        log = desiutil.log.get_logger()

        results = list()

        infiles = glob.glob(os.path.join(indir, 'qframe-*.fits'))
        for filename in infiles:
            qframe = read_qframe(filename)
            night = int(qframe.meta['NIGHT'])
            expid = int(qframe.meta['EXPID'])
            cam = qframe.meta['CAMERA'][0].upper()
            spectro = int(qframe.meta['CAMERA'][1])

            log.debug("computing scores for {} {} {} {}".format(night,expid,cam,spectro))

            scores,comments = compute_frame_scores(qframe,suffix="RAW",flux_per_angstrom=True)
            
            has_calib_frame = False
            cfilename=filename.replace("qframe","qcframe")
            if os.path.isfile(cfilename) : # add scores of calibrated sky-subtracted frame
                qcframe = read_qframe(cfilename)
                cscores,comments = compute_frame_scores(qcframe,suffix="CALIB",flux_per_angstrom=True)
                for k in cscores.keys() :
                    scores[k] = cscores[k]
                has_calib_frame = True

            nfibers=scores['INTEG_RAW_FLUX_'+cam].size
            for f in range(nfibers) :
                fiber = int(qframe.fibermap["FIBER"][f])
                if has_calib_frame :
                    results.append(collections.OrderedDict(
                        NIGHT=night, EXPID=expid, SPECTRO=spectro, CAM=cam, FIBER=fiber,
                        INTEG_RAW_FLUX=scores['INTEG_RAW_FLUX_'+cam][f],
                        MEDIAN_RAW_FLUX=scores['MEDIAN_RAW_FLUX_'+cam][f],
                        MEDIAN_RAW_SNR=scores['MEDIAN_RAW_SNR_'+cam][f],
                        INTEG_CALIB_FLUX=scores['INTEG_CALIB_FLUX_'+cam][f],
                        MEDIAN_CALIB_FLUX=scores['MEDIAN_CALIB_FLUX_'+cam][f],
                        MEDIAN_CALIB_SNR=scores['MEDIAN_CALIB_SNR_'+cam][f]))
                else :
                    results.append(collections.OrderedDict(
                        NIGHT=night, EXPID=expid, SPECTRO=spectro, CAM=cam, FIBER=fiber,
                        INTEG_RAW_FLUX=scores['INTEG_RAW_FLUX_'+cam][f],
                        MEDIAN_RAW_FLUX=scores['MEDIAN_RAW_FLUX_'+cam][f],
                        MEDIAN_RAW_SNR=scores['MEDIAN_RAW_SNR_'+cam][f]))
        return Table(results, names=results[0].keys())
