import jinja2
import bokeh, os, re, sys

from ..plots.guideimage import guide_star_timelapse
from bokeh.embed import components

def write_guide_image_html(infile, outfile, night, cam):
    '''Writes html file with guide timelapse movie plots for all guide stars on one camera.
    Args:
        infile: file containing guide-rois image data (str)
        outfile: file to write html to (str)
        night: night of exposure (int)
        cam: camera to generate plots for (int)
    Returns html components.'''
    
    env = jinja2.Environment(
        loader=jinja2.PackageLoader('nightwatch.webpages', 'templates')
    )
    
    template = env.get_template('guideimage.html')
    
    expid = os.path.basename(infile).split("-")[2].split(".")[0]

    html_components = dict(
        bokeh_version=bokeh.__version__, night=night,
        expid=int(str(expid)), zexpid=expid, num_dirs=2, qatype='guiding',
    )
    
    fig = guide_star_timelapse(infile, cam)
    script, div = components(fig)
    html_components["GUIDE_IMAGE"] = dict(script=script, div=div)
   
        
    html = template.render(**html_components)
    
    with open(outfile, 'w') as fx:
        fx.write(html)

    return html_components

    

    