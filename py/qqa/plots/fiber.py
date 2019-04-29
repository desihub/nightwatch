import numpy as np

from astropy.table import Table, join
import jinja2

import bokeh
import bokeh.plotting as bk
from bokeh.embed import components
# from bokeh.models.tickers import FixedTicker
# from bokeh.models.ranges import FactorRange

from bokeh.models import LinearColorMapper, ColorBar # HoverTool, CustomJS, HTMLTemplateFormatter, NumeralTickFormatter
from bokeh.transform import transform

import bokeh.palettes

import desimodel.io

def get_colors(x, xmin=None, xmax=None):
    '''
    TODO: document
    TODO: move this into plots.core or similar
    '''
    palette = np.array(bokeh.palettes.all_palettes['RdBu'][11])
    n = len(palette)
    
    x = np.asarray(x)
    if xmin is None:
        xmin = np.min(x)
    if xmax is None:
        xmax = np.max(x)

    x.clip(xmin, xmax)
    ii = (n*(x-xmin) / (xmax-xmin)).astype(int).clip(0,n-1)
    return palette[ii]

def plot_fibers(qadata, name, cam=None, width=250, height=230,
    zmin=None, zmax=None):
    '''TODO: document'''

    #- bytes vs. str, what a pain
    qadata = Table(qadata)
    qadata['CAM'] = qadata['CAM'].astype(str)
    
    #- Filter data to just this camera
    if cam is not None:
        ii = (qadata['CAM'] == cam.lower()) | (qadata['CAM'] == cam.upper())
        qadata = qadata[ii]

    #- Join with fiberpos to know where fibers are on focal plane
    #- TODO: use input fibermap instead
    fiberpos = Table(desimodel.io.load_fiberpos())
    fiberpos.remove_column('SPECTRO')
    qadata = join(qadata, fiberpos, keys='FIBER')

    metric = qadata[name]
    if zmin is not None or zmax is not None:
        metric = np.clip(metric, zmin, zmax)

    #- Focal plane colored scatter plot
    fig = bk.figure(width=width, height=width, toolbar_location=None)
    
    colors = get_colors(metric)
    fig.scatter(qadata['X'], qadata['Y'], color=colors, radius=5, alpha=0.7)
    fig.x_range = bokeh.models.Range1d(-420, 420)
    fig.y_range = bokeh.models.Range1d(-420, 420)
    
    ii = ~np.in1d(fiberpos['FIBER'], qadata['FIBER'])
    fig.scatter(fiberpos['X'][ii], fiberpos['Y'][ii], color='#DDDDDD', radius=2)
    
    camcolors = dict(B='steelblue', R='firebrick', Z='gray')
    
    if cam is not None:
        color = camcolors[cam.upper()]
        fig.ellipse(x=[0,], y=[0,], width=830, height=830, fill_color=None,
                    line_color=color, line_alpha=0.5, line_width=2)
    
    if cam is not None:
        fig.text([-350,], [350,], [cam.upper(),], text_color=camcolors[cam.upper()],
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
    #- TODO: move basic histogram code into plots.core or similar
    hist, edges = np.histogram(metric, density=True, bins=50)
        
    centers = 0.5*(edges[1:] + edges[:-1])

    hfig = bk.figure(width=width, height=80)

    colors = get_colors(centers)
    hfig.quad(top=hist, bottom=0, left=edges[:-1], right=edges[1:], color=colors, alpha=0.5)
    
    hfig.xaxis.axis_label = name
    
    hfig.toolbar_location = None
    hfig.title.text_color = '#ffffff'
    hfig.yaxis.major_label_text_font_size = '0pt'
    hfig.xgrid.grid_line_color = None
    hfig.ygrid.grid_line_color = None
    hfig.yaxis.major_tick_line_color = None
    hfig.yaxis.minor_tick_line_color = None
    hfig.outline_line_color = None
    hfig.yaxis.axis_line_color = None

    return fig, hfig
