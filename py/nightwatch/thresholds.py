import sys, os, re 
import numpy as np
import json
import csv
from astropy.table import Table, vstack
import fitsio

import bokeh.plotting as bk
from bokeh.layouts import gridplot, column, row
from bokeh.models import TapTool as TapTool
from bokeh.models import OpenURL, ColumnDataSource, HoverTool, CustomJS, Span, Band, BoxAnnotation, ResetTool, BoxZoomTool
from nightwatch.qa.base import QA
from bokeh.models.widgets import DataTable, TableColumn, NumberFormatter

def get_outdir():
    '''Retrieve the path to the threshold_files directory within nightwatch by finding the user's python path.'''
    nightwatch_path = ''
    user_paths = os.environ['PYTHONPATH'].split(os.pathsep)
    for path in user_paths:
        if 'nightwatch' in path:
            nightwatch_path += path
    nightwatch_path += '/nightwatch/threshold_files'
    return nightwatch_path

def write_threshold_json(indir, outdir, start_date, end_date, name):
    '''
    Inputs:
        indir: contains summary.json files for each night (str)
        outdir: where the thresholds files should be generated (str)
        start_date, end_date: range over which thresholds should be calculated (int)
        name: the metric thresholds are being generated for (str)
    Output:
        writes a json file containing the thresholds per amp to the nightwatch/threshold_files directory
        (NOTE: if amp is not in previous nights summary files, the thresholds generated 
        will be None and will need to be manually input if they need to be used)'''
    datadict = dict()
    amps = []
    rest_amps = []
    nights = np.arange(start_date, end_date+1)
    nights_real = [night for night in nights if os.path.isfile(os.path.join(indir, '{night}/summary.json'.format(night=night)))]
    for night in nights_real:
        with open(os.path.join(indir,'{night}/summary.json'.format(night=night))) as json_file:
            data = json.load(json_file)
        if name in ["READNOISE"]:
            # amps += data['PER_AMP'][name].keys()
            all_amps = [cam+spec+amp for spec in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'] for cam in ['B', 'R', 'Z'] for amp in ['A', 'B', 'C', 'D']]
            # rest_amps += list(np.setdiff1d(all_amps, amps))
        if name in ["BIAS"]:
            amps += data['PER_AMP'][name].keys()
            all_amps = [cam+spec+amp for spec in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'] for cam in ['B', 'R', 'Z'] for amp in ['A', 'B', 'C', 'D']]
            rest_amps += list(np.setdiff1d(all_amps, amps))
        datadict[night] = data
    thresholds = dict()
    if name in ["READNOISE"]:
        for amp in all_amps:
            ampnom = datadict[night]['PER_AMP']['READNOISE_NOM_ZERO']
            # add functionality for nom/min, zero/dark
            thresholds[amp] = dict(upper_err=ampnom+1, upper=ampnom+0.5, lower=ampnom-0.5, lower_err=ampnom-1)
    if name in ["BIAS"]:
        for amp in all_amps:
            num_exps = []
            meds = []
            stds = []
            if amp in amps:
                for night in nights_real:
                    if amp in list(datadict[night]['PER_AMP'][name].keys()):
                        meds.append(datadict[night]['PER_AMP'][name][amp]['median'])
                        stds.append(datadict[night]['PER_AMP'][name][amp]['std'])
                        num_exps.append(datadict[night]['PER_AMP'][name][amp]['num_exp'])
                    else:
                        continue
                weights = np.array(num_exps)/np.sum(num_exps)
                med_avg = np.average(meds, weights=weights)
                std_avg = np.average(stds, weights=weights)
                upper_err = med_avg + 5*std_avg
                upper = med_avg + 3*std_avg
                lower = med_avg - 3*std_avg
                lower_err = med_avg - 5*std_avg
                thresholds[amp] = dict(upper_err=upper_err, upper=upper, lower=lower, lower_err=lower_err)
            if amp in rest_amps:
                thresholds[amp] = dict(upper_err=4.5, upper=4, lower=1.5, lower_err=1)
    if name in ['COSMICS_RATE']:
        for cam in ['R', 'B', 'Z']:
            num_exps = []
            lower_error = []
            lower = []
            upper = []
            upper_error = []
            for night in nights_real:
                lower_error.append(datadict[night]['PER_AMP'][name][cam]['lower_error'])
                lower.append(datadict[night]['PER_AMP'][name][cam]['lower'])
                upper.append(datadict[night]['PER_AMP'][name][cam]['upper'])
                upper_error.append(datadict[night]['PER_AMP'][name][cam]['upper_error'])
                num_exps.append(datadict[night]['PER_AMP'][name][cam]['num_exp'])
            weights = np.array(num_exps)/np.sum(num_exps)
            lower_err_avg = np.average(lower_error, weights=weights)
            lower_avg = np.average(lower, weights=weights)
            upper_avg = np.average(upper, weights=weights)
            upper_err_avg = np.average(upper_error, weights=weights)
            thresholds[cam] = dict(lower_err=lower_err_avg, lower=lower_avg, upper=upper_avg, upper_err=upper_err_avg)
    if name in ['DX', 'DY', 'XSIG', 'YSIG']:
        for cam in ['R', 'B', 'Z']:
            num_exps = []
            mins = []
            maxs = []
            meds = []
            for night in nights_real:
                mins.append(abs(datadict[night]['PER_CAMERA'][name][cam]['mind']))
                maxs.append(abs(datadict[night]['PER_CAMERA'][name][cam]['maxd']))
                meds.append(abs(datadict[night]['PER_CAMERA'][name][cam]['med']))
                num_exps.append(datadict[night]['PER_CAMERA'][name][cam]['num_exp'])
            weights = np.array(num_exps)/np.sum(num_exps)
            min_avg = -np.average(mins, weights=weights)
            max_avg = np.average(maxs, weights=weights)
            med_lower = -abs(np.average(meds, weights=weights))
            med_upper = abs(np.average(meds, weights=weights))
            thresholds[cam] = dict(lower_err=min_avg, lower=med_lower, upper=med_upper, upper_err=max_avg)
    #outdir = get_outdir()
    threshold_file = os.path.join(outdir, '{name}-{night}.json'.format(name=name, night=end_date+1))
    with open(threshold_file, 'w') as json_file:
         json.dump(thresholds, json_file, indent=4)
    print('Wrote {}'.format(threshold_file))

def pick_threshold_file(name, night, outdir=None, in_nightwatch=True):
    '''Picks the right threshold file to use given the metric and the night. If no file is found, it returns
    the earliest file.
    Arguments:
        name: metric thresholds are needed for (str)
        night: the night the thresholds are needed for (int)
    Options:
        outdir: specify where to look for threshold files
        in_nightwatch: tells function to look in nightwatch module for threshold files
    Output:
        filepath: a path to the proper threshold file'''
    file = '{name}-{night}.json'.format(name=name, night=night)
    
    if in_nightwatch:
        threshold_dir = get_outdir()
    if not in_nightwatch and outdir is not None:
        threshold_dir = outdir
    
    filepath = ''
    files = [f for f in np.sort(os.listdir(threshold_dir)) if name in f]
    
    for f in files:
        if str(night) in f:
            filepath += os.path.join(threshold_dir, file)    
    if filepath == '':
        filepath += os.path.join(threshold_dir, files[0])
    
    return filepath

def get_thresholds(filepath, return_keys=None):
    '''Unpack threshold values to use in plotting amp graphs
    Arguments:
        filepath: the path to the threshold file being unpacked
    Options:
        return_keys: if True, returns in addition to the lower and upper threshold lists,
        a list of the amps that had thresholds associated with them (not None). If none, does nothing
    Output:
        lower: [lowerB, lowerR, lowerZ] returns the lower thresholds for cam B, R, Z amps concatenated
        upper: [upperB, upperR, upperZ] returns the upper thresholds for cam B, R, Z amps concatenated
        real_keys: see return_key option'''
    with open(filepath, 'r') as json_file:
        threshold_data = json.load(json_file)
    keys = threshold_data.keys()
    lowerB = []
    lower_errB = []
    upperB = []
    upper_errB = []
    real_keysB = []
    lowerZ = []
    lower_errZ = []
    upperZ = []
    upper_errZ = []
    real_keysZ = []
    lowerR = []
    lower_errR = []
    upperR = []
    upper_errR = []
    real_keysR = []
    for key in keys:
        if key[0] == 'B':
            lowerB.append(threshold_data[key]['lower'])
            upperB.append(threshold_data[key]['upper'])
            lower_errB.append(threshold_data[key]['lower_err'])
            upper_errB.append(threshold_data[key]['upper_err'])
            real_keysB.append(key)
        if key[0] == 'Z':
            lowerZ.append(threshold_data[key]['lower'])
            upperZ.append(threshold_data[key]['upper'])
            lower_errZ.append(threshold_data[key]['lower_err'])
            upper_errZ.append(threshold_data[key]['upper_err'])
            real_keysZ.append(key)
        if key[0] == 'R':
            lowerR.append(threshold_data[key]['lower'])
            upperR.append(threshold_data[key]['upper'])
            lower_errR.append(threshold_data[key]['lower_err'])
            upper_errR.append(threshold_data[key]['upper_err'])
            real_keysR.append(key)
        else:
            continue
    lower = [[lower_errB, lowerB], [lower_errR, lowerR], [lower_errZ, lowerZ]]
    upper = [[upperB, upper_errB], [upperR, upper_errR], [upperZ, upper_errZ]]
    real_keys = [real_keysB, real_keysR, real_keysZ]
    
    if return_keys:
        return lower, upper, real_keys
    if return_keys == None:
        return lower, upper 

def get_timeseries_dataset(data_dir, start_date, end_date, hdu, aspect, filepath):
    '''reuses the timeseries function for the flask app, but with some changes. 
    Inputs:
        data_dir: directory of nights, where data_dir/NIGHT/EXPID/qa-EXPID.fits files can be found.
        start_date: starting date for range over which timeseries should be generated
        end_date: last date for range over which timeseries should be generated
        hdu: the level of qa metric. ex: PER_AMP, PER_CAM, PER_CAMFIBER. currently, only PER_AMP supported
        aspect: the metric being plotted. ex: READNOISE, BIAS, COSMICS_RATE
        filepath: threshold file to be used
    Output:
        source_data: a list of dictionaries with per_amp data. Each element contains keywords [EXPID, EXPIDZ, NIGHT,
        aspect_data, CAM, lower, upper]'''
    
    start_date = str(start_date).zfill(8)
    end_date = str(end_date).zfill(8)

    list_tables = []

    avaliable_dates = []
    i,j,y = os.walk(data_dir).__next__()
    for dir in j:
        if (start_date <= dir and end_date >= dir):
            avaliable_dates += [os.path.join(i, dir)]

    for date in avaliable_dates:
        for i,j,y in os.walk(date):
            for file in y:
                if re.match(r"qa-[0-9]{8}.fits", file):
                    #print(Table(os.path.join(i, file)).info())
                    try:
                        list_tables += [Table.read(os.path.join(i, file), hdu=hdu)]
                        #list_tables += [fitsio.read(os.path.join(i, file), hdu, columns=list(QA.metacols[hdu])+[aspect])]
                    except Exception as e:
                        print("{} does not have desired hdu or column".format(file))

    if list_tables == []:
        return None
    table = vstack(list_tables, metadata_conflicts='silent')
#     table = None
#     for tab in list_tables:
#         if table is None:
#             table = tab
#         else:
#             table = np.append(table, tab)
#     table = Table(table)
    table.sort("EXPID") # axis

    metacols = QA.metacols

    group_by_list = list(metacols[hdu])
    group_by_list.remove("NIGHT")
    group_by_list.remove("EXPID")
    if group_by_list == []:
        table_by_amp = table
    else:
        table_by_amp = table.group_by(group_by_list).groups.aggregate(list)

    #filepath = pick_threshold_file(aspect, end_date)
    with open(filepath, 'r') as json_file:
        threshold_data = json.load(json_file)
    source_data = [0]*120
    if "CAM" in table_by_amp.colnames:
        colors = {"B":"blue", "R":"red", "Z":"green"}
        group_by_list.remove("CAM")
        for cam in ["B", "R", "Z"]:
            cam_table = table_by_amp[table_by_amp["CAM"] == cam]
            for row in cam_table:
                length = len(row["EXPID"])
                #print(row[aspect])
                data=dict(
                    EXPID = row["EXPID"],
                    EXPIDZ = [str(expid).zfill(8) for expid in row["EXPID"]],
                    NIGHT = row["NIGHT"],
                    aspect_values = row[aspect],
                    CAM = row['CAM'],
                )
                amp = cam + str(row['SPECTRO']) + row['AMP']
                amps = []
                amps.append(amp)
                if aspect in ['READNOISE', 'BIAS']:
                    data['lower_err'] = [threshold_data[amp]['lower_err']]*length
                    data['lower'] = [threshold_data[amp]['lower']]*length
                    data['upper'] = [threshold_data[amp]['upper']]*length
                    data['upper_err'] = [threshold_data[amp]['upper_err']]*length
                if aspect in ['COSMICS_RATE']:
                    data['lower_err'] = [threshold_data[cam]['lower_err']]*length
                    data['lower'] = [threshold_data[cam]['lower']]*length
                    data['upper'] = [threshold_data[cam]['upper']]*length
                    data['upper_err'] = [threshold_data[cam]['upper_err']]*length
                for col in group_by_list:
                    data[col] = [str(row[col])]*length
                source_data[get_amp_rows(amps)[0]] = data         
    else:
        for row in table_by_amp:
            length = len(row["EXPID"])
            data=dict(
                EXPID = row["EXPID"],
                EXPIDZ = [str(expid).zfill(8) for expid in row["EXPID"]],
                NIGHT = row["NIGHT"],
                aspect_values = row[aspect]
            )
            for col in group_by_list:
                data[col] = [str(row[col])]*length
            source_data.append(data)
            
    return source_data

def get_amp_rows(amps, cam_sep=None):
    '''Convert amp keys from threshold files into an index that can be used to filter
    out selected amps when plotting timeseries and histograms.
    Input:
        amps: list of amps in the (cam+spectro+amp) format
    Options:
        cam_sep: if True, indicates that data is already separated by camera
    Output:
        ids: numpy array of the corresponding ids to filter a list '''
    ids = []
    amp_vals = {'A':0, 'B':1, 'C':2, 'D':3}
    cam_vals = {'B':0, 'R':10, 'Z':20}
    
    if cam_sep:
        for amp in amps:
            spec_val = int(amp[1])
            amp_val = amp_vals[amp[2]]
            ids.append(spec_val*4 + amp_val)
    else:
        for amp in amps:
            cam_val = cam_vals[amp[0]]
            spec_val = int(amp[1])
            amp_val = amp_vals[amp[2]]
            ids.append(((cam_val+spec_val)*4)+amp_val)
    return np.array(ids)

def plot_timeseries(src, title, amps=None, plot_height=300, plot_width=900):
    '''Given a list of separate dictionaries containing data for each amp, plots timeseries.
    Input:
        src: a list of dictionaries, with elements containing keywords [EXPID, EXPIDZ, NIGHT, aspect_value, CAM, lower, upper]
        title: y-axis label, (name of metric being plotted)
    Options:
        amps: a list of amps to be plotted. if None, all amps are plotted.
        plot_height, plot_width: width and height of plot in pixels
    Output:
        a bokeh Column object, containing the 3 timeseries plots for each camera for the given metric.'''
    #amps = [cam+str(spec)+amp for cam in ['B', 'R', 'Z'] for spec in np.arange(0, 10) for amp in ['A', 'B', 'C', 'D']]
    ids = []
    if amps == None:
        ids += list(np.arange(0, len(src)))
    else:
        ids.append(get_amp_rows(amps))
    src_selected = np.array(src)[ids]
    cam_figs = []
    for cam in ['B', 'R', 'Z']:
        colors = {'R': 'firebrick', 'B':'steelblue', 'Z':'green'}
        cam_src = [s for s in src_selected if s['CAM']==cam]
        
        hover= HoverTool(names = ['circles'], tooltips = [('Amp', '@AMP'),
                                     ('Spec', '@SPECTRO'),
                                     ('EXPID', '@EXPID'),
                                     ('{}'.format(title), '@aspect_values'),
                                     ('Upper threshold', '@upper'),
                                     ('Lower threshold', '@lower')])
        box_zoom = BoxZoomTool()
        reset = ResetTool()
        
        fig = bk.figure(title=cam, plot_height=plot_height, plot_width=plot_width, tools=[hover, box_zoom, reset])
        if len(cam_src) == 0:
            continue
        else:
            for i in range(len(cam_src)):
                source=ColumnDataSource()
                for key in cam_src[i].keys():
                    if key != 'CAM':
                        source.add(cam_src[i][key], key)
                    if key == 'CAM':
                        continue
                fig.circle(x='EXPIDZ', y='aspect_values', color=colors[cam], size=2, name='circles', source=source)
                fig.line(x='EXPIDZ', y='aspect_values', line_color=colors[cam], source=source)
                good_range = BoxAnnotation(bottom=cam_src[i]['lower'][0], top=cam_src[i]['upper'][0], 
                                           fill_color='green', fill_alpha=0.05)
                fig.add_layout(good_range)
                #fig.line(x='EXPIDZ', y='lower', line_dash='dashed', line_color='black', source=source)
                #fig.line(x='EXPIDZ', y='upper', line_dash='dashed', line_color='black', source=source)
                fig.xaxis.axis_label = 'Exposure ID'
                if cam in ['R', 'B']:
                    fig.xaxis.axis_label_text_color = 'white'
                fig.yaxis.axis_label = ' '.join(title.split(sep='_')).title()
            cam_figs.append(fig)
    return column(cam_figs)

def get_threshold_table(name, filepath, width=600):
    '''Given a filepath, returns a table containing the lower and upper threshold values for each amp
    for a certain metric.
    Input:
        name: metric (str)
        filepath: path to a threshold file (str)
    Options:
        width: width of the plot in pixels
    Output:
        a bokeh DataTable object'''
    #amps = [cam+str(spec)+amp for cam in ['B', 'R', 'Z'] for spec in np.arange(0, 10) for amp in ['A', 'B', 'C', 'D']]
    lower, upper, keys = get_thresholds(filepath, return_keys=True)
    
    lower_col = []
    lower_err_col = []
    upper_col = []
    upper_err_col = []
    keys_col = []
    
    if name in ['READNOISE', 'BIAS']:
        lower_col += (lower[0][1]+lower[1][1]+lower[2][1])
        lower_err_col += (lower[0][0]+lower[1][0]+lower[2][0])
        upper_col += (upper[0][0]+upper[1][0]+upper[2][0])
        upper_err_col += (upper[0][1]+upper[1][1]+upper[2][1])
        keys_col += (keys[0] + keys[1] + keys[2])
    if name in ['COSMICS_RATE']:
        lower_col += [lower[0][1], lower[1][1], lower[2][1]]
        lower_err_col += [lower[0][0], lower[1][0], lower[2][0]]
        upper_col += [upper[0][0], upper[1][0], upper[2][0]]
        upper_err_col += [upper[0][1], upper[1][1], upper[2][1]]
        keys_col += (keys[0]+keys[1]+keys[2])
        
        for i in range(len(lower_col)):
            if lower_col[i] == 0 or lower_col[i] == None:
                lower_col[i] = 'N/A'
                lower_err_col[i] = 'N/A'
                upper_col[i] = 'N/A'
                upper_err_col[i] = 'N/A'
            else:
                continue
    
    src = ColumnDataSource(data=dict(
        key=keys_col,
        lower_err=lower_err_col,
        lower=lower_col,
        upper=upper_col,
        upper_err=upper_err_col,
    ))
    
    columns = []
    if name in ['READNOISE', 'BIAS']:
        columns += [TableColumn(field='key', title='Amp')]
    if name in ['COSMICS_RATE']:
        columns += [TableColumn(field='key', title='Cam')]
    
    columns += [
        TableColumn(field="lower_err", title="Lower Error", formatter=NumberFormatter(format="0.00")),
        TableColumn(field="lower", title="Lower Warning", formatter=NumberFormatter(format="0.00")),
        TableColumn(field="upper", title="Upper Warning", formatter=NumberFormatter(format="0.00")),
        TableColumn(field="upper_err", title="Upper Error", formatter=NumberFormatter(format="0.00")),
    ]
    
    data_table = DataTable(source=src, columns=columns, width=width, selectable=True, sortable=True)
    return data_table

def plot_histogram(src, bins=20, amps=None, plot_height=250, plot_width=250):
    '''Given timeseries data for each amp, plots histograms per camera across all exposures in the data.
    Input:
        src: a list of dictionaries containing data per amp for some metric.
    Options:
        bins: number of bins for the histogram, default 20. (int)
        amps: list of selected amps to use when making histogram. if None, uses all amps.
        plot_height, plot_width = height, width of plot in pixels
    Output:
        a bokeh Column figure object, containing all 3 histograms (one per cam)'''
    ids = []
    if amps == None:
        ids = list(np.arange(0, len(src)))
    else:
        ids = get_amp_rows(amps)
    src_selected = np.array(src)[np.array(ids)]
    cam_figs = []
    for cam in ['B', 'R', 'Z']:
        fig = bk.figure(plot_height=plot_height, plot_width=plot_width, toolbar_location=None, title=cam)
        fig.title.text_color = 'white'
        colors = {'R': 'firebrick', 'B':'steelblue', 'Z':'green'}
        cam_src = [s for s in src_selected if s['CAM']==cam]
        aspect_data = []
        for src in cam_src:
            aspect_data += list(src['aspect_values'])
        
        hist, edges = np.histogram(aspect_data, density=True, bins=bins)
        fig.quad(top=hist, bottom=0, left=edges[:-1], right=edges[1:], 
                 fill_color=colors[cam], line_color='black', alpha=0.70)
        fig.add_layout(Span(location=np.percentile(aspect_data, 1),
                            dimension='height', line_color='black',
                            line_width=2,
                           ))
        fig.add_layout(Span(location=np.percentile(aspect_data, 99),
                            dimension='height', line_color='black',
                            line_width=2,
                           ))
        fig.yaxis.axis_label = 'Value'
        fig.yaxis.axis_label_text_color = 'white'
        cam_figs.append(fig)
        
    return row(cam_figs)


def get_specs(time_data):
    '''return the spectrographs that have timeseries data'''
    specs = []
    for i in range(len(time_data)):
        if type(time_data[i]) == dict:
            specs.append(time_data[i]['SPECTRO'][0])
        if type(time_data[i]) == int:
            continue
    return np.unique(specs)

def get_spec_amps(spec, lst=None):
    '''return amps that correspond to a spectrograph in cam+spec+amp format.
    Args:
        spec: an integer spectrograph number, or a list of spectrographs. If
        a list, enable the lst option.
    Options:
        lst: if true, will return amps for multiple spectrographs. if None,
        will assume spec is a single value.'''
    amps = []
    if lst == None:
        for cam in ['B', 'R', 'Z']:
            for amp in ['A', 'B', 'C', 'D']:
                amps.append(cam+str(spec)+amp)
    if lst == True:
        for s in spec:
            for cam in ['B', 'R', 'Z']:
                for amp in ['A', 'B', 'C', 'D']:
                    amps.append(cam+str(s)+amp)
    return amps
