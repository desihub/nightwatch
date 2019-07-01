import jinja2
import bokeh
import sys, os, re
from bokeh.embed import components
from bokeh.layouts import column

from ..thresholds import get_timeseries_dataset, plot_timeseries, get_threshold_table, get_amp_rows, pick_threshold_file, plot_histogram

def write_threshold_html(outfile, datadir, start_date, end_date):
    
    env = jinja2.Environment(
        loader=jinja2.PackageLoader('qqa.webpages', 'templates')
    )
    template = env.get_template('thresholds.html')

    html_components = dict(
        bokeh_version=bokeh.__version__,
        start=start_date, end=end_date,
    )
    
    for aspect in ['READNOISE', 'BIAS']:
        data = get_timeseries_dataset(datadir, start_date, end_date, 'PER_AMP', aspect)
        fig = plot_timeseries(data)
        filepath = pick_threshold_file(aspect, end_date)
        table = get_threshold_table(filepath)
        fig1 = column(fig, table)
        if fig1 is None:
            return "No data between {} and {}".format(start_date, end_date)

        script, div = components(fig1)
        html_components[aspect] = dict(script=script, div=div)
    
    for aspect in ["COSMICS_RATE"]:
        data = get_timeseries_dataset(datadir, start_date, end_date, 'PER_AMP', aspect)
        fig = plot_histogram(data, 20)
        filepath = pick_threshold_file(aspect, end_date)
        table = get_threshold_table(filepath)
        fig1 = column(fig, table)
        if fig1 is None:
            return "No data between {} and {}".format(start_date, end_date)
        
        script, div = components(fig1)
        html_components[aspect] = dict(script=script, div=div)
        
    html = template.render(**html_components)
    
    with open(outfile, 'w') as fx:
        fx.write(html)

    return html_components

    