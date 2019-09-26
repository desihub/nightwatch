import numpy as np

import jinja2
import bokeh
from bokeh.embed import components

from ..plots.camera import plot_camera_qa

from ..thresholds import get_thresholds, pick_threshold_file

def write_camera_html(outfile, data, header):
    '''
    Creates a html file with camera qa data (DX, DY, XSIG, YSIG) plotted vs
    Spectrograph number. Each column should have three plots, corresponding to
    the R, B, Z cameras.

    Args :
        outfile : path to where put the html file
        data : PER_CAMERA table (can be astropy table or just numpy matrix)
        header : header of HDU 0 of the input raw data file

    Returns :
        dictionary containing the html components used to plot the html file
    '''

    night = header['NIGHT']
    expid = header['EXPID']
    flavor = header['FLAVOR'].rstrip()
    if "PROGRAM" not in header :
        program = "no program in header!"
    else :
        program = header['PROGRAM'].rstrip()
    exptime = header['EXPTIME']

    env = jinja2.Environment(
        loader=jinja2.PackageLoader('nightwatch.webpages', 'templates')
    )
    template = env.get_template('camera.html')

    html_components = dict(
        bokeh_version=bokeh.__version__, exptime='{:.1f}'.format(exptime),
        night=night, expid=expid, zexpid='{:08d}'.format(expid),
        flavor=flavor, program=program, qatype='camera',
        num_dirs=2,
    )
    num_plots = len(set([i for i in ["MEANDX", "MEANDY", "MEANXSIG", "MEANYSIG"] if i in data.dtype.names]))
    if num_plots==0:
        plot_width = 100
    else:
        plot_width = int(1350/num_plots)

    #- Generate the bokeh figures
    dx_file = pick_threshold_file('DX', night, in_nightwatch=True)
    lower_dx, upper_dx = get_thresholds(dx_file)
    if "MEANDX" in data.dtype.names:
        fig = plot_camera_qa(data, 'DX', lower=lower_dx, upper=upper_dx, title='DX with camera',
                minmax=(-0.3, 0.3), height=200, width=plot_width)
        script, div = components(fig)
        html_components['DX'] = dict(script=script, div=div)
    
    dy_file = pick_threshold_file('DY', night, in_nightwatch=True)
    lower_dy, upper_dy = get_thresholds(dy_file)
    if "MEANDY" in data.dtype.names:
        fig = plot_camera_qa(data, 'DY', lower=lower_dy, upper=upper_dy, title='DY with camera',
                minmax=(-0.3, 0.3), height=200, width=plot_width)
        script, div = components(fig)
        html_components['DY'] = dict(script=script, div=div)

    xsig_file = pick_threshold_file('XSIG', night, in_nightwatch=True)
    lower_xsig, upper_xsig = get_thresholds(xsig_file)
    if "MEANXSIG" in data.dtype.names:
        fig = plot_camera_qa(data, 'XSIG', lower=lower_xsig, upper=upper_xsig, title='XSIG with camera',
                line0=False, minmax=(0.8, 1.2), height=200, width=plot_width)
        script, div = components(fig)
        html_components['XSIG'] = dict(script=script, div=div)

    ysig_file = pick_threshold_file('YSIG', night, in_nightwatch=True)
    lower_ysig, upper_ysig = get_thresholds(ysig_file)
    if "MEANYSIG" in data.dtype.names:
        fig = plot_camera_qa(data, 'YSIG', lower=lower_ysig, upper=upper_ysig, title='YSIG with camera',
                line0=False, minmax=(0.8, 1.2), height=200, width=plot_width)
        script, div = components(fig)
        html_components['YSIG'] = dict(script=script, div=div)

    #- Combine template + components -> HTML
    html = template.render(**html_components)

    #- Write HTML text to the output file
    with open(outfile, 'w') as fx:
        fx.write(html)

    return html_components
