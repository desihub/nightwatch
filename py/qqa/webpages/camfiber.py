import numpy as np
import jinja2
import bokeh
import desimodel.io

from bokeh.embed import components
from bokeh.layouts import gridplot

import bokeh.plotting as bk
from bokeh.models import ColumnDataSource
from astropy.table import Table, join, vstack, hstack


from ..plots.fiber import plot_fibers, plot_fibernums
from ..plots.camfiber import plot_camfib_focalplate, plot_per_fibernum


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
    TOOLS = 'pan,box_zoom,reset'

    #- Gets a shared ColumnDataSource of DATA
    cds, agg_cds = get_cds(data, ATTRIBUTES, CAMERAS)

    #- Gets the layout for the fibernum plots
    fibernum_gridlist = []
    #- Gets the gridplots for each metric in ATTRIBUTES
    for attr in ATTRIBUTES:
        #- TODO: aggregation later (box and whisker) or binning
        if attr in list(cds.data.keys()):
            figs_list = plot_per_fibernum(cds, attr, CAMERAS, percentiles=PERCENTILES,
                                         titles=TITLESPERCAM, tools=TOOLS)

            fibernum_gridlist.extend(figs_list)

    #- Organizes the layout of the plots
    fn_camfiber_layout = gridplot(fibernum_gridlist, ncols=1, toolbar_location='above')

    #- Gets the html components of the fibernum plots
    script, div = components(fn_camfiber_layout)
    html_components['FIBERNUM_PLOTS'] = dict(script=script, div=div)
    #- Combine template + components -> HTML
    html_fibernum = template.render(**html_components)

    #- Write HTML text to the output file
    with open(outfile, 'w') as fx:
        fx.write(html_fibernum)


    focalplate_template = env.get_template('focalplate.html')
    #- Gets the layout for the focal plate plots
    focalplate_gridlist = []
    #- Gets the gridplots for each metric in ATTRIBUTES
    for attr in ATTRIBUTES:
        if attr in list(cds.data.keys()):
            figs_list, hfigs_list = plot_camfib_focalplate(cds, attr, CAMERAS, percentiles=PERCENTILES,
                                     titles=TITLESPERCAM, tools=TOOLS)

            focalplate_gridlist.extend([figs_list, hfigs_list])

    #- Organizes the layout of the plots
    fp_camfiber_layout = gridplot(focalplate_gridlist, toolbar_location='right')

    #- Gets the html components of the focalplate plots
    script, div = components(fp_camfiber_layout)
    html_components['FOCALPLATE_PLOTS'] = dict(script=script, div=div)
    #- Combine template + components -> HTML
    html_focalplate = focalplate_template.render(**html_components)

    #- Write HTML text to the output file
    print('outfile is ' + outfile)
    with open(outfile, 'w') as fx:
        print('will write focalplate plots')
        # fx.write(html_focalplate)


    agg_fibernum_template = env.get_template('agg_fibernum.html')
    #- Gets the layout for the focal plate plots
    aggfib_tabslist = []
    #- Gets the gridplots for each metric in ATTRIBUTES
    for attr in ATTRIBUTES:
        if attr in list(agg_cds.data.keys()):
            gplot = binned_boxplots_per_metric(agg_cds, attr, width=width, height=height)
            tab = Panel(child=gplot, title=attr)
            tabs_list.append(tab)

    #- Organizes the layout of the plots
    af_camfiber_layout = Tabs(tabs=aggfib_tabslist)

    #- Gets the html components of the focalplate plots
    script, div = components(af_camfiber_layout)
    html_components['AGGFIB_PLOTS'] = dict(script=script, div=div)
    #- Combine template + components -> HTML
    html_aggfib = agg_fibernum_template.render(**html_components)

    #- Write HTML text to the output file
    print('outfile is ' + outfile)
    with open(outfile, 'w') as fx:
        print('will write aggfib plots')
        # fx.write(html_aggfib)

    return html_components


