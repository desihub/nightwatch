.. Nightwatch documentation master file, created by
   sphinx-quickstart on Sun Jan 21 11:00:56 2024.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Nightwatch!
======================

.. image:: img/nw-logo.png
  :alt: A logo of an eye with stars.
  :width: 200px
  :align: right

Nightwatch is a Python package that generates and displays realtime quality
assurance (QA) metrics for nightly DESI observing shifts. It calculates metrics
at the level of individual DESI fibers, CCD amplifiers, CCD cameras, and
spectrographs.

DESI Support Observing Scientists (SOs) use the QA from DESI shifts posted on
the `main Nightwatch website at NERSC
<https://nightwatch.desi.lbl.gov/nights.html>`_. Non-expert instructions and
example plots are posted to the `Nightwatch page
<https://desi.lbl.gov/trac/wiki/DESIOperations/NightWatch/NightWatchDescription>`_
on the DESI wiki.

The design of Nightwatch is based on experience and lessons learned from SDSS
SOS and prior work on the DESI QuickLook and QuickLook Framework. The initial
design was provided by Stephen Bailey and Julien Guy. Initial plot designs were
created by Ruhi Doshi, Ana Lyons, and William Sheu (UC Berkeley). Current
primary maintainers are Segev BenZvi and Jose Bermejo-Climent. The full list of
project contributors is `available here
<https://github.com/desihub/nightwatch/graphs/contributors>`_.

.. toctree::
   :maxdepth: 1
   :caption: Contents:

   overview.rst
   installation.rst
   running.rst
   experts.rst

Indices and tables
==================
* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
