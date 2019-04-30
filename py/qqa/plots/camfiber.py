import numpy as np

import jinja2

import bokeh
import bokeh.plotting as bk
from bokeh.embed import components
# from bokeh.models.tickers import FixedTicker
# from bokeh.models.ranges import FactorRange

from .fiber import plot_fibers
from .core import default_css

def write_camfiber_html(data, outfile, header):
    '''TODO: document'''
    
    night = header['NIGHT']
    expid = header['EXPID']
    flavor = header['FLAVOR'].rstrip()
    if "PROGRAM" not in header :
        program = "no program in header!"
    else :
        program = header['PROGRAM'].rstrip()
    exptime = header['EXPTIME']
    
    html_template = '''
    <!DOCTYPE html>
    <html lang="en-US">

    <link
        href="https://cdn.pydata.org/bokeh/release/bokeh-{version}.min.css"
        rel="stylesheet" type="text/css"
    >
    <link
        href="https://cdn.pydata.org/bokeh/release/bokeh-tables-{version}.min.css"
        rel="stylesheet" type="text/css"
    >
    <script src="https://cdn.pydata.org/bokeh/release/bokeh-{version}.min.js"></script>
    <script src="https://cdn.pydata.org/bokeh/release/bokeh-tables-{version}.min.js"></script>

    <head>
    <style>
    {default_css}
    </style>
    </head>

    <body>
    <h1>Night {night} exposure {expid}</h1>
    <p>{exptime:.0f} second {flavor} ({program}) exposure</p>
    <h2>Per-camera-fiber QA metrics</h2>

    '''.format(version=bokeh.__version__, night=night, expid=expid,
        exptime=exptime, flavor=flavor, program=program,
        default_css=default_css)
    
    html_template += '''
    <p>Integrated Raw Counts</p>
    <div>
        {{ INTEG_RAW_FLUX_script }} {{ INTEG_RAW_FLUX_div }}
    </div>
    <p>Median calibrated signal-to-noise</p>
    <div>
        {{ MEDIAN_CALIB_SNR_script }} {{ MEDIAN_CALIB_SNR_div }}
    </div>
    </body>
    </html>
    '''
    
    #- Add a basic set of PER_AMP QA plots
    plot_components = dict()
    for qaname in ['INTEG_RAW_FLUX', 'MEDIAN_CALIB_SNR']:
        figB, hfigB = plot_fibers(data, qaname, 'B')
        figR, hfigR = plot_fibers(data, qaname, 'R')
        figZ, hfigZ = plot_fibers(data, qaname, 'Z')
        figs = bk.gridplot([[figB, figR, figZ], [hfigB, hfigR, hfigZ]],
                    toolbar_location='right')
        # script, div = components(bk.Row(*figs))
        
        # script, div = components(bk.Row(figs[0].children[0]))
        script, div = components(figs)
                
        plot_components[qaname+'_script'] = script
        plot_components[qaname+'_div'] = div
            
    #- Combine template + components -> HTML
    html = jinja2.Template(html_template).render(**plot_components)
    
    #- Write HTML text to the output file
    with open(outfile, 'w') as fx:
        fx.write(html)
    