import numpy as np
import jinja2
import bokeh
import desimodel.io

from bokeh.embed import components
from bokeh.layouts import gridplot, layout

import bokeh.plotting as bk
from bokeh.models import ColumnDataSource
from bokeh.models import Panel, Tabs
from astropy.table import Table, join, vstack, hstack

from ..plots.camfiber import plot_camfib_focalplate, plot_per_fibernum


def write_camfiber_html(outfile, data, header):
    '''
    Args:
        outfile : output directory for generated html file
        data : fits file of per_camfiber data
        header : fits file header

    Writes the default generated fibernum camfiber plots to OUTFILE
    Also generates and writes an alternate view of focalplate camfiber plots
    Returns a components dictionary of summary camfiber plots
    '''
    #- Default plot options
    ATTRIBUTES = ['INTEG_RAW_FLUX', 'MEDIAN_RAW_FLUX', 'MEDIAN_RAW_SNR', 'INTEG_CALIB_FLUX',
                 'MEDIAN_CALIB_FLUX', 'MEDIAN_CALIB_SNR']
    CAMERAS = ['B', 'R', 'Z']
    PERCENTILES = {'B':(0, 95), 'R':(0, 95), 'Z':(0, 98)}
    TITLES = {'INTEG_RAW_FLUX':'Integrated Raw Counts', 'MEDIAN_RAW_FLUX':'Median Raw Counts',
              'MEDIAN_RAW_SNR':'Median Raw S/N', 'INTEG_CALIB_FLUX':'Integrated Calibration Flux',
              'MEDIAN_CALIB_FLUX':'Median Calibration Flux', 'MEDIAN_CALIB_SNR':'Median Calibration S/N'}
    TITLESPERCAM = {'B':TITLES}
    TOOLS = 'pan,box_zoom,tap,reset'

    
    #- Sets environment to get get templates
    env = jinja2.Environment(
        loader=jinja2.PackageLoader('qqa.webpages', 'templates')
    )

    #- FIBERNUM PLOTS (default camfiber page)
    fn_template = env.get_template('fibernum.html')
    write_fibernum_plots(data, fn_template, outfile, header, ATTRIBUTES, CAMERAS, TITLESPERCAM, TOOLS)

    #- FOCALPLATE PLOTS
    index_fp_file = outfile.index('.html')
    fp_outfile = outfile[:index_fp_file] + '-focalplate_plots.html'
    fp_template = env.get_template('focalplate.html')
    write_focalplate_plots(data, fp_template, fp_outfile, header, ATTRIBUTES, CAMERAS, PERCENTILES, TITLESPERCAM, TOOLS)

    return dict({})


def write_fibernum_plots(data, template, outfile, header, ATTRIBUTES, CAMERAS, TITLESPERCAM, TOOLS):
    '''
    Args:
        data : fits file of per_camfiber data
        template : html template
        outfile : output directory for generated html file
        header : fits file header
        ATTRIBUTES : list of attributes to plot
        CAMERAS : list of camera filters to plot
        TITLESPERCAM : titles for plots
        TOOLS : supported features
        
    Writes the fibernum plots to OUTFILE
    '''
    #- Gets a shared ColumnDataSource of DATA
    cds = get_cds(data, ATTRIBUTES, CAMERAS)

    #- Gets the plot list for each metric in ATTRIBUTES
    fibernum_gridlist = []
    for attr in ATTRIBUTES:
        #- TODO: aggregation later (box and whisker) or binning
        if attr in list(cds.data.keys()):
            figs_list = plot_per_fibernum(cds, attr, CAMERAS, titles=TITLESPERCAM, tools=TOOLS)

            fibernum_gridlist.extend(figs_list)

    #- Organizes the layout of the plots
    fn_camfiber_layout = layout(fibernum_gridlist)

    #- Writes the htmlfile
    write_file = write_htmlfile(fn_camfiber_layout, template, outfile, header)


def write_focalplate_plots(data, template, outfile, header, ATTRIBUTES, CAMERAS, PERCENTILES, TITLESPERCAM, TOOLS):    
    '''
    Args:
        data : fits file of per_camfiber data
        template : html template
        outfile : output directory for generated html file
        header : fits file header
        ATTRIBUTES : list of attributes to plot
        CAMERAS : list of camera filters to plot
        PERCENTILES : list of percentiles to clip histogram data per camera
        TITLESPERCAM : titles for plots
        TOOLS : supported features
        
    Writes the focalplate plots to OUTFILE
    '''
    #- Gets a shared ColumnDataSource of DATA
    cds = get_cds(data, ATTRIBUTES, CAMERAS)

    #- Gets the plot list for each metric in ATTRIBUTES
    focalplate_gridlist = []
    for attr in ATTRIBUTES:
        if attr in list(cds.data.keys()):
            figs_list, hfigs_list = plot_camfib_focalplate(cds, attr, CAMERAS, percentiles=PERCENTILES,
                                     titles=TITLESPERCAM, tools=TOOLS)

            focalplate_gridlist.extend([figs_list, hfigs_list])

    #- Organizes the layout of the plots
    fp_camfiber_layout = gridplot(focalplate_gridlist, toolbar_location='right')

    #- Writes the htmlfile
    write_file = write_htmlfile(fp_camfiber_layout, template, outfile, header)



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
    return cds


def create_cds(data, attributes, bin_size=25):
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


def write_htmlfile(layout, template, outfile, header):
    '''
    Args:
        layout : bokeh layout object of plot figures
        template : html template
        outfile : outfile directory
        header : fits file header
    
    Writes the LAYOUT of plots to OUTFILE
    '''
    night = header['NIGHT']
    expid = header['EXPID']
    flavor = header['FLAVOR'].rstrip()
    if "PROGRAM" not in header :
        program = "no program in header!"
    else :
        program = header['PROGRAM'].rstrip()
    exptime = header['EXPTIME']

    components_dict = dict(
        bokeh_version=bokeh.__version__, exptime='{:.1f}'.format(exptime),
        night=night, expid=expid, zexpid='{:08d}'.format(expid),
        flavor=flavor, program=program, qatype = 'camfiber',
    )

    script, div = components(layout)
    components_dict['CAMFIBER_PLOTS'] = dict(script=script, div=div)
    html_camfib = template.render(**components_dict)

    #- Write HTML text to the output files
    with open(outfile, 'w') as fx:
        fx.write(html_camfib)
