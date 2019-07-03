import jinja2
import bokeh
import sys, os, re
from bokeh.embed import components
from bokeh.layouts import column, gridplot, row

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
    
    for aspect in ['READNOISE', 'BIAS', 'COSMICS_RATE']:
        data = get_timeseries_dataset(datadir, start_date, end_date, 'PER_AMP', aspect)
        timeseries = plot_timeseries(data, aspect)
        histogram = plot_histogram(data, bins=20)
        filepath = pick_threshold_file(aspect, end_date)
        table = get_threshold_table(filepath)
        fig = gridplot(children=[[timeseries, histogram]], toolbar_location='right')
        if fig is None:
            return "No data between {} and {}".format(start_date, end_date)

        script, div = components(fig)
        table_script, table_div = components(table)
        table_label = '{}_table'.format(aspect)
        html_components[aspect] = dict(script=script, div=div)
        html_components[table_label] = dict(script=table_script, div=table_div)
    
#     for aspect in ["COSMICS_RATE"]:
#         data = get_timeseries_dataset(datadir, start_date, end_date, 'PER_AMP', aspect)
#         timeseries = plot_timeseries(data)
#         histogram = plot_histogram(data, 20)
#         filepath = pick_threshold_file(aspect, end_date)
#         table = get_threshold_table(filepath)
#         fig = gridplot([timeseries, histogram], [table,])
#         if fig is None:
#             return "No data between {} and {}".format(start_date, end_date)
        
#         script, div = components(fig)
#         html_components[aspect] = dict(script=script, div=div)
        
    html = template.render(**html_components)
    
    with open(outfile, 'w') as fx:
        fx.write(html)

    return html_components

    