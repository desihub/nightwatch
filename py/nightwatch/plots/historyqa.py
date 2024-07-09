
import numpy as np

import bokeh
import bokeh.plotting as bk
from bokeh.models import (
    ColumnDataSource, OpenURL, Div, Range1d, MonthsTicker,
    TapTool, HelpTool, HoverTool, Range1d, BoxAnnotation, ResetTool, BoxZoomTool,
    LinearColorMapper, ColorBar, Whisker, Band)
from bokeh.models.widgets import Panel, Tabs
import bokeh.palettes
from bokeh.layouts import column, gridplot

from .timeseries import plot_timeseries


def plot_camera_timeseries(camdata, spec,
    camcolors=dict(B='steelblue', R='crimson', Z='forestgreen')):
    """Produce time series of CCD QA values using DB data.

    Args
        ccds : ndarray containing CCD QA data
        spec : spectrograph 0-9
        camcolors : dict with color data

    Returns
        tabs : Tabs with columns of camera QA plots.
    """
    camtabs = []

    #- Loop over metrics
    for metric, label in zip([('meandx', 'mindx', 'maxdx'),
                              ('meandy', 'mindy', 'maxdy')],
                             ['Δx: Fiber', 'Δy: Wavelength']):

        figs = []

        #- Loop over cameras
        for cam in 'brz':
            select = camdata['cam'] == cam.upper()

            #- Set up plot limit such that 0 is centered in the plot.
            limit = 1.1*np.maximum(np.abs(np.min(camdata[metric[1]][select])),
                                   np.abs(np.max(camdata[metric[2]][select])))

            fig = bk.figure(width=800, height=300, x_axis_type='datetime',
                            y_axis_label=f'{label} (pixels)',
                            y_range=Range1d(-limit, limit, bounds=(-1, None)),
                            tools=['pan', 'box_zoom', 'reset', 'tap']
                            )
            fig.xaxis.major_label_orientation = np.radians(45)
            fig.xaxis.ticker = MonthsTicker(months=np.arange(1,13), num_minor_ticks=4)
            fig.title.text = f'{cam.upper()}{spec}'
            fig.title.text_color = camcolors[cam.upper()]

            source = ColumnDataSource(data={'time'  : camdata['time'][select],
                                            'expid' : camdata['expid'][select],
                                            'night' : camdata['night'][select],
                                            f'{metric[0]}' : camdata[metric[0]][select],
                                            f'{metric[1]}' : camdata[metric[1]][select],
                                            f'{metric[2]}' : camdata[metric[2]][select]})

            #- Add scatterplot with error bars (whisker plot)
            s = fig.scatter('time', metric[0], source=source, color=camcolors[cam.upper()], alpha=0.3)

            error = Whisker(base='time', upper=metric[2], lower=metric[1], source=source, level='annotation', line_color=camcolors[cam.upper()], line_width=1, line_alpha=0.5)
            error.upper_head.size=2
            error.upper_head.line_color=camcolors[cam.upper()]
            error.upper_head.line_alpha=0.5
            error.lower_head.size=2
            error.lower_head.line_color=camcolors[cam.upper()]
            error.lower_head.line_alpha=0.5

            fig.add_layout(error)

            #- Add hover tool
            fig.add_tools(HoverTool(
                tooltips = [('night', '@night'),
                            ('expid', '@expid'),
                            (f'{metric[0]}', f'@{metric[0]}')],
                renderers = [s]
            ))

            #- Add tap tool
            taptool = fig.select(type=TapTool)
            taptool.behavior = 'select'
            taptool.callback = OpenURL(url='../@night/00@expid/qa-camera-00@expid.html')

            #- Store figures in list for column display
            figs.append(fig)

        #- Add figures to columns and columns to a camera panel.
        col = column(figs)
        tab = Panel(child=col, title=f'{label}')
        camtabs.append(tab)

    return Tabs(tabs=camtabs)


def plot_ccd_timeseries(ccds, cam, spec,
    camcolors=dict(B='steelblue', R='crimson', Z='forestgreen')):
    """Produce time series of CCD QA values using DB data.

    Args
        ccds : ndarray containing CCD QA data
        cam : camera string ('b', 'r', 'z').
        spec : spectrograph 0-9
        camcolors : dict with color data

    Returns
        tabs : Tabs with columns of CCD QA results.
    """
    ccdtabs = []

    #- Loop over metrics
    for metric, label in zip(['readnoise', 'bias', 'cosmic_rate'],
                             ['Read Noise', 'Overscan Bias', 'Cosmic Rate']):

        figs = []
        
        #- Loop over amplifiers
        for amp in 'ABCD':
            select = ccds['amp'] == amp

            scale = 4 if metric=='cosmic_rate' else 2

            fig = bk.figure(width=800, height=300, x_axis_type='datetime',
                            y_axis_label=label,
                            y_range=Range1d(-1, scale*np.median(ccds[metric][select]), bounds=(-1, None)),
                            tools=['pan', 'box_zoom', 'reset', 'tap']
                            )
            fig.xaxis.major_label_orientation = np.radians(45)
            fig.xaxis.ticker = MonthsTicker(months=np.arange(1,13), num_minor_ticks=4)
            fig.title.text = f'{cam.upper()}{spec}{amp}'
            fig.title.text_color = camcolors[cam.upper()]

            source = ColumnDataSource(data={'time'  : ccds['time'][select],
                                            'expid' : ccds['expid'][select],
                                            'night' : ccds['night'][select],
                                            f'{metric}' : ccds[metric][select]})

            s = fig.scatter('time', metric, source=source, color=camcolors[cam.upper()], alpha=0.3)

            #- Add hover tool
            fig.add_tools(HoverTool(
                tooltips = [('night', '@night'),
                            ('expid', '@expid'),
                            (f'{metric}', f'@{metric}')],
                renderers = [s]
            ))

            #- Add tap tool
            taptool = fig.select(type=TapTool)
            taptool.behavior = 'select'
            taptool.callback = OpenURL(url='../@night/00@expid/qa-amp-00@expid.html')

            #- Store figures in list for column display
            figs.append(fig)

        #- Add figures to columns and columns to a camera panel.
        col = column(figs)
        tab = Panel(child=col, title=f'{label}')
        ccdtabs.append(tab)

    return Tabs(tabs=ccdtabs)


