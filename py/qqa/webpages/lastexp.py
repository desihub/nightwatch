import os

import numpy as np

import jinja2
import bokeh
from bokeh.embed import components
from bokeh.layouts import gridplot, layout

from ..plots.amp import plot_amp_qa
from ..plots.spectra import plot_spectra_input
from . import summary

def write_lastexp_html(outfile, qadata, qprocdir):
    '''TODO: document'''

    plotdir = os.path.dirname(outfile)
    plot_components = summary.get_summary_plots(qadata, plotdir, qprocdir)
    plot_components['qatype'] = 'summary'

    env = jinja2.Environment(
        loader=jinja2.PackageLoader('qqa.webpages', 'templates')
    )
    template = env.get_template('lastexp.html')

    #- Tell HTML to auto-reload upon change, using {staticdir}/live.js
    plot_components['autoreload'] = True
    plot_components['staticdir'] = 'cal_files'

    #- Combine template + components -> HTML
    html = template.render(**plot_components)

    #- Write HTML text to the output file
    with open(outfile, 'w') as fx:
        fx.write(html)

    return plot_components
