from __future__ import absolute_import, division, print_function

import numpy as np
import bokeh as bk

import jinja2
from bokeh.embed import components
import bokeh
import bokeh.plotting as bk
from bokeh.models import ColumnDataSource

from astropy.time import Time
from bokeh.models import HoverTool, ColorBar
from bokeh.layouts import gridplot
from astropy.table import join
from astropy.time import TimezoneInfo
import astropy.units as u
from datetime import tzinfo
from datetime import datetime
from bokeh.models.glyphs import HBar
from bokeh.models import LabelSet, FactorRange
from bokeh.palettes import viridis
from bokeh.transform import factor_cmap
from bokeh.models.widgets.tables import DataTable, TableColumn
from astropy import coordinates
from bokeh.models.widgets import NumberFormatter
from pathlib import PurePath

import warnings
warnings.filterwarnings('ignore', 'ERFA function.*dubious year.*')
warnings.filterwarnings('ignore', 'Tried to get polar motions for times after IERS data is valid.*')

utc_offset = -7*u.hour

def find_night(exposures, night):
    """
    Generates a subtable of exposures corresponding to data from a single night N and adds column TIME
    ARGS:
        exposures : Table of exposures with columns...
        night : String representing a single value in the NIGHT column of the EXPOSURES table
    Returns an astropy table object
    """
    #- Filters by NIGHT
    exposures = exposures[exposures['NIGHT'] == night]

    #- Creates DateTime objects in Arizona timezone
    mjds = np.array(exposures['MJD'])
    times = [(Time(mjd, format='mjd', scale='utc') + utc_offset).to_datetime() for mjd in mjds]

    #- Adds times to table
    exposures['TIME'] = times

    return exposures


def get_timeseries(cds, name):
    """
    Generates times and values arrays for column `name`
    ARGS:
        cds : ColumnDataSource of exposures
        name : String corresponding to a column in CDS
    Returns numpy array objects
    """
    x = np.array(cds.data['TIME'])
    y = np.array(cds.data[name])

    return x, y

def plot_timeseries(source, name, color, tools=None, x_range=None, title=None, tooltips=None, width=400, height=150, min_border_left=50, min_border_right=50):
    """
    Plots values corresponding to NAME from SOURCE vs. time with TOOLS
    ARGS:
        source : ColumnDataSource of exposures
        name : string name of this timeseries
        color : color for plotted data points
        x_range : a range of x values to link multiple plots together
    Options:
        height, width: height and width of the graph in pixels
        x_range: x-axis range of the graph
        tools: interactive features
        title: graph title
        min_border_left, min_border_right: set minimum width of surrounding labels (in pixels)
    Returns bokeh figure object
    """

    times, values = get_timeseries(source, name)

    fig = bk.figure(width=width, height=height, tools=tools,
                    x_axis_type='datetime', x_range=x_range,
                    active_scroll='wheel_zoom', title=title,
                    x_axis_label='Time', output_backend="webgl",
                    min_border_left=min_border_left,
                    min_border_right=min_border_right)
    fig.xaxis.axis_label_text_color='#ffffff'
    fig.line('TIME', name, source=source)
    r = fig.circle('TIME', name, line_color=color, fill_color='white',
                   size=6, line_width=2, hover_color='firebrick', source=source)

    #- Formatting
    fig.xgrid.grid_line_color = None
    fig.outline_line_color = None
    fig.yaxis.axis_label = name.title()

    if name == 'TRANSP':
        fig.yaxis.axis_label = 'Transparency'
    if name == 'HOURANGLE':
        fig.yaxis.axis_label = 'Hour Angle'
    if name == 'EXPTIME':
        fig.yaxis.axis_label = 'Exposure Time'

    #- Add hover tool
    hover = HoverTool(renderers = [r], tooltips=tooltips)
    fig.add_tools(hover)

    return fig

def plot_timeseries_fine(fine_data_src, exposures_src, name, color, tools=None, x_range=None, title=None, tooltips=None, width=400, height=150, min_border_left=50, min_border_right=50):
    
#     source = ColumnDataSource(data=dict(
#         time = fine_data['TIME'],
#         attr = fine_data[name]
#     ))
    
