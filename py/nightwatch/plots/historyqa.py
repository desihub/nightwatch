
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

