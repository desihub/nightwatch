#import numpy as np
#import scipy as sp
#
#import bokeh
#import bokeh.plotting as bk
#from bokeh.models import LinearColorMapper, ColorBar, ColumnDataSource, HTMLTemplateFormatter, NumeralTickFormatter, OpenURL, TapTool, HoverTool, Label, FactorRange, Div, CustomJS, Slider, Image, Legend, Span
#from bokeh.transform import cumsum, transform
#from bokeh.layouts import column, gridplot, row
#from bokeh.colors import RGB
#from bokeh.models.widgets import NumberFormatter
#from bokeh.models.widgets.tables import DataTable, TableColumn
#
#import astropy
#from astropy.table import Table, join
#from astropy.io import fits as fits
#from astropy.time import Time, TimezoneInfo
#from datetime import datetime, tzinfo, timedelta
#import astropy.units as u
#from collections import Counter, OrderedDict
#from pathlib import PurePath
#

import numpy as np

import bokeh
import bokeh.plotting as bk
from bokeh.models import (
    ColumnDataSource, OpenURL, Div, Range1d, MonthsTicker,
    TapTool, HelpTool, HoverTool, Range1d, BoxAnnotation, ResetTool, BoxZoomTool,
    LinearColorMapper, ColorBar, Whisker, Band)
import bokeh.palettes
from bokeh.layouts import column, gridplot

from .timeseries import plot_timeseries

def plot_flats_timeseries(flats,
    camcolors=dict(B='steelblue', R='crimson', Z='forestgreen')):

    figs = []
    tooltips = None

    for cam in 'R':
        for spec in np.arange(10):
            name = f'{cam.lower()}_integ_flux'
            select = flats['spec'] == spec

            fig = bk.figure(width=800, height=300, x_axis_type='datetime',
                            y_axis_label=name.upper(),
                            y_range=Range1d(0, np.percentile(flats[name][select], 99.5), bounds=(0, None))
                )
            fig.xaxis.major_label_orientation = np.radians(45)
            fig.xaxis.ticker = MonthsTicker(months=np.arange(1,13), num_minor_ticks=4)
            fig.title.text = f'{cam}{spec}'
            fig.title.text_color = camcolors[cam]

            source = ColumnDataSource(data={'time'  : flats['time'][select],
                                            'expid' : flats['expid'][select],
                                            'spec'  : flats['spec'][select],
                                            f'{name}' : flats[name][select]})

#        fig = plot_timeseries(source, name, cam=cam)
            s = fig.scatter('time', name, source=source, color=camcolors[cam])

            #- Add hover tool
            if tooltips is None:
                tooltips = [('Time', '@time'),
                            ('Cam', f'{cam}@spec'),
                            ('INTEG_FLUX', f'@{name}')]
            hover = HoverTool(renderers=[s], tooltips=tooltips)
            fig.add_tools(hover)

            figs.append(fig)

    return column(figs)

