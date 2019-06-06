"""
Placeholder: per-camera per-fiber plots
"""
import numpy as np

import jinja2
from astropy.table import Table

import bokeh
import bokeh.plotting as bk
from bokeh.embed import components

from ..plots.fiber import plot_fibers
from ..plots.core import get_colors
import bokeh.palettes as palettes


def plot_per_camfiber(cds, attribute, cameras, components_dict, percentiles={},
                      zmaxs={}, zmins={}, titles={}, tools=None, tooltips=None):
    '''
    ARGS:
        cds : ColumnDataSource of data
        attribute : string corresponding to column name in DATA
        cameras : list of string representing unique camera values
        components_dict : dictionary of html components for rendering

    Options:
        percentiles : dictionary of cameras corresponding to (min,max)
            percentiles to clip data
        zmaxs : dictionary of cameras corresponding to hardcoded max values
            to clip data
        zmins : dictionary of cameras corresponding to hardcoded min values
            to clip data
        titles : dictionary of titles per camera for a group of camfiber plots
            where key-value pairs represent a camera-attribute plot title

    ***MUTATES ARGUMENT
    Updates COMPONENTS_DICT to include key-value pairs to the html components
        for camfib attribute plot-bokeh gridplot object
    '''
    if attribute not in list(cds.data.keys()):
        return
    
    metric = np.array(cds.data.get(attribute), copy=True)
    #- TODO: add customizable clipping (percentiles, zmins, zmaxs)    
    pmin, pmax = np.percentile(metric, (2.5, 97.5))
    metric = np.clip(metric, pmin, pmax)
    
    xrange = (min(metric) * 0.99, max(metric) * 1.01)

    colors_for_metric(cds, attribute, metric)
    
    figs_list = []
    hfigs_list = []
    
    for c in cameras:
        fig, hfig = plot_fibers(cds, attribute, cam=c, percentile=percentiles.get(c),
                                zmin=zmins.get(c), zmax=zmaxs.get(c), 
                                title=titles.get(c, {}).get(attribute), tools=tools,
                                tooltips=tooltips, x_range=xrange)

        figs_list.append(fig)
        hfigs_list.append(hfig)
    figs = bk.gridplot([figs_list, hfigs_list], toolbar_location='right')
    script, div = components(figs)

    components_dict[attribute] = dict(script=script, div=div)


def colors_for_metric(cds, attribute, metric, num_bins=10):
    #- If the function is here, it provides the same range for the same attribute,
    #- rather than adjusting per camera
    #- TODO: document
    try:
        colors = get_colors(metric, palette=palettes.all_palettes['Paired'][num_bins])
    except RuntimeWarning as rw:
        print(attribute + ' get colors caused a truedivide error from get colors')
    colname = attribute + '_color'

    cds.add(colors, colname)
