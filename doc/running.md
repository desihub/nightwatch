# Running Nightwatch

Nightwatch performs 3 steps:
  * running qproc to process the raw data into preprocessed images and spectra
  * QA analysis of those processed data
  * generating plots to visualize the QA results
  
These steps can be run individually on a single exposure, or in automated
mode nightwatch will monitor a directory for new input data and run the necessary
steps before going back to watching for additional new data.

Run `nightwatch --help` for an overview, or `nightwatch <command> --help`
for help on individual commands.

## Automated Nightwatch

To run nightwatch in automated mode:
```
nightwatch monitor --indir INDIR --outdir OUTDIR
```
This will monitor INDIR/YEARMMDD/EXPID/ for new raw data, and when it appears
monitor will run qproc, qa, and make plots, outputting them to
OUTDIR/YEARMMDD/EXPID/

## Processing a single exposure

To process a single exposure (qproc, qa, plots):
```
nightwatch run --infile RAWDATAFILE --outdir QPROCDIR
```

## Running individual steps

For debugging and development, it can also be convenient to run individual
steps for individual exposures without having to run all the other steps:

```
nightwatch qproc --infile RAWDATAFILE --outdir QPROCDIR
nightwatch qa --indir QPROCDIR --outdir QADIR
nightwatch plot --indir QADIR --outdir QAPLOTDIR
```



