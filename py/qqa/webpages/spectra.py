import numpy as np

import jinja2
import bokeh, sys
from bokeh.embed import components

from ..plots import spectra

def get_spectra_html(data, expid, view, downsample_str, select_string = None):
    '''TODO: document'''

    if view not in ["spectrograph", "objtype", "input"]:
        print("No such view " + view, file=sys.stderr)
        return "No such view " + view

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
        if downsample_str[len(downsample_str)] != "x":
            return("invalid downsample")
        try:
            downsample = int(downsample_str[0:len(downsample_str)-1])
        except:
            return("invalid downsample")

    html_components["downsample"] = downsample
    #- Generate the bokeh figure
    if view == "spectrograph":
        fig = spectra.plot_spectra_spectro(data, expid, downsample)
    elif view == "objtype":
        fig = spectra.plot_spectra_objtype(data, expid, downsample)
    elif view == "input":
        html_components["input"] = True
        fig = None
        if select_string != None:
            html_components["select_str"] = select_string
            fig = spectra.plot_spectra_input(data, expid, downsample, select_string)
            if fig is None:
                return "None selected"

    if fig:
        #- Convert that into the components to embed in the HTML
        script, div = components(fig)
        #- Save those in a dictionary to use later
        html_components['spectra'] = dict(script=script, div=div)
    #- Combine template + components -> HTML
    html = template.render(**html_components)

    return html
