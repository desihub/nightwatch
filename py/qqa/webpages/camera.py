import numpy as np

import jinja2
import bokeh
from bokeh.embed import components

from ..plots.camera import plot_camera_qa

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
        loader=jinja2.PackageLoader('qqa.webpages', 'templates')
    )
    template = env.get_template('camera.html')

    html_components = dict(
        bokeh_version=bokeh.__version__, exptime='{:.1f}'.format(exptime),
        night=night, expid=expid, zexpid='{:08d}'.format(expid),
        flavor=flavor, program=program, qatype='camera',
    )

    #- Generate the bokeh figures
    if "MEANDX" in data.dtype.names:
        fig = plot_camera_qa(data, 'DX', title='DX with camera',
                minmax=(-0.1, 0.1), height=150, width=300)
        script, div = components(fig)
        html_components['DX'] = dict(script=script, div=div)

    if "MEANDY" in data.dtype.names:
        fig = plot_camera_qa(data, 'DY', title='DY with camera',
                minmax=(-0.1, 0.1), height=150, width=300)
        script, div = components(fig)
        html_components['DY'] = dict(script=script, div=div)

    if "MEANXSIG" in data.dtype.names:
        fig = plot_camera_qa(data, 'XSIG', title='XSIG with camera',
                line0=False, minmax=(0.8, 1.3), height=150, width=300)
        script, div = components(fig)
        html_components['XSIG'] = dict(script=script, div=div)

    if "MEANYSIG" in data.dtype.names:
        fig = plot_camera_qa(data, 'YSIG', title='YSIG with camera',
                line0=False, minmax=(0.8, 1.3), height=150, width=300)
        script, div = components(fig)
        html_components['YSIG'] = dict(script=script, div=div)

    #- Combine template + components -> HTML
    html = template.render(**html_components)

    #- Write HTML text to the output file
    with open(outfile, 'w') as fx:
        fx.write(html)

    return html_components
