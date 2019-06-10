import numpy as np

import jinja2
import bokeh
from bokeh.embed import components

from ..plots.camera import plot_camera_qa

def write_camera_html(outfile, data, header):
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
    template = env.get_template('camera.html')

    html_components = dict(
        bokeh_version=bokeh.__version__, exptime='{:.1f}'.format(exptime),
        night=night, expid=expid, zexpid='{:08d}'.format(expid),
        flavor=flavor, program=program, qatype='camera',
    )

    #- Generate the bokeh figures
    fig = plot_camera_qa(data, 'DX', title='DX with camera')
    script, div = components(fig)
    html_components['DX'] = dict(script=script, div=div)

    fig = plot_camera_qa(data, 'DY', title='DY with camera')
    script, div = components(fig)
    html_components['DY'] = dict(script=script, div=div)

    fig = plot_camera_qa(data, 'XSIG', title='XSIG with camera', line0=False)
    script, div = components(fig)
    html_components['XSIG'] = dict(script=script, div=div)

    fig = plot_camera_qa(data, 'YSIG', title='YSIG with camera', line0=False)
    script, div = components(fig)
    html_components['YSIG'] = dict(script=script, div=div)

    #- Combine template + components -> HTML
    html = template.render(**html_components)

    #- Write HTML text to the output file
    with open(outfile, 'w') as fx:
        fx.write(html)

    return html_components
