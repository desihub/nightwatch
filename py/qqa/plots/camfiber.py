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


def plot_per_camfiber(data, attribute, cameras, components_dict, percentiles={}, 
                      zmaxs={}, zmins={}, titles={}):
    '''
    ARGS:
        data : 
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
    if attribute not in data.dtype.names:
        return

    figs_list = []
    hfigs_list = []
    for c in cameras:
        fig, hfig = plot_fibers(data, attribute, cam=c, percentile=percentiles.get(c, None),
            zmin=zmins.get(c), zmax=zmaxs.get(c), title=titles.get(c, {}).get(attribute))
        figs_list.append(fig)
        hfigs_list.append(hfig)
    figs = bk.gridplot([figs_list, hfigs_list], toolbar_location='right')
    script, div = components(figs)

    components_dict[attribute] = dict(script=script, div=div)
