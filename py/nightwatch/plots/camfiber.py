import numpy as np
import jinja2
import bokeh

from astropy.table import Table
import bokeh
import bokeh.plotting as bk
import bokeh.palettes as bp
from bokeh.models import TapTool, OpenURL

from ..plots.fiber import plot_fibers_focalplane, plot_fibernums
# from ..plots.core import get_colors


def plot_camfib_focalplane(cds, attribute, cameras, percentiles={},
                      zmaxs={}, zmins={}, titles={},
                      tools='pan,box_zoom,reset'):
    '''
    ARGS:
        cds : ColumnDataSource of data
        attribute : string corresponding to column name in DATA
        cameras : list of string representing unique camera values

    Options:
        percentiles : dictionary of cameras corresponding to (min,max)
            to clip data for histogram
        zmaxs : dictionary of cameras corresponding to hardcoded max values
            to clip data for histogram
        zmins : dictionary of cameras corresponding to hardcoded min values
            to clip data for histogram
        titles : dictionary of titles per camera for a group of camfiber plots
            where key-value pairs represent a camera-attribute plot title
        tools, tooltips : supported plot interactivity features
    '''
    if attribute not in list(cds.data.keys()):
        raise ValueError('{} not in cds.data.keys'.format(attribute))

    metric = np.array(cds.data.get(attribute), copy=True)

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

        fig, hfig = plot_fibers_focalplane(cds, attribute, cam=c,
                        percentile=percentiles.get(c),
                        zmin=zmins.get(c), zmax=zmaxs.get(c),
                        title=titles.get(c, {}).get(attribute),
                        tools=tools, hist_x_range=hist_x_range,
                        fig_x_range=fig_x_range, fig_y_range=fig_y_range,
                        colorbar=colorbar)

        figs_list.append(fig)
        hfigs_list.append(hfig)

    return figs_list, hfigs_list


def plot_camfib_fot(cds, attribute, cameras, percentiles={},
                      zmaxs={}, zmins={}, titles={},
                      tools='pan,box_zoom,reset'):
    '''
    ARGS:
        cds : ColumnDataSource of data
        attribute : string corresponding to column name in DATA
        cameras : list of string representing unique camera values

    Options:
        percentiles : dictionary of cameras corresponding to (min,max)
            to clip data for histogram
        zmaxs : dictionary of cameras corresponding to hardcoded max values
            to clip data for histogram
        zmins : dictionary of cameras corresponding to hardcoded min values
            to clip data for histogram
        titles : dictionary of titles per camera for a group of camfiber plots
            where key-value pairs represent a camera-attribute plot title
        tools, tooltips : supported plot interactivity features
    '''
    if attribute not in list(cds.data.keys()):
        raise ValueError('{} not in cds.data.keys'.format(attribute))

    metric = np.array(cds.data.get(attribute), copy=True)

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

        first_x_range = bokeh.models.Range1d(-420, 420)
        first_y_range = bokeh.models.Range1d(-420, 420)

        #- shared ranges to support linked features
        if not figs_list:
            fig_x_range = first_x_range
            fig_y_range = first_y_range
        else:
            fig_x_range = figs_list[0].x_range
            fig_y_range = figs_list[0].y_range

        fig, hfig = plot_fibers_focalplane(cds, attribute, cam=c,
                        percentile=percentiles.get(c),
                        zmin=zmins.get(c), zmax=zmaxs.get(c),
                        title=titles.get(c, {}).get(attribute),
                        palette = list(np.flip(bp.YlGnBu[5])),
                        tools=tools, hist_x_range=hist_x_range,
                        fig_x_range=fig_x_range, fig_y_range=fig_y_range,
                        colorbar=False, on_target=True)

        figs_list.append(fig)


    return figs_list

