import jinja2
from jinja2 import select_autoescape
import bokeh, os, re, sys

from ..plots.guideimage import guide_star_timelapse
from bokeh.embed import components

def write_guide_image_html(image_data, outfile, night, expid):
    '''Writes html file with guide timelapse movie plots for all guide stars on all cameras.
    Args:
        image_data: dictionary containing guide-rois image data
        outfile: file to write html to (str)
        night: night of exposure (int)
    Returns html components.'''
    
    env = jinja2.Environment(
        loader=jinja2.PackageLoader('nightwatch.webpages', 'templates'),
        autoescape=select_autoescape(disabled_extensions=('txt',),
                                     default_for_string=True, 
                                     default=True)
    )
    
    zexpid = '{expid:08d}'.format(expid=expid)
    qatype = 'guide-image'
    template = env.get_template('guideimage.html')

    html_components = dict(
        bokeh_version=bokeh.__version__, night=night,
        expid=int(str(zexpid)), zexpid=zexpid, num_dirs=2, qatype=qatype,
        guideimage=True
    )
    
    fig = guide_star_timelapse(image_data)
    script, div = components(fig)
    html_components["GUIDE_IMAGE"] = dict(script=script, div=div)
   
        
    html = template.render(**html_components)
    
    with open(outfile, 'w') as fx:
        fx.write(html)

    return html_components

    

    