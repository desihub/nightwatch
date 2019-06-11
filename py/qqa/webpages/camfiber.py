import numpy as np

import jinja2

import bokeh
import bokeh.plotting as bk
from bokeh.embed import components

from ..plots.fiber import plot_fibers
from ..plots.camfiber import plot_per_camfiber
import desimodel.io
from bokeh.models import ColumnDataSource
from astropy.table import Table, join, vstack#, hstack


from ..plots.core import get_size


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

    #- TODO: delete
    #print('before plots: html_components dict size is ' + str(get_size(html_components)))

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
    TOOLS = ['pan','box_select','reset']
    SCATTER = True

    #- Gets a shared ColumnDataSource of DATA
    cds = get_cds(data, ATTRIBUTES, CAMERAS, scatter=SCATTER)

    #- TODO: delete
    #print('cds size is ' + str(get_size(cds)))


    #- Gets the html components for each camfib plot in ATTRIBUTES
    for attr in ATTRIBUTES:
        plot_per_camfiber(cds, attr, CAMERAS, html_components, percentiles=PERCENTILES,
            titles=TITLESPERCAM, tools=TOOLS, scatter_fibernum=SCATTER)

    #- Combine template + components -> HTML
    html = template.render(**html_components)

    #- TODO: delete
    #print('html size is ' + str(get_size(html)))
    #print('html dict size is ' + str(get_size(html_components)))

    #- Write HTML text to the output file
    with open(outfile, 'w') as fx:
        fx.write(html)

    return html_components


def get_cds(data, attributes, cameras, scatter=False):
    '''
    Creates a column data source from DATA
    Args:
        data : a fits file of camfib data collected
        attributes : a list of metrics

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

    if scatter:
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



# def agg_data_cds(data, attributes, cameras, agg_func=np.mean):
#     '''
#     Aggregates the data by fiber position into 50 groups of 10 using AGG_FUNC
#     Args:
#         data : an astropy table of camfib data collected
#         attributes : a list of metrics
#         cameras : a list of camera filters
#     Options:
#         agg_func : the aggregation function

#     Returns an astropy table object from DATA binned by fiber num
#     '''
#     fiber_bins = np.array(data['FIBER']) // 100
#     data = data.group_by(fiber_bins)

#     '''TODO: DEVICE_TYPE, CAM columns dropped'''
#     data = data.groups.aggregate(agg_func)

#     return data

# def data_per_cam_metric(t, attributes, cameras):
#     '''
#     Generates a table which reorganizes DATA so it has a column
#         for each metric-camera combo in ATTRIBUTES-CAMERAS
#     Args:
#         data : an astropy table of camfib data collected
#         attributes : a list of metrics
#         cameras : a list of camera filters

#     Returns an astropy table object
#     '''
#     #- get the metrics for each camera
#     cam_stacks = [get_metrics_for_cam(t, c, attributes) for c in cameras]

#     #- get the nonmetric columns
#     single_cam = filter_by_cam(t, cameras[0])
#     non_metrics = get_nonmetric_table(single_cam)

#     #- horizontally stack the tables
#     stacks = [non_metrics] + cam_stacks
#     by_cam = hstack(stacks)

#     return by_cam

# def get_metrics_for_cam(t, cam, attributes):
#     '''
#     Generates a table of columns corresponding to a specific
#         CAM-ATTRIBUTE combination from T
#     Args:
#         t : a full astropy table of camfiber data
#         cam : a string representation of a camera filter
#             (i.e. 'B', 'R', 'Z')
#         attributes : a list of metrics to include in the new table

#     Returns an astropy table object
#     '''
#     #- only select the subset of rows measured by camera
#     t = filter_by_cam(t, cam)
#     #- only get the metrics columns
#     t = t[attributes]
#     #- renames the columns to have the form metric_cam
#     for colname in t.colnames:
#         t.rename_column(colname, colname + "_" + cam)

#     return t

# def filter_by_cam(t, cam):
#     '''
#     Filters T by CAM
#     Args:
#         t : an astropy table of camfib data
#         cam : a string representation of a camera filter
#             (i.e. 'B', 'R', 'Z')

#     Returns an astropy table object
#     '''
#     #- selects the row indices of t which corresond to cam
#     mask = np.char.upper(np.array(t['CAM'])) == cam.upper()
#     return t[mask]

# def get_nonmetric_table(t):
#     '''
#     Generates a table corresponding to the non-metric columns
#     TODO: check, it should be determined based on each fiber as the primary key
#     Args:
#         t : an astropy table of camfiber data filtered to a single camera

#     Returns an astropy table object
#     '''
#     #- a list of columns to include in this table
#     cols = ['NIGHT', 'EXPID', 'SPECTRO', 'FIBER', 'PETAL', 'DEVICE',
#                   'DEVICE_TYPE', 'LOCATION', 'X', 'Y', 'Z', 'Q', 'S', 'SLIT',
#                   'SLITBLOCK', 'BLOCKFIBER', 'POSITIONER', 'SPECTROGRAPH']

#     nonmetric_cols = []

#     for col in t.colnames:
#         if col in cols:
#             nonmetric_cols.append(col)

#     return t[nonmetric_cols]
