# Adding a new QA

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

# Adding a new plot

WORK IN PROGRESS.

The intension is to provide a suite of standard plotting functions for each
type of QA (e.g. PER_AMP or PER_FIBER).  New metrics can re-use the same
plotting functions to add new plots to the HTML template.
See plots/amp.py for an example.