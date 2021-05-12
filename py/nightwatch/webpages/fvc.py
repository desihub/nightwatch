import jinja2
from jinja2 import select_autoescape
import bokeh, os, re, sys

from ..plots.fvc import plot_fvc
from bokeh.embed import components

def write_fvc_html(output, downsample, night, expid):
    '''
    Writes the downsampled fvc image to a given output file.
    Inputs:
        output: the filepath to write html file to
        downsample: downsample image NxN
        night: the night YYYYMMDD the image belongs to
        expid: the exposure ID of the image
    '''

    env = jinja2.Environment(
        loader=jinja2.PackageLoader('nightwatch.webpages', 'templates'),
        autoescape=select_autoescape(disabled_extensions=('txt',),
                                     default_for_string=True,
                                     default=True)
    )

    template = env.get_template('fvc.html')
    
    expos = '{:08d}'.format(night) +'/'+ '{:08d}'.format(expid)
    zexpid = '{expid:08d}'.format(expid=expid)
    qatype = 'fvc'
    
    fig = plot_fvc(expos, downsample=2) # Downsample chosen for ~10 second load time
    plot_script, plot_div = components(fig)

    html_components = dict(
        bokeh_version=bokeh.__version__, night=night,
        expid=int(str(zexpid)), zexpid=zexpid, num_dirs=2, qatype=qatype,
        plot_script=plot_script, plot_div=plot_div,
    )
    
    html = template.render(**html_components)

    #- Write HTML text to the output file
    with open(output, 'w') as fx:
        fx.write(html)

    print('Wrote {}'.format(output))
    

    
