"""
Placeholder: Core shared routines for plotting
"""
import numpy as np
import bokeh
import bokeh.plotting as bk
import bokeh.palettes as bp
from bokeh.transform import linear_cmap
from bokeh.models import ColumnDataSource
from bokeh.models import NumeralTickFormatter
import math


def get_colors(x, palette=bp.all_palettes['RdYlBu'][11],
    xmin=None, xmax=None):
    '''
    Returns a palette of colors for an array of values
    Supports clipping of this metric to provided min and max values
    Args:
        x : an array of values corresponding to a metric to plot
    Options:
        palette : a bokeh palette of colors
        xmin, xmax : cutoffs to clip values in x
    '''
    palette = np.array(palette)
    n = len(palette)

    x = np.asarray(x)
    if xmin is None:
        xmin = np.min(x)
    if xmax is None:
        xmax = np.max(x)

    x.clip(xmin, xmax)
    if (xmin == xmax):
        raise RuntimeWarning
    ii = (n*(x-xmin) / (xmax-xmin)).astype(int).clip(0,n-1)
    return palette[ii]

def plot_histogram(metric, num_bins=50, width=250, height=80, x_range=None, title=None,
                  palette=None, low=None, high=None):
    '''
    Generates a histogram of values from METRIC

    Args:
        metric : a numpy array of values to plot

    Options:
        palette : a bokeh palette to color the histogram
        num_bins : number of bins for the histogram
        width, height : width and height of figure in pixels
        x_range : range of histogram values
        title : figure title

    Returns a Bokeh figure object
    '''
    hfig = bk.figure(width=width, height=height, x_range=x_range)
    hist, edges = np.histogram(metric, density=True, bins=num_bins)
    centers = 0.5 * (edges[1:] + edges[:-1])

    data = dict(
        top = hist,
        bottom = np.zeros(len(hist)),
        left = edges[:-1],
        right = edges[1:],
        centers = centers)
    src = ColumnDataSource(data=data)

    #- Generate histogram colors
    if palette is not None:
        if not low:
            print('new low')
            low = min(metric)
        if not high:
            print('new high')
            high = max(metric)
        mapper = linear_cmap('centers', palette, low=low, high=high, nan_color='gray')
    else:
        palette = ['gray' for _ in range(len(edges))]
        mapper = linear_cmap('centers', palette, low=min(metric), high=max(metric), nan_color='gray')


    hfig.quad(top='top', bottom='bottom', left='left', right='right', color=mapper,
              alpha=0.5, source=src)

    hfig.xaxis.axis_label = title
    hfig.toolbar_location = None
    hfig.title.text_color = '#ffffff'
    hfig.yaxis.major_label_text_font_size = '0pt'
    hfig.xgrid.grid_line_color = None
    hfig.ygrid.grid_line_color = None
    hfig.yaxis.major_tick_line_color = None
    hfig.yaxis.minor_tick_line_color = None
    hfig.outline_line_color = None
    hfig.yaxis.axis_line_color = None
    hfig.xaxis.major_label_orientation = math.pi/4
    hfig.xaxis[0].formatter = NumeralTickFormatter(format='0.0a')

    return hfig