#     exp_source = ColumnDataSource(data=dict(
#         time = exposures['TIME'],
#         med_attr = exposures[name]
#     ))
    
    fig =  bk.figure(plot_height=height, plot_width=width, 
                     x_range=x_range, x_axis_type='datetime',
                     active_scroll='wheel_zoom', title=title,
                     x_axis_label='Time', min_border_left=min_border_left,
                     min_border_right=min_border_right, output_backend="webgl")
    fig.circle('TIME', name, size=2, alpha=0.25, color=color, source=fine_data_src)
    medians = fig.circle('TIME', name, size=8, line_color=color, fill_color='white', 
                         source=exposures_src, hover_color='firebrick', line_width=2)
    
    #formatting
    fig.xgrid.grid_line_color = None
    fig.outline_line_color = None
    fig.yaxis.axis_label = name.title()
    
    if name == 'TRANSP':
        fig.yaxis.axis_label = 'Transparency'
    if name == 'HOURANGLE':
        fig.yaxis.axis_label = 'Hour Angle'
         
    hover = HoverTool(renderers = [medians], tooltips = tooltips)
    fig.add_tools(hover)
    
    return fig
    

def get_nightlytable(exposures):
    '''
    Generates a summary table of the exposures from the night observed.
    Args:
        exposures: Table of exposures with columns...
    Returns a bokeh DataTable object.
    '''

    source = ColumnDataSource(data=dict(
        expid = np.array(exposures['EXPID']),
        flavor = np.array(exposures['FLAVOR'], dtype='str'),
        exptime = np.array(exposures['EXPTIME']),
        tileid = np.array(exposures['TILEID']),
        airmass = np.array(exposures['AIRMASS']),
        seeing = np.array(exposures['SEEING']),
        transp = np.array(exposures['TRANSP']),
        sky = np.array(exposures['SKY']),
        hourangle = np.array(exposures['HOURANGLE'])
    ))

    formatter = NumberFormatter(format='0,0.00')
    columns = [
        TableColumn(field='expid', title='Exposure ID'),
        TableColumn(field='flavor', title='Flavor'),
        TableColumn(field='exptime', title='Exposure Time'),
        TableColumn(field='tileid', title='Tile ID'),
        TableColumn(field='airmass', title='Airmass', formatter=formatter),
        TableColumn(field='seeing', title='Seeing', formatter=formatter),
        TableColumn(field='transp', title='Transparency', formatter=formatter),
        TableColumn(field='sky', title='Sky', formatter=formatter),
        TableColumn(field='hourangle', title='Hour Angle', formatter=formatter)
    ]

    nightly_table = DataTable(source=source, columns=columns, width=1000, sortable=True)

    return nightly_table

def get_moonloc(night):
    """
    Returns the location of the moon on the given NIGHT
    Args:
        night : night = YEARMMDD of sunset
    Returns a SkyCoord object
    """
    #- Re-formats night into YYYY-MM-DD HH:MM:SS
    iso_format = night[:4] + '-' + night[4:6] + '-' + night[6:] + ' 00:00:00'
    t_midnight = Time(iso_format, format='iso') + 24*u.hour
    #- Sets timezone
    t_local = t_midnight + (-7)*u.hour

    #- Sets location
    kitt = coordinates.EarthLocation.of_site('Kitt Peak National Observatory')

    #- Gets moon coordinates
    moon_loc = coordinates.get_moon(time=t_local, location=kitt)

    return moon_loc

