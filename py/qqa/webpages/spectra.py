import numpy as np

import jinja2
import bokeh, sys
from bokeh.embed import components

from ..plots import spectra

def get_spectra_html(data, expid, view, frame, downsample_str, select_string = None):
    '''
    Generates the html for the page conatining spectra plots. The format of
    the page depends on the provided view.

    Args:
        data: night directory that contains the expid we want to process spectra for
        expid: string or int of the expid we want to process spectra for
        view: must be either "spectrograph", "objtype", "input".
            "spectrograph":
                generates 10 different plots corresponding to each spectrograph
            "objtype":
                generates different plots corresponding to each different objtype
            "input":
                generates different plots corresponding to the user's input
        frame: filename header to look for ("qframe" or "qcframe")
        downsample_str: string corresponding to downsample, structured like "4x".
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
        loader=jinja2.PackageLoader('qqa.webpages', 'templates')
    )
    template = env.get_template('spectra.html')

    html_components = dict(
        bokeh_version=bokeh.__version__
    )
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
