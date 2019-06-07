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
        tools, tooltips : supported plot interactivity features

    ***MUTATES ARGUMENT
    Updates COMPONENTS_DICT to include key-value pairs to the html components
        for camfib attribute plot-bokeh gridplot object
    '''
    if attribute not in list(cds.data.keys()):
        return
    
    metric = np.array(cds.data.get(attribute), copy=True)
    #- TODO: add customizable clipping (percentiles, zmins, zmaxs)    
    
    hist_x_range = (min(metric) * 0.99, max(metric) * 1.01)
    
    figs_list = []
    hfigs_list = []
    
    for i in range(len(cameras)):
        c = cameras[i]
        if i == 0:
            plate_x_range = bokeh.models.Range1d(-420, 420)
            plate_y_range = bokeh.models.Range1d(-420, 420)
        else:
            plate_x_range = figs_list[0].x_range
            plate_y_range = figs_list[0].y_range

        fig, hfig = plot_fibers(cds, attribute, cam=c, percentile=percentiles.get(c),
                        zmin=zmins.get(c), zmax=zmaxs.get(c), 
                        title=titles.get(c, {}).get(attribute), tools=tools,
                        tooltips=tooltips, hist_x_range=hist_x_range,
                        plate_x_range=plate_x_range, plate_y_range=plate_y_range)

        figs_list.append(fig)
        hfigs_list.append(hfig)
    figs = bk.gridplot([figs_list, hfigs_list], toolbar_location='right')
    script, div = components(figs)

    components_dict[attribute] = dict(script=script, div=div)
