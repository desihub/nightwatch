import numpy as np

import jinja2
import bokeh
from bokeh.embed import components

from ..plots.amp import plot_amp_qa

def write_amp_html(outfile, data, header):
    '''TODO: document'''
    
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
    template = env.get_template('amp.html')

    html_components = dict(
        bokeh_version=bokeh.__version__, exptime='{:.1f}'.format(exptime),
        night=night, expid=expid, flavor=flavor, program=program,
    )
    
    #- Add a basic set of PER_AMP QA plots
    plot_components = dict()

    #- Generate the bokeh figure
    fig = plot_amp_qa(data, 'READNOISE', title='CCD Amplifier Read Noise',
        qamin=1.5, qamax=4.0)
    #- Convert that into the components to embed in the HTML
    script, div = components(fig)
    #- Save those in a dictionary to use later
    html_components['READNOISE'] = dict(script=script, div=div)

    #- Amplifier offset
    fig = plot_amp_qa(data, 'BIAS', title='CCD Amplifier Overscan Bias Level',
        palette=bokeh.palettes.all_palettes['GnBu'][6])
    script, div = components(fig)
    html_components['BIAS'] = dict(script=script, div=div)

    #- Cosmics rate
    fig = plot_amp_qa(data, 'COSMICS_RATE',
        title='CCD Amplifier cosmics per minute',
        palette=bokeh.palettes.all_palettes['RdYlGn'][11][1:-1],
        qamin=0, qamax=50)
    script, div = components(fig)
    html_components['COSMICS_RATE'] = dict(script=script, div=div)

    #- Combine template + components -> HTML
    html = template.render(**html_components)

    #- Write HTML text to the output file
    with open(outfile, 'w') as fx:
        fx.write(html)

    return html_components
