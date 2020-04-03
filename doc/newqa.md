# Adding a new QA

Nightwatch is split into 3 steps:

  * processing data
  * performing QA on the results
  * making plots and html pages to display those QA results

## Adding a new processing step

Currently (April 2020) Nightwatch only processes spectroscopic data
using `desi_qproc`.  If you want to expand it to process non-spectroscopic
data, add the code to do that in `nightwatch.run` and then call it from
`nightwatch.script.main_run()` just after it calls `run.run_qproc`.

## Adding a new QA metric

To add a new QA metric, either extend the functionality of an existing
QA class in py/nightwatch/qa/, or add a new QA class using one of the existing
classes as an example.

QA classes are organized by what level of data or hardware they are testing:
PER_AMP, PER_CAMERA, PER_FIBER, PER_CAMFIBER, PER_SPECTRO, PER_EXP.  A single
QA class can generate multiple metrics for a given type of QA
(e.g. READ_NOISE and BIAS for PER_AMP), and multiple QA classes can implement
different metrics for the same type of QA.

New QA classes should:

  * subclass `nightwatch.qa.base.QA`
  * implement the variables/functions defined in `nightwatch.qa.base.QA`:
      * QA.output_type
      * QA.valid_flavor(self, flavor)
      * QA.run(self, indir)

The current QA classes are structured for spectroscopic data; it may be that
non-spectroscopic data should follow a different structure, but still follow
the basic split of differentiating processing data from making and saving QA
measurements of those data.

## Adding a new plot

Documentation WORK IN PROGRESS.

The intension is to provide a suite of standard plotting functions for each
type of QA (e.g. PER_AMP or PER_FIBER).  New metrics can re-use the same
plotting functions to add new plots to the HTML template.
See plots/amp.py for an example.

See `nightwatch.run.make_plots` for how these are called.

