# calculates nominal read noise for zero and dark
# outputs FITS with all fields to [outdir]

import fitsio
import numpy as np
import os

nwdir = "/global/cfs/cdirs/desi/spectro/nightwatch/nersc"
zerodirs = ["20210107/00071175","20210108/00071353", "20210109/00071521", "20210110/00071664", "20210111/00071802"] #"20210106/00071024",
outdir = "" # "../"

# make darkdirs
darkdirs = []
for zerodir in zerodirs:
    fulldir = os.path.join(nwdir, zerodir)
    expid = os.path.basename(fulldir)
    night = os.path.basename(os.path.dirname(fulldir))
    
    darkdir = os.path.join(night, '{:08d}'.format(int(expid)+2))
    darkdirs.append(darkdir)

# create filepaths
zeroqafiles = []
for zerodir in zerodirs:
    fulldir = os.path.join(nwdir, zerodir)
    expid = os.path.basename(fulldir)
    night = os.path.basename(os.path.dirname(fulldir))
    
    qafile = os.path.join(fulldir, 'qa-{:08d}.fits'.format(int(expid)))
    zeroqafiles.append(qafile)

darkqafiles = []
for darkdir in darkdirs:
    fulldir = os.path.join(nwdir, darkdir)
    expid = os.path.basename(fulldir)
    night = os.path.basename(os.path.dirname(fulldir))
    
    qafile = os.path.join(fulldir, 'qa-{:08d}.fits'.format(int(expid)))
    darkqafiles.append(qafile)

# extract and sort amp files 
zeroamps = []
zeroamps_rn = []
for qafile in zeroqafiles:
    data = fitsio.FITS(qafile)
    amp = data["PER_AMP"].read()
    amp.sort(order=["CAM", "SPECTRO", "AMP"]) # https://numpy.org/doc/stable/reference/generated/numpy.recarray.sort.html
    zeroamps.append(amp)
    zeroamps_rn.append(amp["READNOISE"])
    
darkamps = []
darkamps_rn = []
for qafile in darkqafiles:
    data = fitsio.FITS(qafile)
    amp = data["PER_AMP"].read()
    amp.sort(order=["CAM", "SPECTRO", "AMP"]) # https://numpy.org/doc/stable/reference/generated/numpy.recarray.sort.html
    darkamps.append(amp)
    darkamps_rn.append(amp["READNOISE"])
    
# combbined rnnoms
nrows = 10*3*4
rnnoms = np.empty(nrows, dtype=[('CAM', 'U1'), ('SPECTRO', '>i8'), ('AMP', 'U1'),
                                ('READNOISE_NOM_ZERO','>f8'), ('READNOISE_MIN_ZERO','>f8'), ('READNOISE_STD_ZERO','>f8'), ('READNOISE_WARNING_ZERO','>i8'),
                                ('READNOISE_NOM_DARK','>f8'), ('READNOISE_MIN_DARK','>f8'), ('READNOISE_STD_DARK','>f8'), ('READNOISE_WARNING_DARK','>i8')])
rnnoms['READNOISE_NOM_ZERO'] = np.median(zeroamps_rn, axis=0)
rnnoms['READNOISE_MIN_ZERO'] = np.amin(zeroamps_rn, axis=0)
rnnoms['READNOISE_STD_ZERO'] = np.std(zeroamps_rn, axis=0)
rnnoms['READNOISE_WARNING_ZERO'] = np.ones(nrows)*(-1) # default to -1
rnnoms['READNOISE_NOM_DARK'] = np.median(darkamps_rn, axis=0)
rnnoms['READNOISE_MIN_DARK'] = np.amin(darkamps_rn, axis=0)
rnnoms['READNOISE_STD_DARK'] = np.std(darkamps_rn, axis=0)
rnnoms['READNOISE_WARNING_DARK'] = np.ones(nrows)

rnnoms['CAM'] = amp['CAM'] # using a random amp to get sorted order
rnnoms['SPECTRO'] = amp['SPECTRO']
rnnoms['AMP'] = amp['AMP']

fitsio.write(os.path.join(outdir, "rnnoms.fits"), rnnoms)