def get_cds(data, attributes, cameras):
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

    cds = create_cds(data, attributes)
    agg_cds = aggregate_by_fibernums(data, attributes)
    return cds, agg_cds


def create_cds(data, attributes):
    '''
    Creates a column data source from DATA with metrics in ATTRIBUTES
    Args:
        data : an astropy table of camfib data collected
        attributes : a list of metrics
    '''
    data_dict = dict({})
    bins = np.array(np.array(data['FIBER']) // bin_size).astype(int)
    data['FIBER_BIN'] = bins

    for colname in data.dtype.names:
        if colname in attributes:
            data_dict[colname] = data[colname].astype(np.float32)
        else:
            data_dict[colname] = data[colname]

    cds = ColumnDataSource(data=data_dict)

    return cds



def aggregate_by_fibernums(data, metrics, num_bins=200):
    '''
    Bins DATA by fiber number by binning the data per camera
    and then vertically stacking them
    Args:
        data : a full astropy table of camfiber data
        metrics : a list of attributes
    Options:
        num_bins : number of bins to aggreate fibers into

    Returns an astropy table object
    '''
    #- Generates bins
    fiber_bins = np.array(data['FIBER']) // num_bins
    fiber_bins = fiber_bins.astype(int)
    data['FIBER_BINS'] = fiber_bins

    #- Only the metrics which are in the data
    metrics = [m for m in metrics if m in data.colnames]

    cameras = ['B', 'R', 'Z']
    data = camerastack(data, metrics, cameras)

    metrics = [["{}_{}".format(m, c) for c in cameras] for m in metrics]

    agg_cds = (data, metrics, num_bins=num_bins)
    return agg_cds



def camerastack(data, metrics, cams):
    cam_stacks = []
    #- get the metrics columns for each camera
    for c in cameras:
        c_table = rename_camcolumns(data, c, metrics)
        cam_stacks.append(c_table)
    data.remove_column('CAM')

    return hstack(cam_stacks)

def rename_camcolumns(data, cam, metrics):
    '''
    TODO: document
    '''
    #- Filters to only CAM data
    mask = np.char.upper(np.array(data['CAM'])) == cam.upper()
    data = data[mask]

    #- Chooses only the subset of columns which are metrics
    data = data[[metrics]]
    #- Renmaes the metrics columns to be camera specific
    for colname metrics:
        data.rename(colname, colname + "_" + cam)

    return data


def summarystats_metric(table, metric, num_bins=200):

    def get_outliers(metric_col, upper, lower):
        metric_col = np.array(metric_col)
        metric_outliers = metric_col[(metric_col > upper) | (metric_col < lower)]
        return metric_outliers

    full_metric_col = table['FIBER_BIN', metric]
    summary_stats = []
    for fiberbin in range(num_bins):
        #- get subtable rows
        subtable = full_metric_col[full_metric_col['FIBER_BIN'] == fiberbin]
        subcol = subtable[metric]

        #- get summary stats
        q1, q2, q3 = np.quantile(subcol, [0.25, 0.5, 0.75])
        iqr = q3 - q1
        upper = q3 + 1.5*iqr
        lower = q1 - 1.5*iqr

        #- get list of outliers
        metric_outliers = get_outliers(subcol, upper, lower)

        #- shrink stem size if no outliers
        upper = min(np.quantile(subcol, 1), upper)
        lower = max(np.quantile(subcol, 0), lower)

        summary = dict(q1=q1, q2=q2, q3=q3, iqr=iqr, upper=upper,
                       lower=lower, outliers=metric_outliers)
        summary_stats.append(summary)
    return summary_stats


def summarytable(agg_data_table, metrics, num_bins=200):
    agg_data = dict(FIBERNUM=np.arange(num_bins))

    for m in metrics:
        statsdict_list = summarystats_metric(agg_data_table, m, num_bins)
        agg_data[m] = statsdict_list

    agg_cds = ColumnDataSource(data=agg_data)
    return agg_cds
