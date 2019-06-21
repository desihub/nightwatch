import numpy as np

import jinja2
import bokeh
from bokeh.embed import components
from bokeh.layouts import gridplot, layout

from ..plots.amp import plot_amp_qa
from . import camfiber

def write_lastexp_html(outfile, data):
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

    #- CCD Rease Noise
    fig = plot_amp_qa(data['PER_AMP'], 'READNOISE', title='CCD Amplifier Read Noise',
        qamin=1.5, qamax=4.0)
    script, div = components(fig)
    html_components['READNOISE'] = dict(script=script, div=div)

    #- Raw flux
    if flavor.upper() in ['ARC', 'FLAT']:
        cameras = ['B', 'R', 'Z']  #- TODO: derive from data
        cds = camfiber.get_cds(data['PER_CAMFIBER'], ['INTEG_RAW_FLUX',], cameras)
        figs_list = camfiber.plot_per_fibernum(cds, 'INTEG_RAW_FLUX', cameras) #, titles=TITLESPERCAM, tools=TOOLS)
        fn_camfiber_layout = layout(figs_list)

        script, div = components(fn_camfiber_layout)
        html_components['RAWFLUX'] = dict(script=script, div=div)

    #- TODO: Spectra
    if flavor.upper() in ['ARC', 'FLAT', 'SCIENCE']:
        pass

    #- Combine template + components -> HTML
    html = template.render(**html_components)

    #- Write HTML text to the output file
    with open(outfile, 'w') as fx:
        fx.write(html)

    return html_components
