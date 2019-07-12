import jinja2
import bokeh
import sys, os, re
from bokeh.embed import components
from bokeh.layouts import column, gridplot, row
from bokeh.models.widgets import Panel, Tabs

from ..thresholds import get_timeseries_dataset, plot_timeseries, get_threshold_table, get_amp_rows, pick_threshold_file, plot_histogram, get_spec_amps, get_specs

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
        filepath = pick_threshold_file(aspect, end_date)
        specs_in_use = get_specs(data)
        tabs = []
        for i in specs_in_use:
            time = plot_timeseries(data, aspect, amps=get_spec_amps(i), plot_height=250, plot_width=750)
            tab = Panel(child=time, title='{}'.format(i))
            tabs.append(tab)
 
        time = Tabs(tabs=tabs)
        hist = plot_histogram(data, 20, amps=get_spec_amps(specs_in_use, lst=True), plot_height=250, plot_width=250)
        table = get_threshold_table(aspect, filepath, width=750)
        if time is None or hist is None or table is None:
            return "No data between {} and {}".format(start_date, end_date)

        time_script, time_div = components(time)
        hist_script, hist_div = components(hist)
        table_script, table_div = components(table)
        time_label = '{}_time'.format(aspect)
        hist_label = '{}_hist'.format(aspect)
        table_label = '{}_table'.format(aspect)
        html_components[time_label] = dict(script=time_script, div=time_div)
        html_components[hist_label] = dict(script=hist_script, div=hist_div)
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


    