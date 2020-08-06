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
    '''Write summary webpage for the last exposure processed

    Args:
        outfile: output HTML filename
        qadata: dict of QA tables, keys PER_AMP, PER_CAMFIBER, etc.
        qprocdir: directory with qproc outputs

    Returns:
        html_components dict with keys 'script', 'div' from bokeh
    '''

    plot_components = summary.get_summary_plots(qadata, qprocdir)
    plot_components['qatype'] = 'summary'

    #- Fix links to preproc images
    #- default assumes they are in same dir as summary html, but that isn't
    #- the case for this last exposure summary which is at the top level
    #- TODO: this is fragile; could it be made better?
    if 'READNOISE' in plot_components:
        night = str(plot_components['night'])
        zexpid = plot_components['zexpid']  #- zero padded str expid
        plot_components['READNOISE']['script'] = \
            plot_components['READNOISE']['script'].replace(
                '{"url":"@name-4x.html"}',
                '{"url":"'+night+'/'+zexpid+'/@name-4x.html"}'
                )

    env = jinja2.Environment(
        loader=jinja2.PackageLoader('nightwatch.webpages', 'templates'),
        autoescape=select_autoescape(disabled_extensions=('txt',),
                                     default_for_string=True, 
                                     default=True,
    )
    template = env.get_template('lastexp.html')

    #- Tell HTML to auto-reload upon change, using {staticdir}/live.js
    plot_components['autoreload'] = True
    plot_components['staticdir'] = 'static'

    #- Combine template + components -> HTML
    html = template.render(**plot_components)

    #- Write HTML text to the output file
    with open(outfile, 'w') as fx:
        fx.write(html)

    return plot_components
