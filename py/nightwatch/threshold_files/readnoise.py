import fitsio
import numpy as np
import os
import numpy.lib.recfunctions as rfn

def append_nominal(amp, rnnoms):
    """Sort and append nominal read noise and flags to PER_AMP recarray
    Args:
        amp: input PER_AMP recarray
        rnnoms: FITS file of nominal noise and warning flags
    Returns:
        Sorted recarray with appended nominal columns (zero and dark)
    """
    amp.sort(order=["CAM", "SPECTRO", "AMP"])
    rnnoms_cleaned = rfn.drop_fields(rnnoms, drop_names=["CAM", "SPECTRO", "AMP"])
    scienceamp = rfn.merge_arrays((amp, rnnoms_cleaned), flatten=True)

    
    return mergedamp

def set_rnflag(amp, nominal="med"):
    """Set read noise warning flags for a PER_AMP recarray
    Args:
        amp: input PER_AMP recarray with nominal readnoises appended
        nominal: nominal readnoise using median ("med") or minimum ("min") of reference zeros/darks
    Returns:
        Recarray with flags READNOISE_WARNING_ZERO and READNOISE_WARNING_DARK set
    """
    rn = amp["READNOISE"]
    if nominal=="med":
        nom_zero = amp["READNOISE_NOM_ZERO"]
        nom_dark = amp["READNOISE_NOM_DARK"]
    elif nominal=="min":
        nom_zero = amp["READNOISE_MIN_ZERO"]
        nom_dark = amp["READNOISE_MIN_DARK"]
    else:
        return "ERROR"
    
    zerodiff = rn - nom_zero
    darkdiff = rn - nom_dark
    
    # flag set to
    # 1 if read noise is 0
    # 0 if diff from nominal <0.5 ADU
    # 2 if diff from nominal <1 ADU
    # 4 if diff from nominal >=1 ADU
    warnflaglist = [1, 0, 2]
    warnflagdefault = 4 # if read_noise not zero and diff from nominal >=1 ADU
    
    zerocondlist = [rn==0, np.abs(zerodiff)<0.5, np.abs(zerodiff) < 1]
    zerowarn = np.select(zerocondlist, warnflaglist, default=warnflagdefault)
    amp["READNOISE_WARNING_ZERO"] = zerowarn

    darkcondlist = [rn==0, np.abs(darkdiff)<0.5, np.abs(darkdiff) < 1]
    darkwarn = np.select(darkcondlist, warnflaglist, default=warnflagdefault)
    amp["READNOISE_WARNING_DARK"] = darkwarn
    
    return amp