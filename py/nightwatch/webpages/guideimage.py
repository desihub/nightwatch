import jinja2
import bokeh, os, re, sys

from ..plots.guideimage import guide_star_timelapse, all_stars_timelapse
from bokeh.embed import components

def write_guide_image_html(infile, outfile, night, cam):
    '''add docstrings'''
    
    env = jinja2.Environment(
        loader=jinja2.PackageLoader('nightwatch.webpages', 'templates')
    )
    
    template = env.get_template('guideimage.html')
    
    expid = os.path.basename(infile).split("-")[2].split(".")[0]

    html_components = dict(
        bokeh_version=bokeh.__version__, night=night,
        expid=int(str(expid)), zexpid=expid, num_dirs=2, qatype='guiding',
        current=cam, available=[0, 2, 3, 5, 7, 8]
    )
    
    fig = all_stars_timelapse(infile, cam)
    script, div = components(fig)
    html_components["GUIDE_IMAGE"] = dict(script=script, div=div)
   
        
    html = template.render(**html_components)
    
    with open(outfile, 'w') as fx:
        fx.write(html)

    return html_components

    

    