import numpy as np
import scipy as sp

import bokeh
import bokeh.plotting as bk
from bokeh.models import LinearColorMapper, ColorBar, ColumnDataSource, HTMLTemplateFormatter, NumeralTickFormatter, OpenURL, TapTool, HoverTool, Label, FactorRange, Div, CustomJS, Slider, Image, Legend, Span
from bokeh.transform import cumsum, transform
from bokeh.layouts import column, gridplot, row
from bokeh.colors import RGB
from bokeh.models.widgets import NumberFormatter
from bokeh.models.widgets.tables import DataTable, TableColumn

import astropy
from astropy.table import Table, join
from astropy.io import fits as fits
from astropy.time import Time, TimezoneInfo
from datetime import datetime, tzinfo, timedelta
import astropy.units as u
from collections import Counter, OrderedDict
from pathlib import PurePath

from .timeseries import plot_timeseries

def plot_flats_timeseries(flats):

    figs_list = []

    for cam in 'brz':
        name = f'{cam}_integ_flux'
        source = ColumnDataSource(data=dict(time=flats['time'], name=flats[name]))
        fig = plot_timeseries(source, name, cam=cam)

        figs_list.append(fig)

    return figs_list

