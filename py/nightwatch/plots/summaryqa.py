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

#- Avoid warnings from date & coord calculations in the future
import warnings
warnings.filterwarnings('ignore', 'ERFA function.*dubious year.*')
warnings.filterwarnings('ignore', 'Tried to get polar motions for times after IERS data is valid.*')

def get_skyplot(exposures, tiles, width=500, height=250, min_border_left=50, min_border_right=50):
    '''
    Generates sky plot of DESI survey tiles and progress. Colorcoded by night each tile was first
    observed, uses nights_first_observed function defined previously in this module to retrieve
    night each tile was first observed.
    Args:
        exposures: Table of exposures with columns ...
        tiles: Table of tile locations with columns ...
    Options:
        width, height: plot width and height in pixels
        min_border_left, min_border_right: set minimum width for external labels in pixels
    Returns bokeh Figure object
    '''

    exposures_sorted = Table(np.sort(exposures, order='MJD'))
    tiles_sorted = Table(np.sort(tiles, order='TILEID'))
    
    source = ColumnDataSource(data=dict(
        RA = exposures_sorted['RA'],
        DEC = exposures_sorted['DEC'],
        NIGHT = exposures_sorted['NIGHT'],
        MJD = exposures_sorted['MJD'],
        EXPID = exposures_sorted['EXPID'],
    ))
    
    tiles_source = ColumnDataSource(data=dict(
        RA = tiles_sorted['RA'],
        DEC = tiles_sorted['DEC'],
        TILEID = tiles_sorted['TILEID']
    ))

    color_mapper = LinearColorMapper(palette="Viridis256", low=exposures_sorted['MJD'].min(), high=exposures_sorted['MJD'].max())

    #making figure
    fig = bk.figure(width=width, height=height, min_border_left=min_border_left, 
                    min_border_right=min_border_right, output_backend="webgl")

    #observed tiles
    tile_renderer = fig.circle('RA', "DEC", color='gray', size=1, alpha=0.1, source=tiles_source)
    renderer = fig.circle('RA', 'DEC', color=transform('MJD', color_mapper), size=7, alpha=0.5, source=source)
    #fig.line('RA', 'DEC', line_width=1, line_color='black', line_dash='dashed', alpha=0.5, source=source)
    color_bar = ColorBar(color_mapper=color_mapper, label_standoff=12, location=(0,0), title='MJD', width=5)
    fig.add_layout(color_bar, 'right')

    fig.xaxis.axis_label = 'RA [degrees]'
    fig.yaxis.axis_label = 'Declination [degrees]'
    fig.title.text = 'Observed Tiles, Nightly Progress'
    fig.grid.visible = False
    
    hover = HoverTool(
            tooltips="""
                <font face="Arial" size="0">
                <font color="blue"> RA: </font> @RA <br>
                <font color="blue"> DEC: </font> @DEC <br>
                <font color="blue"> NIGHT/EXPID: </font> @NIGHT / @EXPID
                </font>
            """, renderers = [renderer]
        )
    
#     tile_hover = HoverTool(
#             tooltips="""
#                 <font face="Arial" size="0">
#                 <font color="blue"> RA: </font> @RA <br>
#                 <font color="blue"> DEC: </font> @DEC <br>
#                 <font color="blue"> TILEID: </font> @TILEID
#                 </font>
#             """, renderers = [tile_renderer]
#         )

    fig.add_tools(hover)

    return fig

def get_median(attribute, exposures):
    '''Get the median value for a given attribute for all nights for all exposures taken each night.
    Input:
        attributes: one of the labels in the exposure column, string
        exposures: table with the exposures data
    Output:
        returns a numpy array of the median values for each night
    '''
    medians = []
    for n in np.unique(exposures['NIGHT']):
        ii = (exposures['NIGHT'] == n)
        attrib = np.asarray(exposures[attribute])[ii]
        medians.append(np.ma.median(attrib))  #- use masked median

    return np.array(medians)

