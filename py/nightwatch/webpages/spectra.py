import os
import re
import numpy as np

import jinja2
from jinja2 import select_autoescape
import bokeh, sys
from bokeh.embed import components

from ..plots import spectra
from ..plots.spectra import plot_spectra_qa_arcs, plot_spectra_qa_flats
from ..calibrations import pick_calib_file, get_calibrations

from desiutil.log import get_logger


def write_spectra_html(outfile, qadata, header, nightdir):
    '''Write spectra QA webpage

    Args:
        outfile: output HTML filename
        qadata: exposure QA table
        header: dict-like data header with keys NIGHT, EXPID, PROGRAM
        nightdir: path to qproc outputs

    Returns:
        html_components dict with keys 'script', 'div' from bokeh
    '''
    
    log = get_logger() 
    night = header['NIGHT']
    expid = header['EXPID']
    if 'OBSTYPE' in header :
        obstype = header['OBSTYPE'].rstrip().upper()
    else :
        log.warning('Use FLAVOR instead of missing OBSTYPE')
        obstype = header['FLAVOR'].rstrip().upper()
    if 'PROGRAM' not in header :
        program = 'no program in header!'
    else :
        program = header['PROGRAM'].rstrip()
    exptime = header['EXPTIME']

    env = jinja2.Environment(
        loader=jinja2.PackageLoader('nightwatch.webpages', 'templates'),
        autoescape=select_autoescape(disabled_extensions=('txt',),
                                     default_for_string=True, 
                                     default=True)
    )
    
    template = env.get_template('spectro.html')

    html_components = dict(
        bokeh_version=bokeh.__version__, exptime='{:.1f}'.format(exptime),
        night=night, expid=expid, zexpid='{:08d}'.format(expid),
        obstype=obstype, program=program, qatype='spectro',
        num_dirs=2,
    )
    
    #- Plot random spectra.
    if obstype.upper() in ['ARC','FLAT','TESTARC','TESTFLAT','SCIENCE','SKY','TWILIGHT'] and \
            'PER_CAMFIBER' in qadata:
        downsample = 4
        nfib = min(5, len(qadata['PER_CAMFIBER']))
        fibers = sorted(np.random.choice(qadata['PER_CAMFIBER']['FIBER'], size=nfib, replace=False))
        fibers = ','.join([str(tmp) for tmp in fibers])

        frame = 'qcframe' if obstype.upper() == 'SCIENCE' else 'qframe'

        specfig = spectra.plot_spectra_input(nightdir, expid, frame,
                      downsample, fibers, height=400, width=1000)
        script, div = components(specfig)
        html_components['SPECTRA'] = dict(script=script, div=div, fibers=fibers)

    #- Plot calibration exposure QA: Arcs.
    if obstype.upper() == 'ARC' and 'PER_SPECTRO' in qadata:
        arclines = [n for n in qadata['PER_SPECTRO'].dtype.names \
                    if re.match('[BRZ][0-9]{4}', n)]

        calsfile = pick_calib_file('CALIB-ARCS', night)
        cals = get_calibrations(calsfile, program)

        arclinefig = spectra.plot_spectra_qa_arcs(qadata['PER_SPECTRO'], arclines, cals)

        script, div = components(arclinefig)
        html_components['CAL_ARCS'] = dict(script=script, div=div)

    #- Plot calibration exposure QA: Flats.
    if obstype.upper() == 'FLAT' and 'PER_SPECTRO' in qadata:
        calsfile = pick_calib_file('CALIB-FLATS', night)
        cals = get_calibrations(calsfile, program)

        flatsfig = spectra.plot_spectra_qa_flats(qadata['PER_SPECTRO'], cals)

        script, div = components(flatsfig)
        html_components['CAL_FLATS'] = dict(script=script, div=div)

    html = template.render(**html_components)

    #- Write HTML text to the output file
    with open(outfile, 'w') as fx:
        fx.write(html)

    return html_components


def get_spectra_html(data, night, expid, view, frame, downsample_str, select_string = None):
    '''
    Generates the html for the page conatining spectra plots. The format of
    the page depends on the provided view.

    Args:
        data: night directory that contains the expid we want to process.
        night : string or int of the night we want to process spectra.
        expid: string or int of the expid we want to process spectra.
        view: must be either "spectrograph", "objtype", "input".
            "spectrograph":
                generate 10 different plots corresponding to each spectrograph
            "objtype":
                generate different plots corresponding to each different objtype
            "input":
                generates different plots corresponding to the user's input
        frame: filename header to look for ("qframe" or "qcframe")
        downsample_str: string corresponding to downsample, e.g., "4x".
            if None, assumes "4x"

    Options:
        select_string: the user input only for when view = "input". If None,
            returns no spectra plot, but only inputboxes

    Returns html string that should display the spectra plots
    '''

    if view not in ["spectrograph", "objtype", "input"]:
        print("No such view " + view, file=sys.stderr)
        return "No such view " + view

    if frame not in ["qcframe", "qframe"]:
        print("No such frame " + str(frame), file=sys.stderr)
        frame = "qframe"

    env = jinja2.Environment(
        loader=jinja2.PackageLoader('nightwatch.webpages', 'templates'),
        autoescape=select_autoescape(disabled_extensions=('txt',),
                                     default_for_string=True, 
                                     default=True)
    )
    
    template = env.get_template('spectra.html')

    html_components = dict(
        bokeh_version=bokeh.__version__, night=night, expid=int(expid),
        zexpid='{:08d}'.format(expid), downsample=downsample_str, # spectra=True,
    )
    
    num_dirs = 6 #night/expid/spectra/view/.../frame/downsample-x
    add_dirs = len(select_string.split("/")) if select_string else 0
    html_components['num_dirs'] = num_dirs + add_dirs
    
    
    if downsample_str is None:
        downsample = 4
    else:
        if downsample_str[len(downsample_str)-1] != "x":
            return("invalid downsample")
        try:
            downsample = int(downsample_str[0:len(downsample_str)-1])
        except:
            return("invalid downsample")

    html_components["downsample"] = downsample
    html_components["view"] = view.capitalize()
    html_components["expid"] = str(expid).zfill(8)
    html_components["frame"] = frame

    #- Generate the bokeh figure
    if view == "spectrograph":
        fig = spectra.plot_spectra_spectro(data, expid, frame, downsample)
    elif view == "objtype":
        fig = spectra.plot_spectra_objtype(data, expid, frame, downsample)
    elif view == "input":
        html_components["input"] = True
        fig = None
        if select_string != None:
            select_string =select_string.replace(" ", "")
            html_components["select_str"] = select_string
            fig = spectra.plot_spectra_input(data, expid, frame, downsample, select_string)
            if fig is None:
                return "None selected"
        if fig:
            script, div = components(fig)
            #- Save those in a dictionary to use later
            html_components['spectra'] = dict(script=script, div=div)
        #- Combine template + components -> HTML
        html = template.render(**html_components)
        return html

    if fig:
        #- Convert that into the components to embed in the HTML
        script, div = components(fig)
        #- Save those in a dictionary to use later
        html_components['spectra'] = dict(script=script, div=div)
        #- Combine template + components -> HTML
        html = template.render(**html_components)
        return html

    else:
        return "no {}-*-{}.fits files found".format(frame, str(expid).zfill(8))
