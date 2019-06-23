import os

import numpy as np

import jinja2
import bokeh
from bokeh.embed import components
from bokeh.layouts import gridplot, layout

from ..plots.amp import plot_amp_qa
from ..plots.spectra import plot_spectra_input
from . import camfiber

def write_lastexp_html(outfile, data, qprocdir):
    '''TODO: document'''
    
    header = data['HEADER']
    night = header['NIGHT']
    expid = header['EXPID']
    flavor = header['FLAVOR'].rstrip()
    if "PROGRAM" not in header :
        program = "no program in header!"
    else :
        program = header['PROGRAM'].rstrip()
    exptime = header['EXPTIME']

    env = jinja2.Environment(
        loader=jinja2.PackageLoader('qqa.webpages', 'templates')
    )
    template = env.get_template('lastexp.html')

    html_components = dict(
        bokeh_version=bokeh.__version__, exptime='{:.1f}'.format(exptime),
        night=night, expid=expid, zexpid='{:08d}'.format(expid),
        flavor=flavor, program=program,
    )
    
    #- Add a basic set of PER_AMP QA plots
    plot_components = dict()

    plot_width = 500

    #- CCD Read Noise
    fig = plot_amp_qa(data['PER_AMP'], 'READNOISE', title='CCD Amplifier Read Noise',
        qamin=1.5, qamax=4.0, ymin=0, ymax=5.0,
        plot_width=plot_width, plot_height=110)
    script, div = components(fig)
    html_components['READNOISE'] = dict(script=script, div=div)

    #- Raw flux
    if flavor.upper() in ['ARC', 'FLAT']:
        cameras = ['B', 'R', 'Z']  #- TODO: derive from data
        cds = camfiber.get_cds(data['PER_CAMFIBER'], ['INTEG_RAW_FLUX',], cameras)
        figs_list = camfiber.plot_per_fibernum(cds, 'INTEG_RAW_FLUX', cameras,
            height=120, ymin=0, width=plot_width)
        figs_list[0].title = bokeh.models.Title(text="Integrated Raw Flux Per Fiber")
        fn_camfiber_layout = layout(figs_list)

        script, div = components(fn_camfiber_layout)
        html_components['RAWFLUX'] = dict(script=script, div=div)

    #- Random Spectra
    if flavor.upper() in ['ARC', 'FLAT', 'SCIENCE'] and \
            'PER_CAMFIBER' in data and \
            qprocdir is not None:
        downsample = 4
        nfib = min(5, len(data['PER_CAMFIBER']))
        fibers = sorted(np.random.choice(data['PER_CAMFIBER']['FIBER'], size=nfib, replace=False))
        fibers = ','.join([str(tmp) for tmp in fibers])

        specfig = plot_spectra_input(os.path.dirname(qprocdir), expid, downsample,
            fibers, height=300, width=plot_width*2)
        script, div = components(specfig)
        html_components['SPECTRA'] = dict(script=script, div=div, fibers=fibers)

    #- Combine template + components -> HTML
    html = template.render(**html_components)

    #- Write HTML text to the output file
    with open(outfile, 'w') as fx:
        fx.write(html)

    return html_components