def get_summarytable(exposures):
    '''
    Generates a summary table of key values for each night observed. Uses collections.Counter(), OrderedDict()
    Args:
        exposures: Table of exposures with columns...
    Returns a bokeh DataTable object.
    '''
    nights = np.unique(exposures['NIGHT'])

    isbright = (exposures['PROGRAM'] == 'BRIGHT')
    isgray = (exposures['PROGRAM'] == 'GRAY')
    isdark = (exposures['PROGRAM'] == 'DARK')
    iscalib = (exposures['PROGRAM'] == 'CALIB')

    num_nights = len(nights)
    brights = list()
    grays = list()
    darks = list()
    calibs = list()
    totals = list()
    for n in nights:
        thisnight = exposures['NIGHT'] == n
        totals.append(np.count_nonzero(thisnight))
        brights.append(np.count_nonzero(thisnight & isbright))
        grays.append(np.count_nonzero(thisnight & isgray))
        darks.append(np.count_nonzero(thisnight & isdark))
        calibs.append(np.count_nonzero(thisnight & iscalib))

    med_air = get_median('AIRMASS', exposures)
    med_seeing = get_median('SEEING', exposures)
    med_exptime = get_median('EXPTIME', exposures)
    med_transp = get_median('TRANSP', exposures)
    med_sky = get_median('SKY', exposures)
    med_angle = get_median('HOURANGLE', exposures)

    source = ColumnDataSource(data=dict(
        nights = list(nights),
        totals = totals,
        brights = brights,
        grays = grays,
        darks = darks,
        calibs = calibs,
        med_air = med_air,
        med_seeing = med_seeing,
        med_exptime = med_exptime,
        med_transp = med_transp,
        med_sky = med_sky,
        med_angle = med_angle,
    ))

    formatter = NumberFormatter(format='0,0.00')
    template_str = '<a href="nightqa-<%= nights %>.html"' + ' target="_blank"><%= value%></a>'

    columns = [
        TableColumn(field='nights', title='NIGHT', width=100, formatter=HTMLTemplateFormatter(template=template_str)),
        TableColumn(field='totals', title='Total', width=50),
        TableColumn(field='brights', title='Bright', width=50),
        TableColumn(field='grays', title='Gray', width=50),
        TableColumn(field='darks', title='Dark', width=50),
        TableColumn(field='calibs', title='Calibs', width=50),
        TableColumn(field='med_exptime', title='Median Exp. Time', width=100),
        TableColumn(field='med_air', title='Median Airmass', width=100, formatter=formatter),
        TableColumn(field='med_seeing', title='Median Seeing', width=100, formatter=formatter),
        TableColumn(field='med_sky', title='Median Sky', width=100, formatter=formatter),
        TableColumn(field='med_transp', title='Median Transparency', width=115, formatter=formatter),
        TableColumn(field='med_angle', title='Median Hour Angle', width=115, formatter=formatter),
    ]

    summary_table = DataTable(source=source, columns=columns, width=900, sortable=True, fit_columns=False)
    return summary_table

def get_hist(fine_data, attribute, color, width=250, height=250, min_border_left=50, min_border_right=50):
    '''
    Generates a histogram of the attribute provided for the given exposures table
    Args:
        exposures: Table of exposures with columns "PROGRAM" and attribute
        attribute: String; must be the label of a column in exposures
        color: String; color of the histogram
    Options:
        width, height: plot width and height in pixels
        min_border_left, min_border_right: set minimum width for external labels in pixels
    Returns bokeh Figure object
    '''
    #keep = exposures['PROGRAM'] != 'CALIB'
    #exposures_nocalib = exposures[keep]
    
    attr_data = np.array(fine_data[attribute])
    attr_data = attr_data[~np.isnan(attr_data)]

    hist, edges = np.histogram(attr_data, density=True, bins=25)

    fig = bk.figure(plot_width=width, plot_height=height,
                    x_axis_label = attribute.title(),
                    min_border_left=min_border_left, min_border_right=min_border_right,
                    title = 'title')

    fig.quad(top=hist, bottom=0, left=edges[:-1], right=edges[1:], fill_color=color, alpha=0.5)
    fig.toolbar_location = None
    fig.title.text_color = '#ffffff'
    fig.yaxis.major_label_text_font_size = '0pt'

    if attribute == 'TRANSP':
        fig.xaxis.axis_label = 'Transparency'

    if attribute == 'HOURANGLE':
        fig.xaxis.axis_label = 'Hour Angle'

    return fig

def get_exposuresPerTile_hist(exposures, color, width=250, height=250, min_border_left=50, min_border_right=50):
    '''
    Generates a histogram of the number of exposures per tile for the given
    exposures table
    Args:
        exposures: Table of exposures with column "TILEID"
        color: String; color of the histogram
    Options:
        width, height: plot width and height in pixels
        min_border_left, min_border_right: set minimum width for external labels in pixels
        min_border_left, min_border_right: set minimum width for external labels in pixels
    Returns bokeh Figure object
    '''
    keep = exposures['PROGRAM'] != 'CALIB'
    
    exposures_nocalib = exposures[keep]

    exposures_nocalib["ones"] = 1
    exposures_nocalib = exposures_nocalib["ones", "TILEID"]
    exposures_nocalib = exposures_nocalib.group_by("TILEID")
    exposures_nocalib = exposures_nocalib.groups.aggregate(np.sum)

    hist, edges = np.histogram(exposures_nocalib["ones"], density=True, bins=np.arange(0, np.max(exposures_nocalib["ones"])+1))

    fig = bk.figure(plot_width=width, plot_height=height,
                    x_axis_label = "# Exposures per Tile",
                    title = 'title',
                    min_border_left=min_border_left, min_border_right=min_border_right)
    fig.quad(top=hist, bottom=0, left=edges[:-1], right=edges[1:], fill_color=color, alpha=0.5)
    fig.toolbar_location = None
    fig.title.text_color = '#ffffff'
    fig.yaxis.major_label_text_font_size = '0pt'

    return fig