def get_skypathplot(exposures, tiles, night, width=600, height=300, min_border_left=50, min_border_right=50):
    """
    Generate a plot which maps the location of tiles observed on NIGHT
    ARGS:
        exposures : Table of exposures with columns specific to a single night
        tiles: Table of tile locations with columns ...
        night: int
    Options:
        height, width: height and width of the graph in pixels
        min_border_left, min_border_right: set minimum width of surrounding labels (in pixels)
    Returns a bokeh figure object
    """
    #- Converts data format into ColumnDataSource
    src = ColumnDataSource(data={'RA':np.array(exposures['RA']),
                                 'DEC':np.array(exposures['DEC']),
                                 'EXPID':np.array(exposures['EXPID']),
                                 'PROGRAM':np.array([str(n) for n in exposures['PROGRAM']])})

    #- Plot options
    string_date = str(night)[4:6] + "-" + str(night)[6:] + "-" + str(night)[:4]

    fig = bk.figure(width=width, height=height, title='Tiles observed on ' + string_date,
                    min_border_left=min_border_left, min_border_right=min_border_right)
    fig.yaxis.axis_label = 'Declination (degrees)'
    fig.xaxis.axis_label = 'Right Ascension (degrees)'

    #- Plots all tiles
    unobs = fig.circle(tiles['RA'], tiles['DEC'], color='gray', size=1, alpha=0.1)

    #- Plots tiles observed on NIGHT
    obs = fig.scatter('RA', 'DEC', size=5, fill_alpha=0.7, source=src)
    fig.line(src.data['RA'], src.data['DEC'], color='navy', alpha=0.4)

    #- Stars the first point observed on NIGHT
    try:
        ra = src.data['RA']
        dec = src.data['DEC']
        fig.asterisk(ra[0], dec[0], size=10, line_width=1.5, fill_color=None, color='orange')
    except:
        print('No data for {night}'.format(night=night))

    #- Adds moon location at midnight on NIGHT
#     night = str(exposures['NIGHT'][0])
#     moon_loc = get_moonloc(night)
#     ra, dec = float(moon_loc.ra.to_string(decimal=True)), float(moon_loc.dec.to_string(decimal=True))
#     fig.circle(ra, dec, size=10, color='gold')


    #- Circles the first point observed on NIGHT
#     first = exposures[0]
#     fig.asterisk(first['RA'], first['DEC'], size=10, line_width=1.5, fill_color=None, color='gold')

    #- Adds hover tool
    TOOLTIPS = [("(RA, DEC)", "(@RA, @DEC)"), ("EXPID", "@EXPID")]
    obs_hover = HoverTool(renderers = [obs], tooltips=TOOLTIPS)
    fig.add_tools(obs_hover)

    return fig

def overlaid_hist(all_exposures, night_exposures, attribute, color, width=300, height=150, min_border_left=50, min_border_right=50):
    """
    Generates an overlaid histogram for a single attribute comparing the distribution
    for all of the exposures vs. those from just one night
    ARGS:
        all_exposures : a table of all the science exposures
        night_exposures : a table of all the science exposures for a single night
        attribute : a string name of a column in the exposures tables
        color : color of histogram
    Options:
        height, width: height and width of the graph in pixels
        min_border_left, min_border_right: set minimum width of surrounding labels (in pixels)
    Returns a bokeh figure object
    """
    all_attr = np.array(all_exposures[attribute])
    night_attr = np.array(night_exposures[attribute])
    
    all_attr = all_attr[~np.isnan(all_attr)]
    night_attr = night_attr[~np.isnan(night_attr)]
    
    hist_all, edges_all = np.histogram(all_attr, density=True, bins=25)
    hist_night, edges_night = np.histogram(night_attr, density=True, bins=25)

    fig = bk.figure(plot_width=width, plot_height=height,
                    x_axis_label = attribute.title(), y_axis_label = 'title',
                    min_border_left=min_border_left, min_border_right=min_border_right)
    fig.quad(top=hist_all, bottom=0, left=edges_all[:-1], right=edges_all[1:], fill_color=color, alpha=0.2)
    fig.quad(top=hist_night, bottom=0, left=edges_night[:-1], right=edges_night[1:], fill_color=color, alpha=0.6)

    if attribute == 'TRANSP':
        fig.xaxis.axis_label = 'Transparency'
    if attribute == 'HOURANGLE':
        fig.xaxis.axis_label = 'Hour Angle'
    if attribute == 'EXPTIME':
        fig.xaxis.axis_label = 'Exposure Time'

    fig.yaxis.major_label_text_font_size = '0pt'
    fig.yaxis.major_tick_line_color = None
    fig.yaxis.minor_tick_line_color = None
    fig.yaxis.axis_label_text_color = '#ffffff'
    fig.ygrid.grid_line_color = None
    fig.xgrid.grid_line_color = None
    fig.toolbar_location = None

    return fig

