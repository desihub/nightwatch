"""
Placeholder: Core shared routines for plotting
"""
import numpy as np
import bokeh
import bokeh.plotting as bk
import bokeh.palettes as palettes

def get_colors(x, palette=palettes.all_palettes['RdBu'][11], 
	xmin=None, xmax=None):
    '''
    TODO: document
    Returns a palette of colors for 
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

def plot_histogram(metric, palette=palettes.all_palettes['RdBu'][11], num_bins=50,
                  width=250, height=80, x_range=None, title=None):
    '''
    TODO: document
    Generates a histogram of values from METRIC
    
    Args:
        metric : a numpy array of values to plot
        
    Options:
        palette : a bokeh palette to color the histogram
        num_bins : 
        width, height : 
        x_range : 
        title : 
    
    Returns a Bokeh figure object
    '''
    hfig = bk.figure(width=width, height=height, x_range=x_range)
    hist, edges = np.histogram(metric, density=True, bins=num_bins)
    centers = 0.5 * (edges[1:] + edges[:-1])
    colors = get_colors(centers, palette)
    hfig.quad(top=hist, bottom=0, left=edges[:-1], right=edges[1:], 
        color=colors, alpha=0.5)
    
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

    return hfig