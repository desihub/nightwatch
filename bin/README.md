# Testing Nightwatch at NERSC

## Download or Update Nightwatch

Get a recent version of Nightwatch from [desihub](https://github.com/desihub/nightwatch), either by cloning the
repository over https,
```
git clone https://github.com/desihub/nightwatch.git
```
or by updating a working copy:
```
cd nightwatch
git pull
```

## Set up a Test Area for Output

Nightwatch produces HTML output used by observers to check DESI exposures. Therefore, it's best to copy the output
to a location where you can open it in a web browser. The user areas in the global file system are the best
locations for this. Create the following directory:
```
mkdir -p /global/project/projectdirs/desi/username/nightwatch
```
where `username` is your NERSC username. When running nightwatch, you can save output to this folder and then
view it from the DESI web portal at NERSC:

https://data.desi.lbl.gov/desi/users/username/nightwatch/

Obviously, change "username" in the URL to your actual username.

## Running Nightwatch

To run Nightwatch, set up the user enviroment to use desiconda:
```
source /global/common/software/desi/desi_environment.sh master
```

Then manually set the PYTHONPATH to point to your local working copy of Nightwatch:
```
cd /path/to/nightwatch
export PYTHONPATH=`pwd`/py:$PYTHONPATH
```

### Nightwatch Executables

In the top of the local working copy of Nightwatch you will see the file `./bin/nightwatch`. This is your access
point to programs that Nightwatch can run. Instructions for running the programs are given using a builtin help
menu. For example,
```
./bin/nightwatch -h
```
will produce the help output:
```
USAGE: nightwatch <command> [options]

Supported commands are:
    monitor    Monitor input directory and run qproc, qa, and generate plots
    run        Run qproc, qa, and generate plots for a single exposure
    assemble_fibermap
               Run assemble_fibermap using data from input raw data file
    preproc    Run only preprocessing on an input raw data file
    preproc    Run only preprocessing on an input raw data file
    qproc      Run qproc (includes preproc) on an input raw data file
    qa         Run QA analysis on qproc outputs
    plot       Generate webpages with plots of QA output
    tables     Generate webpages with tables of nights and exposures
    webapp     Run a nightwatch Flask webapp server
    surveyqa   Generate surveyqa webpages
Run "nightwatch <command> --help" for details options about each command
```

### The Run Command

The `run` command in Nightwatch is responsible for running the `preproc` and `qproc` programs on raw DESI
exposures. It then runs the data quality assurance and produces HTML outputs. This is what you will run to
actually test changes to Nightwatch. Usage is:

```
$> ./bin/nightwatch run -h

usage: {prog} run [options]

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

The list of exposures processed by Nightwatch is avaiable [here](https://nightwatch.desi.lbl.gov/nights.html). To
test local changes, run a command line like the following:
```
./bin/nightwatch run -n YYYYMMDD -e ######### -o /global/project/projectdirs/desi/username/nightwatch
```
where
- YYYYMMDD is the date (e.g., 20220111).
- ######## is an exposure ID from that date (e.g., 118039).
- The output folder lives in your user area.

Navigate in your web browser to https://data.desi.lbl.gov/desi/users/username/nightwatch/ to inspect the output
plots once the run is complete.
