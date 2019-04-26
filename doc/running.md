# Running Quick QA (qqa)

Quick QA performs 3 steps:
  * running qproc to process the raw data into preprocessed images and spectra
  * QA analysis of those processed data
  * generating plots to visualize the QA results
  
These steps can be run individually on a single exposure, or in automated
mode qqa will monitor a directory for new input data and run the necessary
steps before going back to watching for additional new data.

Run `qqa --help` for an overview, or `qqa <command> --help` for help on
individual commands.

## Automated Quick QA

To run qqa in automated mode:
```
qqa qqa run --indir INDIR --outdir OUTDIR
```
This will monitor INDIR/YEARMMDD/EXPID/ for new raw data, and when it appears
qqa will run qproc, qa, and make plots, outputting them to
OUTDIR/YEARMMDD/EXPID/

## Running individual steps

For debugging and development, it can also be convenient to run individual
steps for individual exposures:

```
qqa qproc --infile RAWDATAFILE --outdir QPROCDIR
qqa qa --indir QPROCDIR --outdir QADIR
qqa plot --indir QADIR --outdir QAPLOTDIR
```

Note: this is a work in progress and isn't fully working yet.



