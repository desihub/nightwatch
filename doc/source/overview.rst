.. _overview:

Overview
========

Nightwatch is a program designed to provide realtime DESI data quality monitoring. The software runs at KPNO and NERSC and splits its work into three steps:

#. Process exposure data as they are recorded on disk.

#. Compute quality assurance (QA) metrics for the data.

#. Generate plots and HTML pages to display the QA results for monitoring by DESI observers.

These steps can be run individually on a single exposure or in an automated
mode that monitors a directory for new input data. In automated mode,
Nightwatch will run all the necessary steps on the latest exposures before
returning to look for additional new data.

Nighwatch Help
--------------

The Nightwatch program is a front-end for a variety of difference tasks related
to exposure processing, QA generation, and plot and table generation. These are
broken out so that each one can be run and tested separately if need be.

To see the list of available subcommands, run

```
nightwatch --help
```

for an overview of all available commands. To get detailed help on individual
commands, run

```
nightwatch <command> --help
```
