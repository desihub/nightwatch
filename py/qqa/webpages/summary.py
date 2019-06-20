"""
Pages summarizing QA results
"""

import numpy as np
import jinja2

from .. import io
from ..webpages.camfiber import get_cds
from ..plots.camfiber import plot_per_fibernum

from bokeh.embed import components
from bokeh.layouts import layout

def write_summary_html(outfile, qadata, plot_components):
    """Write the most important QA plots to outfile
    
    Args:
        outfile: output HTML file
        qadata : fits file of data for a single exposure
        plot_components: dictionary with keys night, expid, flavor, program,
            and QA plots
    
    changes plot_components['qatype'] to 'summary'
    """
    update_camfib_pc(plot_components, qadata)

    env = jinja2.Environment(
        loader=jinja2.PackageLoader('qqa.webpages', 'templates')
    )
    template = env.get_template('summary.html')
        
    #- TODO: Add links to whatever detailed QA pages exist
    
    plot_components['qatype'] = 'summary'
    html = template.render(**plot_components)

    #- Write HTML text to the output file
    with open(outfile, 'w') as fx:
        fx.write(html)

        
def update_camfib_pc(pc, qadata, 
                     metrics=['INTEG_RAW_FLUX', 'MEDIAN_RAW_SNR'], 
                     cameras=['B', 'R', 'Z'], 
                     titlespercam={'B':{'INTEG_RAW_FLUX':'Integrated Raw Counts', 'MEDIAN_RAW_SNR':'Median Raw S/N'}}, 
                     tools='pan,box_zoom,reset',
                    ):
    
    if 'PER_CAMFIBER' not in qadata:
        return
    
    data = qadata['PER_CAMFIBER']
    cds = get_cds(data, metrics, cameras)

    fibernum_gridlist = []
    for attr in metrics:
        if attr in list(cds.data.keys()):
            figs_list = plot_per_fibernum(cds, attr, cameras, titles=titlespercam, tools=tools)

            fibernum_gridlist.extend(figs_list)

    camfiber_layout = layout(fibernum_gridlist)
    
    script, div = components(camfiber_layout)
    pc['CAMFIBER_METRICS'] = dict(script=script, div=div)

