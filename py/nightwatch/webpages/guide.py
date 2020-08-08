import numpy as np

import jinja2
from jinja2 import select_autoescape
import bokeh
from bokeh.embed import components

from ..plots.guide import guide_scatter_combined, get_all_guide_scatter, get_all_stars_hist
from ..io import get_guide_data

import os 

def write_guide_html(outfile, header, guidedata):
    '''Writes html file with guide line/histogram plots. 
    Args:
        outfile: file to write output, string
        header: header containing metadata on exposure
        guidedata: dictionary of centroid-*.json data, must have entries x_error and y_error
    Returns html components of plot. '''
     
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
        loader=jinja2.PackageLoader('nightwatch.webpages', 'templates'),
        autoescape=select_autoescape(disabled_extensions=('txt',),
                                     default_for_string=True, 
                                     default=True)
    )
    
    template = env.get_template('guide.html')

    html_components = dict(
        bokeh_version=bokeh.__version__, exptime='{:.1f}'.format(exptime),
        night=night, expid=expid, zexpid='{:08d}'.format(expid),
        obstype=obstype, program=program, qatype='guide',
        num_dirs=2,
    )
    
    #- Add a basic set of guide plots
    plot_components = dict()

    #- Generate the bokeh figure
    fig = guide_scatter_combined(guidedata, [0, 2, 3, 5, 7, 8], width=370, height=230, ncols=3)
    
    #- Convert that into the components to embed in the HTML
    script, div = components(fig)
    #- Save those in a dictionary to use later
    html_components['PER_FRAME_GUIDE'] = dict(script=script, div=div)
    
    #- Combine template + components -> HTML
    html = template.render(**html_components)

    #- Write HTML text to the output file
    with open(outfile, 'w') as fx:
        fx.write(html)

    return html_components

    