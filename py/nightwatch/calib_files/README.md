# Calibration files 

This folder contains files defining standard fluxes for calibration exposures.

## CALIB-ARCS

The CALIB-ARCS*.json files contain pseudo-equivalent widths for prominent
spectral lines from the arc lamps. Standard pEW levels are defined for each
spectrograph.

To find the wavelengths of the most prominent lines, run the script

```
python find_arclines.py \
    -n YYYYMMDD
    -i /global/cfs/cdirs/desi/spectro/nightwatch/nersc
    -o arclines.json
```

To compute the pseudo-equivalent widths for a pre-determined list of spectral
lines, run the command

```
python calc_arclines.py \
    -n 20230104-ARCS.ini
    -o CALIB-ARCS-20230104.json
```

