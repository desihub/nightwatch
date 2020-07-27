import numpy as np

import jinja2
import bokeh
from bokeh.embed import components

from ..plots.amp import plot_amp_qa
from ..thresholds import pick_threshold_file, get_thresholds

import os 
from desiutil.log import get_logger

def write_amp_html(outfile, data, header):
    '''Write CCD amp QA webpage

    Args:
        outfile: output HTML filename
        data: PER_AMP QA table
        header: dict-like data header with keys NIGHT, EXPID, PROGRAM

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
    if "PROGRAM" not in header :
        program = "no program in header!"
    else :
        program = header['PROGRAM'].rstrip()
    exptime = header['EXPTIME']

    env = jinja2.Environment(
        loader=jinja2.PackageLoader('nightwatch.webpages', 'templates')
    )
    template = env.get_template('amp.html')

    html_components = dict(
        bokeh_version=bokeh.__version__, exptime='{:.1f}'.format(exptime),
        night=night, expid=expid, zexpid='{:08d}'.format(expid),
        obstype=obstype, program=program, qatype='amp',
        num_dirs=2,
    )
    
    #- Add a basic set of PER_AMP QA plots
    plot_components = dict()

    #- Generate the bokeh figure
    noise_file = pick_threshold_file('READNOISE', night, in_nightwatch=True)
    lower_noise, upper_noise, noise_keys = get_thresholds(noise_file, return_keys=True)
    fig = plot_amp_qa(data, 'READNOISE', lower=lower_noise, upper=upper_noise,
        amp_keys=noise_keys, title='CCD Amplifier Read Noise',
        ymin=[0,0,0], ymax=[5,5,5])
    #- Convert that into the components to embed in the HTML
    script, div = components(fig)
    #- Save those in a dictionary to use later
    html_components['READNOISE'] = dict(script=script, div=div)

    #- Amplifier offset
    bias_file = pick_threshold_file('BIAS', night, in_nightwatch=True)
    lower_bias, upper_bias, bias_keys = get_thresholds(bias_file, return_keys=True)
    fig = plot_amp_qa(data, 'BIAS', lower=lower_bias, upper=upper_bias,
        amp_keys=bias_keys, title='CCD Amplifier Overscan Bias Level',
        ymin=[1100, 1900, 1900], ymax=[1200, 2000, 2000])
    script, div = components(fig)
    html_components['BIAS'] = dict(script=script, div=div)

    #- Cosmics rate
    cosmics_file = pick_threshold_file('COSMICS_RATE', night, in_nightwatch=True)
    lower_cosmics, upper_cosmics, cosmics_keys = get_thresholds(cosmics_file, return_keys=True)
    fig = plot_amp_qa(data, 'COSMICS_RATE', lower=lower_cosmics, upper=upper_cosmics,
        amp_keys=cosmics_keys, title='CCD Amplifier cosmics per minute',
        ymin=[0, 0, 0], ymax=[50, 100, 100])
    script, div = components(fig)
    html_components['COSMICS_RATE'] = dict(script=script, div=div)

    #- Combine template + components -> HTML
    html = template.render(**html_components)

    #- Write HTML text to the output file
    with open(outfile, 'w') as fx:
        fx.write(html)

    return html_components
