import numpy as np
import jinja2
import desimodel.io

import bokeh
import bokeh.plotting as bk
import bokeh.models
from bokeh.embed import components

from astropy.table import Table, join
# from bokeh.models.tickers import FixedTicker
from bokeh.models import LinearColorMapper, ColorBar, HoverTool #, CustomJS, HTMLTemplateFormatter
from bokeh.models import ColumnDataSource, CDSView, BooleanFilter
from bokeh.transform import transform
from bokeh.transform import linear_cmap
import bokeh.palettes as bp
from bokeh.models import ColorBar, BasicTicker, ContinuousTicker, NumeralTickFormatter, TapTool, OpenURL
import math
from ..plots.core import get_colors, plot_histogram


def plot_fibers_focalplane(source, name, cam='',
                camcolors=dict(B='steelblue', R='firebrick', Z='green'),
                width=250, height=270, zmin=None, zmax=None,
                percentile=None, title=None, hist_x_range=None,
                upper_cmap = None, fig_x_range=None, fig_y_range=None,
                colorbar=False, palette=None, plot_hist=True, on_target=False,
                tools=['pan','box_select','reset','tap'], tooltips=None):
    '''
    ARGS:
        source :  ColumnDataSource object
        name : a string data column in qadata

    Options:
        cam : string ('B', 'R', 'Z') to specify which camera wavelength
        camcolors : dictionary of colors corresponding to each CAM option
        width, height : width and height of graph in pixels
        (zmin,zmax) : hardcoded (min,max) to clip data for histogram
        percentile : (min,max) percentiles to clip data for histogram
        title : title for the plot
        tools : string of supported features for the plot
        tooltips : hovertool info
        upper_cmap : max value for cmap (used primarily for pos acc plots)
        hist_x_range, fig_x_range, fig_y_range : figure ranges to support linking
        palette : bokeh palette of colors
        colorbar : boolean value to add a color bar
        plot_hist : boolean value to add a histogram
        on_target : boolean value to make fibers on target plot


    Generates a focal plane plot with data per fiber color-coded based on its value
    Generates a histogram of NAME values per fiber
    '''
    full_metric =np.array(source.data.get(name), copy=True)

    #- adjusts for outliers on the full scale
    pmin_full, pmax_full = np.percentile(full_metric, (0, 95))

    #- Generate colors for both plots
    if not palette:
        palette = np.array(bp.RdYlBu[11])
    if not upper_cmap:
        upper_cmap = pmax_full
    mapper = linear_cmap(name, palette, low=pmin_full, high=upper_cmap, nan_color='gray')
    #- Focal plane colored scatter plot
    fig = bk.figure(width=width, height=height, title=title, tools=tools,
                    x_range=fig_x_range, y_range=fig_y_range)

    #- Filter data to just this camera
    '''TODO: this assumes that the source passed in has a cam argument...
        Will that break when plotting fiber plots individually?
    '''
    booleans_metric = np.char.upper(np.array(source.data['CAM']).astype(str)) == cam.upper()
    view_metric = CDSView(source=source, filters=[BooleanFilter(booleans_metric)])

    #- Plot only the fibers which measured the metric
    s = fig.scatter('X', 'Y', source=source, view=view_metric, color=mapper,
                    radius=5, alpha=0.7)

    #- Add hover tool
    if not tooltips:
        tooltips = [("FIBER", "@FIBER"), ("(X, Y)", "(@X, @Y)"),
                    (name, "@" + name + '{(0.00 a)}')]

    hover = HoverTool(renderers = [s], tooltips=tooltips)
    fig.add_tools(hover)

    #- Plot the rest of the fibers
    fibers_measured = source.data['FIBER'][booleans_metric]
    ii = ~np.in1d(source.data['FIBER'], fibers_measured)
    booleans_empty = [fiber in ii for fiber in range(len(source.data))]
    view_empty = CDSView(source=source, filters=[BooleanFilter(booleans_empty)])
    fig.scatter('X', 'Y', source=source, view=view_empty, color='#DDDDDD', radius=2)


    #- Adds colored outline based on camera
    if cam:
        color = camcolors.get(cam.upper())
        fig.ellipse(x=[0,], y=[0,], width=830, height=830, fill_color=None,
                    line_color=color, line_alpha=0.5, line_width=2)
        fig.text([-350,], [350,], [cam.upper(),],
            text_align='center', text_baseline='middle')
    if on_target:
        d = source.data['ON_TARGET'][booleans_metric]
        on_fib = len(d[d == 1])
        fig.text([-350,], [-400,], ['{}'.format(on_fib),],
                text_align='center',text_baseline='middle')

    #- style visual attributes of the figure
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

    taptool = fig.select(type=TapTool)
    taptool.callback = OpenURL(url="spectra/input/@FIBER/qframe/4x/")

    #- Add colorbar
    if colorbar:
        fig.plot_width = fig.plot_width + 60
        colorbar_offset = 12
        color_bar = ColorBar(color_mapper=mapper['transform'], label_standoff=colorbar_offset,
                border_line_color=None, location=(0,0), ticker=BasicTicker(), width=10,
                formatter=NumeralTickFormatter(format='0.0a'))
        fig.add_layout(color_bar, 'right')
        #- adjusting histogram width for colorbar
        width = fig.plot_width - colorbar_offset

    if not plot_hist:
        return fig, None

    if not plot_hist:
        return fig, None

    #- Histogram of values
    metric = full_metric[booleans_metric]

    if any(booleans_metric):
        if percentile:
            pmin, pmax = np.percentile(metric, percentile)
            metric = np.clip(metric, pmin, pmax)
        if zmin or zmax:
            metric = np.clip(metric, zmin, zmax)
    hfig = plot_histogram(metric, title=name, width=width, x_range=hist_x_range, num_bins=50,
                         palette=mapper['transform'].palette, low=pmin_full, high=pmax_full)

    return fig, hfig


