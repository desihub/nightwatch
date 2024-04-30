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

    x = list(range(11))
    y0 = x
    y1 = [10 - i for i in x]
    y2 = [abs(i - 5) for i in x]

    for cam in 'R':
        name = f'{cam.lower()}_integ_flux'

        fig = bk.figure(width=800, height=300, x_axis_type='datetime',
                        y_axis_label=name.upper(),
                        y_range=Range1d(0, np.percentile(flats[name], 99.5), bounds=(0, None))
            )
        fig.xaxis.major_label_orientation = np.radians(45)
        fig.xaxis.ticker = MonthsTicker(months=np.arange(1,13), num_minor_ticks=4)

        source = ColumnDataSource(data={'time' : flats['time'],
                                        'expid' : flats['expid'],
                                        'spec' : flats['spec'],
                                        f'{name}' : flats[name]})

#        fig = plot_timeseries(source, name, cam=cam)
        s = fig.scatter('time', name, source=source, color=camcolors[cam])

        figs.append(fig)

#    fig = bk.figure(width=700, height=200, x_axis_type='datetime')
##    fig.scatter(flats['time'], flats['b_integ_flux'])
#    source = ColumnDataSource(data={'time':flats['time'], 'expid':flats['expid'], 'b_integ_flux':flats['b_integ_flux']})
#    fig.scatter('time', 'b_integ_flux', source=source)

    print(flats['time'][:10], flats['b_integ_flux'][:10])
#    figs.append(fig)

    return column(figs)

