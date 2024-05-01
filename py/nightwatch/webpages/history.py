"""
Pages summarizing QA history
"""

import os, json, re, time
from collections import OrderedDict, Counter

import numpy as np

import jinja2
from jinja2 import select_autoescape

import bokeh
from bokeh.embed import components

from astropy.table import Table
from astropy.time import Time

import desiutil.log

from .. import io


from ..qa.history import SQLiteSummaryDB
from ..plots.historyqa import plot_flats_timeseries


def write_history(outdir):
    """Write history plots.

    Args:
        outdir: location of output HTML files
    """
    log = desiutil.log.get_logger(level='INFO')

    #- Set up HTML template for output.
    env = jinja2.Environment(
        loader=jinja2.PackageLoader('nightwatch.webpages', 'templates'),
        autoescape=select_autoescape(disabled_extensions=('txt',),
                                     default_for_string=True, 
                                     default=True)
    )
    
    template = env.get_template('history.html')

    #- Update/create the index file.
    outfile = os.path.join(outdir, 'history.html')

    html_components = dict(
        bokeh_version=bokeh.__version__, 
        qatype='history',
        HISTORY_INDEX=True
    )
    html = template.render(**html_components)
    tmpfile = outfile + '.tmp' + str(os.getpid())
    with open(tmpfile, 'w') as fx:
        fx.write(html)
    log.info(f'Wrote {outfile}')
    os.rename(tmpfile, outfile)


def write_flat_cals(infile, outdir):
    """Write history plots.

    Args:
        infile: input SQLite file
        outdir: location of output HTML files
    """
    log = desiutil.log.get_logger(level='INFO')

    #- Set up HTML template for output.
    env = jinja2.Environment(
        loader=jinja2.PackageLoader('nightwatch.webpages', 'templates'),
        autoescape=select_autoescape(disabled_extensions=('txt',),
                                     default_for_string=True, 
                                     default=True)
    )
    
    template = env.get_template('history.html')

    #- Set up access to history DB.
    log.info(f'Access history data from {infile}')
    db = SQLiteSummaryDB(infile)

    #- Loop over calibration FLAT programs.
    for flatid in np.arange(4):
        obstype = 'FLAT'
        program = f'CALIB DESI-CALIB-{flatid:02d} LEDs only'
        outfile = os.path.join(outdir, f'history-flats-leds-{flatid:02d}.html')

        tab = db.get_cal_flats(program)

        fig = plot_flats_timeseries(tab)

        html_components = dict(
            bokeh_version=bokeh.__version__, 
            obstype=obstype, program=program,
            qatype='history'
        )

        script, div = components(fig)
        html_components['FLATS'] = dict(script=script, div=div)

        html = template.render(**html_components)
        tmpfile = outfile + '.tmp' + str(os.getpid())
        with open(tmpfile, 'w') as fx:
            fx.write(html)

        os.rename(tmpfile, outfile)
        log.info(f'Wrote {outfile}')

