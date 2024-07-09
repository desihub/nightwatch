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

import desiutil.log

from .. import io


from ..qa.history import SQLiteSummaryDB
from ..plots.historyqa import plot_camera_timeseries, plot_ccd_timeseries, plot_flats_timeseries, plot_arcs_timeseries


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


def write_camera_qa(infile, outdir):
    """Write camera traceshift plots to HTML.

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
    data = db.get_camera_qadata()

    #- Loop over spectrographs.
    for spec in np.arange(10):
        outfile = os.path.join(outdir, f'history-camera-sp{spec}.html')

        select = data['spec'] == spec
        fig = plot_camera_timeseries(data[select], spec)

        html_components = dict(
            bokeh_version=bokeh.__version__, 
            spectrograph=spec,
            qatype='history'
        )

        script, div = components(fig)
        html_components['CAMERA'] = dict(script=script, div=div)

        html = template.render(**html_components)
        tmpfile = outfile + '.tmp' + str(os.getpid())
        with open(tmpfile, 'w') as fx:
            fx.write(html)

        os.rename(tmpfile, outfile)
        log.info(f'Wrote {outfile}')


def write_ccd_qa(infile, outdir):
    """Write CCD readnoise, bias, and cosmic rate plots to HTML.

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
    data = db.get_ccd_qadata()

    #- Loop over cameras.
    for cam in 'brz':
        #- Loop over spectrographs.
        for spec in np.arange(10):
            outfile = os.path.join(outdir, f'history-ccd-{cam}{spec}.html')

            select = (data['cam'] == cam.upper()) & (data['spec'] == spec)
            fig = plot_ccd_timeseries(data[select], cam, spec)

            html_components = dict(
                bokeh_version=bokeh.__version__, 
                camera=cam.upper(), spectrograph=spec,
                qatype='history'
            )

            script, div = components(fig)
            html_components['CCD'] = dict(script=script, div=div)

            html = template.render(**html_components)
            tmpfile = outfile + '.tmp' + str(os.getpid())
            with open(tmpfile, 'w') as fx:
                fx.write(html)

            os.rename(tmpfile, outfile)
            log.info(f'Wrote {outfile}')


def write_flat_cals(infile, outdir):
    """Write flat-fielding LED history plots.

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

        data = db.get_cal_flats(program)
        fig = plot_flats_timeseries(data)

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


def write_arc_cals(infile, outdir):
    """Write arc lamp calibration history plots.

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

    #- Programs, lines, and lamps to loop over:
    proglines = [('CALIB long Arcs Cd+Xe', ['B4679', 'R6440', 'Z9048'], ['Cd', 'Cd', 'Xe']),
                 ('CALIB short Arcs all',  ['B4048', 'B4801', 'R6508', 'Z8192', 'Z8822'], ['Hg', 'Cd', 'Ne', 'Kr', 'Xe'])]

    for program, lines, lamps in proglines:
        obstype = 'ARC'
        arcid = 'long' if 'long' in program else 'short'
        outfile = os.path.join(outdir, f'history-arcs-{arcid}.html')

        data = db.get_cal_arcs(program=program, fields=lines)
        fig = plot_arcs_timeseries(data, lines, lamps)

        html_components = dict(
            bokeh_version=bokeh.__version__,
            obstype=obstype, program=program,
            qatype='history'
        )

        script, div = components(fig)
        html_components['ARCS'] = dict(script=script, div=div)

        html = template.render(**html_components)
        tmpfile = outfile + '.tmp' + str(os.getpid())
        with open(tmpfile, 'w') as fx:
            fx.write(html)

        os.rename(tmpfile, outfile)
        log.info(f'Wrote {outfile}')