def plot_camfib_posacc(pcd,attribute,percentiles={},
                      tools='pan,box_zoom,reset'):

    figs_list = []
    hfigs_list = []
    metric = np.array(pcd.data.get(attribute), copy=True)
    metric = metric[np.where(metric>0)] #removed nan values
    pmin, pmax = np.percentile(metric, (0, 95))
    hist_x_range = (pmin * 0.99, pmax * 1.01)

    if attribute == 'BLIND':
        title = "Max Blind Move: {:.2f}um".format(np.max(metric))
        upper_cmap = 200
    elif attribute == 'FINAL_MOVE':
        title = 'RMS Final Move: {:.2f}um'.format(np.sqrt(np.square(metric).mean()))
        upper_cmap = 30


    attr_formatted_str = "@" + attribute + '{(0.00 a)}'
    tooltips = [("FIBER", "@FIBER"), ("(X, Y)", "(@X, @Y)"),
                (attribute, attr_formatted_str)]


    first_x_range = bokeh.models.Range1d(-420, 420)
    first_y_range = bokeh.models.Range1d(-420, 420)

    if not figs_list:
        fig_x_range = first_x_range
        fig_y_range = first_y_range
    else:
        fig_x_range = figs_list[0].x_range
        fig_y_range = figs_list[0].y_range

    c = '' # So not to change plot_fibers_focalplane code
    fig, hfig = plot_fibers_focalplane(pcd, attribute,cam=c, 
                        percentile=percentiles.get(c),
                        palette = bp.Magma256,
                        upper_cmap=upper_cmap,
                        title=title,
                        tools=tools, hist_x_range=hist_x_range,
                        fig_x_range=fig_x_range, fig_y_range=fig_y_range,
                        colorbar=True)

    figs_list.append(fig)
    hfigs_list.append(hfig)
    return figs_list, hfigs_list


def plot_per_fibernum(cds, attribute, cameras, titles={},
        tools='pan,box_zoom,tap,reset', width=700, height=80,
        ymin=None, ymax=None):
    '''
    ARGS:
        cds : ColumnDataSource of data
        attribute : string corresponding to column name in DATA
        cameras : list of string representing unique camera values
        width : width of individual camera plots in pixels
        height : height of individual camera plots in pixels
        ymin/ymax : y-axis ranges unless data exceed those ranges

    Options:
        titles : dictionary of titles per camera for a group of camfiber plots
            where key-value pairs represent a camera-attribute plot title
        tools, tooltips : supported plot interactivity features
    '''
    if attribute not in list(cds.data.keys()):
        return

    metric = np.array(cds.data.get(attribute), copy=True)

    #- adjusts for outliers on the full scale
    #- change back to (2.5, 97.5) for the middle 95% for real data...?
    pmin, pmax = np.percentile(metric, (0, 95))

    #- for hover tool
    attr_formatted_str = "@" + attribute + '{(0.00 a)}'
    tooltips = [("FIBER", "@FIBER"), ("(X, Y)", "(@X, @Y)"),
                (attribute, attr_formatted_str)]

    figs_list = []

    for i in range(len(cameras)):
        c = cameras[i]

        min_fiber = max(0, min(list(cds.data['FIBER'])))
        max_fiber = min(5000, max(list(cds.data['FIBER'])))
        first_x_range = bokeh.models.Range1d(min_fiber-1, max_fiber+1)

        #- shared ranges to support linked features, additional plot features
        if i == 0:
            fig_x_range = first_x_range
            toolbar_location='above'
            heightpad = 25 #- extra space for title & toolbar
        else:
            fig_x_range = figs_list[0].x_range
            toolbar_location=None
            heightpad = 0
        
        #- axis labels for the last camera
        if i == (len(cameras) - 1):
            xaxislabels = True
            heightpad = 50
        else:
            xaxislabels = False
        
        #- focused y-ranges unless outliers in data
        cam_metric = metric[np.array(cds.data.get('CAM')) == c]

        if len(cam_metric) == 0:
            #- create a blank plot as a placeholder
            fig = bokeh.plotting.figure(plot_width=width, plot_height=height)
            figs_list.append(fig)
            continue

        plotmin = min(ymin, np.min(cam_metric) * 0.9) if ymin else np.min(cam_metric) * 0.9
        plotmax = max(ymax, nnp.max(cam_metric) * 1.1) if ymax else np.max(cam_metric) * 1.1

        fig_y_range = bokeh.models.Range1d(plotmin, plotmax)

        
        fig = plot_fibernums(cds, attribute, cam=c, title=titles.get(c, {}).get(attribute),
                             tools=tools,tooltips=tooltips, toolbar_location=toolbar_location,
                             fig_x_range=fig_x_range, fig_y_range=fig_y_range,
                             width=width, height=height+heightpad, xaxislabels=xaxislabels,
                            )

        taptool = fig.select(type=TapTool)
        taptool.callback = OpenURL(url="spectra/input/@FIBER/qframe/4x/")
        figs_list.append(fig)
        
    return figs_list