def overlaid_hist_fine(all_data, night_data, attribute, color, width=300, height=150, min_border_left=50, min_border_right=50):
    """
    Generates an overlaid histogram for a single attribute comparing the distribution
    for all of the exposures vs. those from just one night
    ARGS:
        all_data : a table of all the exposures + finer data
        night_data : a table of all the exposures + finer data for a single night
        attribute : a string name of a column in the exposures tables
        color : color of histogram
    Options:
        height, width: height and width of the graph in pixels
        min_border_left, min_border_right: set minimum width of surrounding labels (in pixels)
    Returns a bokeh figure object
    """
    all_attr = np.array(all_data[attribute])
    night_attr = np.array(night_data[attribute])
    
    all_attr = all_attr[~np.isnan(all_attr)]
    night_attr = night_attr[~np.isnan(night_attr)]
    
    hist_all, edges_all = np.histogram(all_attr, density=True, bins=25)
    hist_night, edges_night = np.histogram(night_attr, density=True, bins=25)

    fig = bk.figure(plot_width=width, plot_height=height,
                    x_axis_label = attribute.title(), y_axis_label = 'title',
                    min_border_left=min_border_left, min_border_right=min_border_right)
    fig.quad(top=hist_all, bottom=0, left=edges_all[:-1], right=edges_all[1:], fill_color=color, alpha=0.2)
    fig.quad(top=hist_night, bottom=0, left=edges_night[:-1], right=edges_night[1:], fill_color=color, alpha=0.6)

    if attribute == 'TRANSP':
        fig.xaxis.axis_label = 'Transparency'
    if attribute == 'HOURANGLE':
        fig.xaxis.axis_label = 'Hour Angle'
    if attribute == 'EXPTIME':
        fig.xaxis.axis_label = 'Exposure Time'

    fig.yaxis.major_label_text_font_size = '0pt'
    fig.yaxis.major_tick_line_color = None
    fig.yaxis.minor_tick_line_color = None
    fig.yaxis.axis_label_text_color = '#ffffff'
    fig.ygrid.grid_line_color = None
    fig.xgrid.grid_line_color = None
    fig.toolbar_location = None

    return fig

def get_exptype_counts(exposures, calibs, width=300, height=300, min_border_left=50, min_border_right=50):
    """
    Generate a horizontal bar plot showing the counts for each type of
    exposure grouped by whether they have FLAVOR='science' or PROGRAM='calib'
    ARGS:
        exposures : a table of exposures which only contain those with FLAVOR='science'
        calibs : a table of exposures which only contains those with PROGRAm='calibs'
    Options:
        height, width: height and width in pixels
        min_border_left, min_border_right = set minimum width of surrounding labels (in pixels)
    """
    darks = len(exposures[exposures['PROGRAM'] == 'DARK'])
    grays = len(exposures[exposures['PROGRAM'] == 'GRAY'])
    brights = len(exposures[exposures['PROGRAM'] == 'BRIGHT'])

    arcs = len(calibs['arc' in calibs['FLAVOR']])
    flats = len(calibs['flat' in calibs['FLAVOR']])
    zeroes = len(calibs['zero' in calibs['FLAVOR']])

    types = [('calib', 'ZERO'), ('calib', 'FLAT'), ('calib', 'ARC'),
            ('science', 'BRIGHT'), ('science', 'GRAY'), ('science', 'DARK')]
    counts = np.array([zeroes, flats, arcs, brights, grays, darks])
    COLORS = ['tan', 'orange', 'yellow', 'green', 'blue', 'red']

    src = ColumnDataSource({'types':types, 'counts':counts})

    p = bk.figure(width=width, height=height,
                   x_range=(0, np.max(counts)*1.15),
                  y_range=FactorRange(*types), title='Exposure Type Counts',
                  toolbar_location=None, min_border_left=min_border_left, min_border_right=min_border_right)
    p.hbar(y='types', right='counts', left=0, height=0.5, line_color='white',
           fill_color=factor_cmap('types', palette=COLORS, factors=types), source=src)


    labels = LabelSet(x='counts', y='types', text='counts', level='glyph', source=src,
                      render_mode='canvas', x_offset=5, y_offset=-7,
                      text_color='gray', text_font='tahoma', text_font_size='8pt')
    p.add_layout(labels)

    p.ygrid.grid_line_color=None
    p.xaxis.axis_label = 'label'
    p.xaxis.axis_label_text_color = '#ffffff'

    return p