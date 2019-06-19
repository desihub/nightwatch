import numpy as np
import jinja2
import bokeh

from astropy.table import Table
import bokeh.plotting as bk
import bokeh.palettes as bp
from bokeh.transform import linear_cmap

from ..plots.fiber import plot_fibers, plot_fibernums
# from ..plots.core import get_colors


def plot_camfib_focalplate(cds, attribute, cameras, percentiles={},
                      zmaxs={}, zmins={}, titles={}, tools=None):
    '''
    ARGS:
        cds : ColumnDataSource of data
        attribute : string corresponding to column name in DATA
        cameras : list of string representing unique camera values

    Options:
        percentiles : dictionary of cameras corresponding to (min,max)
            to clip data
        zmaxs : dictionary of cameras corresponding to hardcoded max values
            to clip data
        zmins : dictionary of cameras corresponding to hardcoded min values
            to clip data
        titles : dictionary of titles per camera for a group of camfiber plots
            where key-value pairs represent a camera-attribute plot title
        tools, tooltips : supported plot interactivity features
    '''
    if attribute not in list(cds.data.keys()):
        raise ValueError('{} not in cds.data.keys'.format(attribute))

    metric = np.array(cds.data.get(attribute), copy=True)
    #- TODO: add customizable clipping (percentiles, zmins, zmaxs)

    #- adjusts for outliers on the full scale
    #- change back to (2.5, 97.5) for the middle 95% for real data...?
    pmin, pmax = np.percentile(metric, (0, 95))

    #- common scale for all histograms for this metric
    hist_x_range = (pmin * 0.99, pmax * 1.01)

    #- for hover tool
    attr_formatted_str = "@" + attribute + '{(0.00 a)}'
    tooltips = [("FIBER", "@FIBER"), ("(X, Y)", "(@X, @Y)"),
                (attribute, attr_formatted_str)]

    figs_list = []
    hfigs_list = []

    for i in range(len(cameras)):
        c = cameras[i]

        """
        TODO:
            are linked features supported on the version of bokeh on cori?
            because https://bokeh.pydata.org/en/latest/docs/user_guide/data.html#booleanfilter
            shows the same steps where the tools, column data source, and ranges are shared,
            but the output webpages do not seem to support the linked features
        """
        func = plot_fibers
        first_x_range = bokeh.models.Range1d(-420, 420)
        first_y_range = bokeh.models.Range1d(-420, 420)

        #- shared ranges to support linked features
        if not figs_list:
            fig_x_range = first_x_range
            fig_y_range = first_y_range
        else:
            fig_x_range = figs_list[0].x_range
            fig_y_range = figs_list[0].y_range

        if i == (len(cameras) - 1):
            colorbar = True
        else:
            colorbar = False

        fig, hfig = plot_fibers(cds, attribute, cam=c, percentile=percentiles.get(c),
                        zmin=zmins.get(c), zmax=zmaxs.get(c),
                        title=titles.get(c, {}).get(attribute),
                        tools=tools, hist_x_range=hist_x_range,
                        fig_x_range=fig_x_range, fig_y_range=fig_y_range,
                        colorbar=colorbar)

        figs_list.append(fig)
        hfigs_list.append(hfig)

    return figs_list, hfigs_list



def plot_per_fibernum(cds, attribute, cameras, percentiles={},
                      zmaxs={}, zmins={}, titles={}, tools=None):
    '''
    ARGS:
        cds : ColumnDataSource of data
        attribute : string corresponding to column name in DATA
        cameras : list of string representing unique camera values

    Options:
        percentiles : dictionary of cameras corresponding to (min,max)
            to clip data
        zmaxs : dictionary of cameras corresponding to hardcoded max values
            to clip data
        zmins : dictionary of cameras corresponding to hardcoded min values
            to clip data
        titles : dictionary of titles per camera for a group of camfiber plots
            where key-value pairs represent a camera-attribute plot title
        tools, tooltips : supported plot interactivity features
    '''
    if attribute not in list(cds.data.keys()):
        return

    metric = np.array(cds.data.get(attribute), copy=True)
    #- TODO: add customizable clipping (percentiles, zmins, zmaxs)

    #- adjusts for outliers on the full scale
    #- change back to (2.5, 97.5) for the middle 95% for real data...?
    pmin, pmax = np.percentile(metric, (0, 95))

    #- common scale for all histograms for this metric
    hist_x_range = (pmin * 0.99, pmax * 1.01)

    #- for hover tool
    attr_formatted_str = "@" + attribute + '{(0.00 a)}'
    tooltips = [("FIBER", "@FIBER"), ("(X, Y)", "(@X, @Y)"),
                (attribute, attr_formatted_str)]

    figs_list = []

    for i in range(len(cameras)):
        c = cameras[i]

        """
        TODO:
            are linked features supported on the version of bokeh on cori?
            because https://bokeh.pydata.org/en/latest/docs/user_guide/data.html#booleanfilter
            shows the same steps where the tools, column data source, and ranges are shared,
            but the output webpages do not seem to support the linked features
        """
        min_fiber = min(cds.data['FIBER'])
        max_fiber = min(cds.data['FIBER'])
        first_x_range = bokeh.models.Range1d(min_fiber-1, max_fiber-1)
        # first_y_range = None

        #- shared ranges to support linked features
        if not figs_list:
            fig_x_range = first_x_range
            # fig_y_range = first_y_range
        else:
            fig_x_range = figs_list[0].x_range
            # fig_y_range = figs_list[0].y_range

        fig = plot_fibernums(cds, attribute, cam=c, percentile=percentiles.get(c),
                        zmin=zmins.get(c), zmax=zmaxs.get(c),
                        title=titles.get(c, {}).get(attribute), tools=tools,
                        tooltips=tooltips, toolbar_location=None,
                        hist_x_range=hist_x_range, fig_x_range=fig_x_range,
                        )

        figs_list.append(fig)

    return figs_list
