import numpy as np
import os

import jinja2
import bokeh
from bokeh.embed import components

from ..plots.summaryqa import get_skyplot, get_summarytable, get_hist, get_exposuresPerTile_hist, get_median


def get_summaryqa_html(exposures, tiles, outdir, height=250, width=250):   
    '''docstring'''
    
    env = jinja2.Environment(
        loader=jinja2.PackageLoader('nightwatch.webpages', 'templates')
    )
    
    template = env.get_template('summaryqa.html')
    
    min_border = 30

    skyplot = get_skyplot(exposures, tiles, height=300, width=600, min_border_left=min_border, min_border_right=min_border)
    skyplot_script, skyplot_div = components(skyplot)

    summarytable = get_summarytable(exposures)
    summarytable_script, summarytable_div = components(summarytable)

    seeing_hist = get_hist(exposures, "SEEING", "navy", height=height, width=width, min_border_left=min_border, min_border_right=min_border)
    seeing_script, seeing_div = components(seeing_hist)

    airmass_hist = get_hist(exposures, "AIRMASS", "green", height=height, width=width, min_border_left=min_border, min_border_right=min_border)
    airmass_script, airmass_div = components(airmass_hist)

    transp_hist = get_hist(exposures, "TRANSP", "purple", height=height, width=width, min_border_left=min_border, min_border_right=min_border)
    transp_hist_script, transp_hist_div = components(transp_hist)
    
    exptime_hist = get_hist(exposures, "EXPTIME", "darkorange", height=height, width=width, min_border_left=min_border, min_border_right=min_border)
    exptime_script, exptime_div = components(exptime_hist)
    
    brightnessplot = get_hist(exposures, "SKY", "pink", height=height, width=width, min_border_left=min_border, min_border_right=min_border)
    brightness_script, brightness_div = components(brightnessplot)
    
    exposePerTile_hist = get_exposuresPerTile_hist(exposures, "orange", height=height, width=width, min_border_left=min_border, min_border_right=min_border)
    exposePerTile_hist_script, exposePerTile_hist_div = components(exposePerTile_hist)
    

    #- Convert to a jinja2.Template object and render HTML
    html_components = dict(
        bokeh_version=bokeh.__version__, last_night = max(exposures["NIGHT"]),
        skyplot_script=skyplot_script, skyplot_div=skyplot_div,
        summarytable_script=summarytable_script, summarytable_div=summarytable_div,
        airmass_script=airmass_script, airmass_div=airmass_div,
        seeing_script=seeing_script, seeing_div=seeing_div,
        exptime_script=exptime_script, exptime_div=exptime_div,
        transp_hist_script=transp_hist_script, transp_hist_div=transp_hist_div,
        exposePerTile_hist_script=exposePerTile_hist_script, exposePerTile_hist_div=exposePerTile_hist_div,
        brightness_script=brightness_script, brightness_div=brightness_div,
        )
    
    #- Combine template + components -> HTML
    html = template.render(**html_components)

    #- Write HTML text to the output file
    outfile = os.path.join(outdir, 'summaryqa.html')
    with open(outfile, 'w') as fx:
        fx.write(html)

    return html_components

