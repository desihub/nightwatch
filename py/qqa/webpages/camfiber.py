import numpy as np
import jinja2
import bokeh
import desimodel.io

from bokeh.embed import components
from bokeh.layouts import layout

import bokeh.plotting as bk
from bokeh.models import ColumnDataSource
from astropy.table import Table, join, vstack#, hstack
from ..plots.core import get_size


from ..plots.fiber import plot_fibers
from ..plots.camfiber import plot_per_camfiber


def write_camfiber_html(outfile, data, header):
    '''
    Args:
        outfile : output directory for generated html file
        data : fits file of per_camfiber data
        header : fits file header

    Writes the generated plots to OUTFILE
    '''

    night = header['NIGHT']
    expid = header['EXPID']
    flavor = header['FLAVOR'].rstrip()
    if "PROGRAM" not in header :
        program = "no program in header!"
    else :
        program = header['PROGRAM'].rstrip()
    exptime = header['EXPTIME']

    env = jinja2.Environment(
        loader=jinja2.PackageLoader('qqa.webpages', 'templates')
    )
    template = env.get_template('camfiber.html')

    html_components = dict(
        bokeh_version=bokeh.__version__, exptime='{:.1f}'.format(exptime),
        night=night, expid=expid, zexpid='{:08d}'.format(expid),
        flavor=flavor, program=program, qatype = 'camfiber',
    )

    #- List of attributes to plot per camfiber with default arguments
    ATTRIBUTES = ['INTEG_RAW_FLUX', 'MEDIAN_RAW_FLUX', 'MEDIAN_RAW_SNR', 'INTEG_CALIB_FLUX',
                 'MEDIAN_CALIB_FLUX', 'MEDIAN_CALIB_SNR']
    #- Default cameras and percentile ranges for camfiber plots
    CAMERAS = ['B', 'R', 'Z']
    PERCENTILES = {'B':(0, 95), 'R':(0, 95), 'Z':(0, 98)}
    TITLES = {'INTEG_RAW_FLUX':'Integrated Raw Counts', 'MEDIAN_RAW_FLUX':'Median Raw Counts',
              'MEDIAN_RAW_SNR':'Median S/N', 'INTEG_CALIB_FLUX':'Integrated Calibration Flux',
              'MEDIAN_CALIB_FLUX':'Median Calibration Flux', 'MEDIAN_CALIB_SNR':
              'Median Calibration S/N'}
    TITLESPERCAM = {'B':TITLES}
    TOOLS = 'pan,box_select,reset'
    SCATTER = True

    #- Gets a shared ColumnDataSource of DATA
    cds = get_cds(data, ATTRIBUTES, CAMERAS, agg=SCATTER)

    #- Gets the gridplots for each metric in ATTRIBUTES
    gridlist = []
    for attr in ATTRIBUTES:
        metric_grid = plot_per_camfiber(cds, attr, CAMERAS, html_components, percentiles=PERCENTILES,
            titles=TITLESPERCAM, tools=TOOLS)
        gridlist.append(metric_grid)

    #- Organizes the layout of the plots
    camfiber_layout = layout(children=gridlist)

    #- Gets the html components of the camfiber plots
    script, div = components(camfiber_layout)
    html_components['METRIC_PLOTS'] = dict(script=script, div=div)

    #- Combine template + components -> HTML
    html = template.render(**html_components)

    #- Write HTML text to the output file
    with open(outfile, 'w') as fx:
        fx.write(html)

    return html_components


def get_cds(data, attributes, cameras, agg=False):
	'''
    Creates a column data source from DATA
    Args:
        data : a fits file of camfib data collected
        attributes : a list of metrics
        cameras : a list of cameras
    Options:
    	agg : get an aggregated column data source
    		to plot per fiber number instead of
    		focal plate

    Returns a bokeh ColumnDataSource object
    '''
    #- Get the positions of the fibers on the focal plane
    fiberpos = Table(desimodel.io.load_fiberpos())
    fiberpos.remove_column('SPECTRO')

    #- Join the metrics data with the corresponding fibers
    #- TODO: use input fibermap instead
    data = Table(data)
    if len(data) > 0:
        data = join(data, fiberpos, keys='FIBER')

    #- bytes vs. strings
    for colname in data.colnames:
        if data[colname].dtype.kind == 'S':
            data[colname] = data[colname].astype(str)

    if agg:
        data = aggregate_by_fibernums(data)
#       #- TODO: consider reshaping data into metric-camera combo columns
#       #- data = data_per_cam_metric(data, attributes, cameras)
#       #- data = agg_data_cds(data, attributes, cameras, agg_func=np.mean)

    cds = create_cds(data, attributes)

    return cds


def create_cds(data, attributes):
    '''
    Creates a column data source from DATA with metrics in ATTRIBUTES
    Args:
        data : an astropy table of camfib data collected
        attributes : a list of metrics
    '''
    data_dict = dict({})
    for colname in data.dtype.names:
        if colname in attributes:
            data_dict[colname] = data[colname].astype(np.float32)
        else:
            data_dict[colname] = data[colname]
    cds = ColumnDataSource(data=data_dict)

    return cds


def aggregate_by_fibernums(data):
    '''
    Bins DATA by fiber number by binning the data per camera
    and then vertically stacking them
    Args:
        data : a full astropy table of camfiber data

    Returns an astropy table object
    '''
    cams = ['B', 'R', 'Z']
    cam_stacks = []
    #- get the subtables for each camera
    for c in cams:
        c_table = bin_subtable(data, c)
        cam_stacks.append(c_table)

    return vstack(cam_stacks)

def bin_subtable(data, cam, agg_func=np.mean, num_bins=100):
    '''
    Aggregates DATA by fiber number into NUM_BINS to prevent overplotting
    Args:
        data : an astropy table of camfiber data filtered by CAM
        cam : a string representation of a camera filter (i.e. 'B', 'R', 'Z')
    Options:
        agg_func : function to use for aggregation
        num_bins : number of bins to aggregate into

    Returns an astropy table object
    '''
    #- Filters to only CAM data
    mask = np.char.upper(np.array(data['CAM'])) == cam.upper()
    data = data[mask]

    #- Generates bins
    fiber_bins = np.array(data['FIBER']) // num_bins
    data = data.group_by(fiber_bins)

    #- replaces the CAM, DEVICE_TYPE column at the end to avoid aggregation warnings
    #- from string columns
    data.remove_column('CAM')

    #- TODO: DEVICE_TYPE, CAM columns dropped
    data = data.groups.aggregate(agg_func)

    #- replaces the CAM, DEVICE_TYPE column
    data['CAM'] = cam
    #- redo the FIBER column to correspond to group numbers
    data['FIBER'] = np.array(data['FIBER']) // num_bins
    data['FIBER'] = data['FIBER'].astype(int)

    return data