def plot_fibernums(source, name, cam='',
                camcolors=dict(B='steelblue', R='firebrick', Z='green'),
                width=700, height=80, title=None, fig_x_range=None,
                fig_y_range=None, tools='pan,box_zoom,tap,reset',
                toolbar_location=None, tooltips=None, xaxislabels=True):
    '''
    ARGS:
        source :  ColumnDataSource object
        name : a string data column in qadata

    Options:
        cam : string ('B', 'R', 'Z') to specify which camera wavelength
        camcolors : dictionary of colors corresponding to each CAM option
        width, height : width and height of graph in pixels
        title : title for the plot
        tools, tooltips, toolbar_location : supported features for the plot
        fig_x_range, fig_y_range : figure ranges to support linking
        palette : bokeh palette of colors
        colorbar : boolean value to add a color bar
        xaxislabels : boolean value to plot x axis labels

    Generates a scatterplot of a metric based on its fiber number
    Generates a histogram of NAME values per fiber
    '''
    #- TODO: this assumes that the source passed in has a cam argument...
    #- Will that break when plotting fiber plots individually?
    full_metric = np.array(source.data.get(name), copy=True)
    #- adjusts for outliers on the full scale
    pmin_full, pmax_full = np.percentile(full_metric, (0, 95))

    #- Fibernum scatter plot
    fig = bk.figure(width=width, height=height, title=title, tools=tools,
                    x_range=fig_x_range, y_range=fig_y_range,
                    toolbar_location=toolbar_location)

    #- Filter data to just this camera
    #- TODO: fails when CAM not in the data source provided
    booleans_metric = np.char.upper(np.array(source.data['CAM']).astype(str)) == cam.upper()
    view_metric = CDSView(source=source, filters=[BooleanFilter(booleans_metric)])

    #- Plot only the fibers which measured the metric
    s = fig.scatter('FIBER', name, source=source, view=view_metric,
                    color=camcolors.get(cam.upper()), alpha=0.7)

    #- Add hover tool
    if not tooltips:
        tooltips = [("FIBER", "@FIBER"), (name, "@" + name + '{(0.00 a)}')]
    hover = HoverTool(renderers = [s], tooltips=tooltips)
    fig.add_tools(hover)

    #- style visual attributes of the figure
    if not xaxislabels:
        fig.xaxis.axis_label = None
        fig.xaxis.major_tick_line_color = None
        fig.xaxis.minor_tick_line_color = None
        fig.xaxis.major_label_text_font_size = '0pt'
        fig.xaxis.major_tick_line_width = 0
        fig.xaxis.minor_tick_line_width = 0
    else:
        fig.xaxis.major_label_orientation = math.pi/4
        fig.xaxis.axis_label = 'Fiber number'

    fig.outline_line_color = camcolors.get(cam.upper())
    fig.xaxis.axis_line_color = camcolors.get(cam.upper())
    fig.yaxis.axis_label = cam
    fig.yaxis.minor_tick_line_color=None
    fig.ygrid.grid_line_color = None
    fig.yaxis.formatter = NumeralTickFormatter(format='0.0a')

    taptool = fig.select(type=TapTool)
    taptool.callback = OpenURL(url="spectra/input/@FIBER/qframe/4x/")

    return fig
