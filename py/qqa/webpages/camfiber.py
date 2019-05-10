import numpy as np

import jinja2

import bokeh
import bokeh.plotting as bk
from bokeh.embed import components

from ..plots.fiber import plot_fibers

def write_camfiber_html(outfile, data, header):
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
    template = env.get_template('camfiber.html')

    html_components = dict(
        bokeh_version=bokeh.__version__, exptime='{:.1f}'.format(exptime),
        night=night, expid=expid, flavor=flavor, program=program,
        qatype = 'camfiber',
    )

    #- TODO: refactor these to reduce replicated code, while still supporting
    #- customizations like percentile vs. zmin/zmax

    #- Integrated Raw Flux
    figB, hfigB = plot_fibers(data, 'INTEG_RAW_FLUX', 'B', percentile=(0,95))
    figR, hfigR = plot_fibers(data, 'INTEG_RAW_FLUX', 'R', percentile=(0,95))
    figZ, hfigZ = plot_fibers(data, 'INTEG_RAW_FLUX', 'Z', percentile=(0,98))
    figs = bk.gridplot([[figB, figR, figZ], [hfigB, hfigR, hfigZ]],
                toolbar_location='right')

    script, div = components(figs)
    html_components['INTEG_RAW_FLUX'] = dict(script=script, div=div)

    #- Median S/N
    figB, hfigB = plot_fibers(data, 'MEDIAN_RAW_SNR', 'B', zmin=0, zmax=10)
    figR, hfigR = plot_fibers(data, 'MEDIAN_RAW_SNR', 'R', zmin=0, zmax=10)
    figZ, hfigZ = plot_fibers(data, 'MEDIAN_RAW_SNR', 'Z', zmin=0, zmax=10)
    figs = bk.gridplot([[figB, figR, figZ], [hfigB, hfigR, hfigZ]],
                toolbar_location='right')

    script, div = components(figs)
    html_components['MEDIAN_RAW_SNR'] = dict(script=script, div=div)
            
    #- Combine template + components -> HTML
    html = template.render(**html_components)
    
    #- Write HTML text to the output file
    with open(outfile, 'w') as fx:
        fx.write(html)

    return html_components
    