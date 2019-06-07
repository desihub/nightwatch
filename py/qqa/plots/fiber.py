import numpy as np
import jinja2
import desimodel.io

import bokeh
import bokeh.plotting as bk
import bokeh.models
from bokeh.embed import components

from astropy.table import Table, join
# from bokeh.models.tickers import FixedTicker
# from bokeh.models.ranges import FactorRange
from bokeh.models import LinearColorMapper, ColorBar, HoverTool #, CustomJS, HTMLTemplateFormatter, NumeralTickFormatter
from bokeh.models import ColumnDataSource, CDSView, BooleanFilter
from bokeh.transform import transform
from bokeh.transform import linear_cmap
import bokeh.palettes as palettes
from ..plots.core import get_colors, plot_histogram

def plot_fibers(source, name, cam=None, width=250, height=270, zmin=None, 
                zmax=None, percentile=None, title=None, x_range=None,
                tools='pan,box_select,reset', tooltips=None):
    '''TODO: document
    ARGS:
        source :  ColumnDataSource object
        name : a string data column in qadata

    Options:
        cam : string ('B', 'R', 'Z') to specify which camera wavelength
        (zmin,zmax) : hardcoded (min,max) to clip data
        percentile : (min,max) percentiles to clip data
        width, height : width and height of graph in pixels
        title : title for the plot
        tools : string of supported features for the plot
        tooltips : hovertool info


    Generates a focal plane plot with data per fiber color-coded based on its value
    Generates a histogram of NAME values per fiber
    '''
    #- Focal plane colored scatter plot
    fig = bk.figure(width=width, height=height, title=title, tools=tools)

    #- Filter data to just this camera
    booleans_metric = np.array([True if c == cam.lower() or c == cam.upper()
        else False for c in source.data['CAM']])
    view_metric = CDSView(source=source, filters=[BooleanFilter(booleans_metric)])
    
    #- Plot only the fibers which measured the metric
    s = fig.scatter('X', 'Y', source=source, view=view_metric, color=name+'_color', 
                    radius=5, alpha=0.7)#, hover_color='firebrick')
    # #- Add hover tool
    # hover = HoverTool(renderers = [s], tooltips=tooltips)
    # fig.add_tools(hover)

    
    #- Plot the rest of the fibers
    fibers_measured = source.data['FIBER'][booleans_metric]
    ii = ~np.in1d(source.data['FIBER'], fibers_measured)
    booleans_empty = [fiber in ii for fiber in range(len(source.data))]
    view_empty = CDSView(source=source, filters=[BooleanFilter(booleans_empty)])    
    fig.scatter('X', 'Y', source=source, view=view_empty, color='#DDDDDD', radius=2)

    #- Aesthetics: outline the focal plates by camera color, label cameras,
    #-             style visual attributes of the figure
    fig.x_range = bokeh.models.Range1d(-420, 420)
    fig.y_range = bokeh.models.Range1d(-420, 420)

    camcolors = dict(B='steelblue', R='firebrick', Z='gray')

    if cam:
        color = camcolors[cam.upper()]
        fig.ellipse(x=[0,], y=[0,], width=830, height=830, fill_color=None,
                    line_color=color, line_alpha=0.5, line_width=2)
        fig.text([-350,], [350,], [cam.upper(),],
            text_color=camcolors[cam.upper()],
            text_align='center', text_baseline='middle')

    fig.xgrid.grid_line_color = None
    fig.ygrid.grid_line_color = None
    fig.xaxis.major_tick_line_color = None
    fig.xaxis.minor_tick_line_color = None
    fig.yaxis.major_tick_line_color = None
    fig.yaxis.minor_tick_line_color = None
    fig.outline_line_color = None
    fig.xaxis.axis_line_color = None
    fig.yaxis.axis_line_color = None
    fig.xaxis.major_label_text_font_size = '0pt'
    fig.yaxis.major_label_text_font_size = '0pt'


    #- Histogram of values
    if any(booleans_metric):
        metric = np.array(source.data[name], copy=True)[booleans_metric]
        if percentile:
            pmin, pmax = np.percentile(metric, percentile)
            metric = np.clip(metric, pmin, pmax)
        if zmin or zmax:
            metric = np.clip(metric, zmin, zmax)
        palette = np.sort(source.data[name+'_color'][booleans_metric])
        #palette = palettes.linear_palette(colors, 10)
    else:
        palette = palettes.all_palettes['RdBu'][11]

    hfig = plot_histogram(metric, palette, title=name, width=width,
                          x_range=x_range, num_bins=10)
    


    
    return fig, hfig