def plot_flats_timeseries(flats,
    camcolors=dict(B='steelblue', R='crimson', Z='forestgreen')):
    """Produce time series of flat exposures using DB data.

    Args
        flats : ndarray containing calibration fluxes.
        camcolors : dict with color data.

    Returns
        tabs : Tabs with columns of LED flat calibrations.
    """
    #- Loop over all cameras
    camtabs = []

    for cam in 'brz':
        figs = []

        #- Loop over all spectrographs
        for spec in np.arange(10):
            name = f'{cam}_integ_flux'
            select = flats['spec'] == spec

            fig = bk.figure(width=800, height=300, x_axis_type='datetime',
                            y_axis_label=name.upper(),
                            y_range=Range1d(-1, np.median(flats[name][select]) + 2*np.std(flats[name][select]), bounds=(-1, None)),
                            tools=['pan', 'box_zoom', 'reset', 'tap']
                            )
            fig.xaxis.major_label_orientation = np.radians(45)
            fig.xaxis.ticker = MonthsTicker(months=np.arange(1,13), num_minor_ticks=4)
            fig.title.text = f'{cam}{spec}'
            fig.title.text_color = camcolors[cam.upper()]

            source = ColumnDataSource(data={'time'  : flats['time'][select],
                                            'expid' : flats['expid'][select],
                                            'night' : flats['night'][select],
                                            'spec'  : flats['spec'][select],
                                            f'{name}' : flats[name][select]})

            s = fig.scatter('time', name, source=source, color=camcolors[cam.upper()])

            #- Add hover tool
            fig.add_tools(HoverTool(
                tooltips = [('night', '@night'),
                            ('expid', '@expid'),
                            ('cam', f'{cam}@spec'),
                            ('INTEG_FLUX', f'@{name}')],
                renderers = [s]
            ))

            #- Add tap tool
            taptool = fig.select(type=TapTool)
            taptool.behavior = 'select'
            taptool.callback = OpenURL(url='../@night/00@expid/qa-spectro-00@expid.html')

            #- Store figures in list for column display
            figs.append(fig)

        #- Add figures to columns and columns to a camera panel.
        col = column(figs)
        tab = Panel(child=col, title=f'{cam} Flats')
        camtabs.append(tab)

    return Tabs(tabs=camtabs)


def plot_arcs_timeseries(arcs, lines, lamps,
    camcolors=dict(B='steelblue', R='crimson', Z='forestgreen')):
    """Produce time series of arc line widths using DB data.

    Args
        arcs : ndarray containing calibration fluxes.
        lines : list of arc lines
        lamps : list of arc lamps
        camcolors : dict with color data.

    Returns
        tabs : Tabs with columns of LED flat calibrations.
    """
    #- Loop over all lines
    linetabs = []

    for line, lamp in zip(lines, lamps):
        name = line
        cam = line[0].upper()

        figs = []

        #- Loop over all spectrographs
        for spec in np.arange(10):
            select = arcs['spec'] == spec

            fig = bk.figure(width=800, height=300, x_axis_type='datetime',
                            y_axis_label=f'{name.upper()} integrated flux',
                            y_range=Range1d(-1, np.median(arcs[name][select]) + 2*np.std(arcs[name][select]), bounds=(-1, None)),
                            tools=['pan', 'box_zoom', 'reset', 'tap']
                            )
            fig.xaxis.major_label_orientation = np.radians(45)
            fig.xaxis.ticker = MonthsTicker(months=np.arange(1,13), num_minor_ticks=4)
            fig.title.text = f'{cam}{spec}'
            fig.title.text_color = camcolors[cam.upper()]

            source = ColumnDataSource(data={'time'  : arcs['time'][select],
                                            'expid' : arcs['expid'][select],
                                            'night' : arcs['night'][select],
                                            'spec'  : arcs['spec'][select],
                                            f'{name}' : arcs[name][select]})

            s = fig.scatter('time', name, source=source, color=camcolors[cam.upper()])

            #- Add hover tool
            fig.add_tools(HoverTool(
                tooltips = [('night', '@night'),
                            ('expid', '@expid'),
                            ('cam', f'{cam}@spec'),
                            ('linewidth', f'@{name}')],
                renderers = [s]
            ))

            #- Add tap tool
            taptool = fig.select(type=TapTool)
            taptool.behavior = 'select'
            taptool.callback = OpenURL(url='../@night/00@expid/qa-spectro-00@expid.html')

            #- Store figures in list for column display
            figs.append(fig)

        #- Add figures to columns and columns to a camera panel.
        col = column(figs)
        tab = Panel(child=col, title=f'λ{line[1:]} ({lamp})')
        linetabs.append(tab)

    return Tabs(tabs=linetabs)

