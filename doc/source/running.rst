.. _running:

Running Nightwatch
==================

Setting up the DESI software stack
----------------------------------

At NERSC or KPNO, you will need to set up the DESI software stack to run
Nightwatch. On NERSC, this is done by running the command

```
source /global/common/software/desi/desi_environment.sh
```

followed by

```
module load nightwatch/main
```

if you want to use the main installed version of Nightwatch set up for daily
processing. (Instructions are provided below on setting up a private working
copy of Nightwatch for testing.)

At KPNO, only expert users will be manually running Nightwatch. The easiest way
to access the installed software is to run the `gonightwatch` command defined
in the `datasytems` user account.

Accessing Nightwatch subcommands
--------------------------------

To list the available Nightwatch subcommands, run `nightwatch --help` for an
overview, or `nightwatch <command> --help` for help on individual commands.

For example, running `nightwatch --help` will produce the output

```
USAGE: nightwatch <command> [options]

Supported commands are:
    monitor    Monitor input directory and run qproc, qa, and generate plots
    run        Run qproc, qa, and generate plots for a single exposure
    assemble_fibermap
               Run assemble_fibermap using data from input raw data file
    preproc    Run only preprocessing on an input raw data file
    qproc      Run qproc (includes preproc) on an input raw data file
    qa         Run QA analysis on qproc outputs
    plot       Generate webpages with plots of QA output
    tables     Generate webpages with tables of nights and exposures
    webapp     Run a nightwatch Flask webapp server
    surveyqa   Generate surveyqa webpages
Run "nightwatch <command> --help" for details options about each command
```

The Nightwatch run command
--------------------------

The most commonly used command is the `nightwatch run` which goes through all
the steps of generating and plotting QA data. The `run` command will execute
the following subprocesses in order:

#. `assemble_fibermap`: generate the fibermap table with full pointing information for a given exposure.

#. `preproc`: preprocess CCD images and write the output to a FITS table.

#. `qproc`: run a boxcar extraction on CCD images to pull out fiber spectra (not run on `ZERO` or `DARK` exposures).

#. `qa`: generate quality assurance (QA) metrics for amplifier, camera, and spectrograph-level measurements.

#. `plot`: generate diagnostic plots and webpages using `bokeh <https://bokeh.org/>`_.

#. `tables`: generate summary tables for all exposures in a given night, reporting QA status for amplifier, camera, and spectrograph-level measurements.

To manually run the processing on a single exposure, the run command usage is

```
usage: nightwatch run [options]

optional arguments:
  -h, --help            show this help message and exit
  -i INFILE, --infile INFILE
                        input raw data file
  -o OUTDIR, --outdir OUTDIR
                        output base directory
  --cameras CAMERAS     comma separated list of cameras (for debugging)
  -n NIGHT, --night NIGHT
                        YEARMMDD night
  -e EXPID, --expid EXPID
                        Exposure ID
```

A list of available nights and exposure IDs is available `here
<https://nightwatch.desi.lbl.gov/nights.html>`_. An example of the calling
syntax is

```
nightwatch run -n YYYYMMDD -e NNNNNNNNN -o $SCRATCH/nightwatch
```

if you want to test Nightwatch output.
