import numpy as np

import jinja2
import bokeh
from bokeh.embed import components

from ..plots.amp import plot_amp_qa
from ..thresholds import pick_threshold_file, get_thresholds

import os 

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
        night=night, expid=expid, zexpid='{:08d}'.format(expid),
        flavor=flavor, program=program, qatype='amp',
    )
    
    #- Add a basic set of PER_AMP QA plots
    plot_components = dict()

    #- Generate the bokeh figure
    noise_file = pick_threshold_file('READNOISE', night)
    lower_noise, upper_noise = get_thresholds(noise_file)
    fig = plot_amp_qa(data, 'READNOISE', lower_noise, upper_noise, title='CCD Amplifier Read Noise')
    #- Convert that into the components to embed in the HTML
    script, div = components(fig)
    #- Save those in a dictionary to use later
    html_components['READNOISE'] = dict(script=script, div=div)

    #- Amplifier offset
    bias_file = pick_threshold_file('BIAS', night)
    lower_bias, upper_bias = get_thresholds(bias_file)
    fig = plot_amp_qa(data, 'BIAS', lower_bias, upper_bias, title='CCD Amplifier Overscan Bias Level')
    script, div = components(fig)
    html_components['BIAS'] = dict(script=script, div=div)

    #- Cosmics rate
    cosmics_file = pick_threshold_file('COSMICS_RATE', night)
    lower_cosmics, upper_cosmics = get_thresholds(cosmics_file)
    fig = plot_amp_qa(data, 'COSMICS_RATE', lower_cosmics, upper_cosmics, title='CCD Amplifier cosmics per minute')
    script, div = components(fig)
    html_components['COSMICS_RATE'] = dict(script=script, div=div)

    #- Combine template + components -> HTML
    html = template.render(**html_components)

    #- Write HTML text to the output file
    with open(outfile, 'w') as fx:
        fx.write(html)

    return html_components
