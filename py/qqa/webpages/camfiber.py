import numpy as np
import jinja2
import bokeh
import desimodel.io

from bokeh.embed import components
from bokeh.layouts import gridplot

import bokeh.plotting as bk
from bokeh.models import ColumnDataSource
from astropy.table import Table, join, vstack


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
    cds = get_cds(data, ATTRIBUTES, CAMERAS)

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
    fn_camfiber_layout = gridplot(fibernum_gridlist, ncols=1)

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
    fp_camfiber_layout = gridplot(gridlist, toolbar_location='right')

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
