import sys, os, re 
import numpy as np
import json
import csv
from astropy.table import Table, vstack
import fitsio
import bokeh.plotting as bk
from bokeh.layouts import gridplot, column
from bokeh.models import TapTool as TapTool
from bokeh.models import OpenURL, ColumnDataSource, HoverTool, CustomJS
from qqa.qa.base import QA
from bokeh.models.widgets import DataTable, TableColumn, NumberFormatter

def get_outdir():
    qqa_path = ''
    user_paths = os.environ['PYTHONPATH'].split(os.pathsep)
    for path in user_paths:
        if 'qqa' in path:
            qqa_path += path
    qqa_path += '/qqa/threshold_files'
    return qqa_path

def write_threshold_json(indir, start_date, end_date, name):
    '''
    Inputs:
        indir: contains summary.json files, 
        outdir: where the thresholds files should be generated
        start_date, end_date: range over which thresholds should be calculated
        name: the metric thresholds are being generated for
    Output:
        writes a json file with thresholds for each amp to the specified directory
        (NOTE: if amp is not in previous nights summary files, the thresholds generated 
        will be None and will need to be manually input)'''
    datadict = dict()
    amps = []
    nights = np.arange(start_date, end_date+1)
    nights_real = [night for night in nights if os.path.isfile(os.path.join(indir, '{night}/summary.json'.format(night=night)))]
    for night in nights_real:
        with open(os.path.join(indir,'{night}/summary.json'.format(night=night))) as json_file:
            data = json.load(json_file)
        amps += data['PER_AMP'][name].keys()
        datadict[night] = data
    all_amps = [cam+spec+amp for spec in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'] for cam in ['B', 'R', 'Z'] for amp in ['A', 'B', 'C', 'D']]
    rest_amps = np.setdiff1d(all_amps, amps)
    thresholds = dict()
    if name in ["READNOISE", "BIAS"]:
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
                upper = med_avg + 0.5*std_avg
                lower = med_avg - 0.5*std_avg
                thresholds[amp] = dict(upper=upper, lower=lower)
            if amp in rest_amps:
                thresholds[amp] = dict(upper=None, lower=None)
    if name in ['COSMICS_RATE']:
        num_exps = []
        lower = []
        upper = []
        for night in nights_real:
            lower.append(datadict[night]['PER_AMP'][name]['lower'])
            upper.append(datadict[night]['PER_AMP'][name]['upper'])
            num_exps.append(datadict[night]['PER_AMP'][name]['num_exp'])
        weights = np.array(num_exps)/np.sum(num_exps)
        lower_avg = np.average(lower, weights=weights)
        upper_avg = np.average(upper, weights=weights)
        thresholds = dict(lower=lower_avg, upper=upper_avg) 
        
    outdir = get_outdir()
    threshold_file = os.path.join(outdir, '{name}-{night}.json'.format(name=name, night=end_date+1))
    with open(threshold_file, 'w') as json_file:
         json.dump(thresholds, json_file, indent=4)
    print('Wrote {}'.format(threshold_file))

def pick_threshold_file(name, night):
    file = '{name}-{night}.json'.format(name=name, night=night)
    threshold_dir = get_outdir()
    filepath = ''
    files = [f for f in np.sort(os.listdir(threshold_dir)) if name in f]
    for f in files:
        if str(night) in f:
            filepath += os.path.join(threshold_dir, file)    
    if filepath == '':
        filepath += os.path.join(threshold_dir, files[-1])
    return filepath

def get_thresholds(filepath, return_keys=True):
    '''Unpack threshold values to use in plotting amp graphs'''
    with open(filepath, 'r') as json_file:
        threshold_data = json.load(json_file)
    keys = threshold_data.keys()
    if 'READNOISE' or 'BIAS' in filepath:
        lowerB = []
        upperB = []
        lowerZ = []
        upperZ = []
        lowerR = []
        upperR = []
        real_keys = []
        for key in keys:
            if key[0] == 'B':
                if threshold_data[key]['lower'] == None:
                    continue
                else:
                    lowerB.append(threshold_data[key]['lower'])
                    upperB.append(threshold_data[key]['upper'])
                    real_keys.append(key)
            if key[0] == 'Z': 
                if threshold_data[key]['lower'] == None:
                    continue
                else:
                    lowerZ.append(threshold_data[key]['lower'])
                    upperZ.append(threshold_data[key]['upper'])
                    real_keys.append(key)
            if key[0] == 'R':
                if threshold_data[key]['lower'] == None:
                    continue
                else:
                    lowerR.append(threshold_data[key]['lower'])
                    upperR.append(threshold_data[key]['upper'])
                    real_keys.append(key)
            else:
                continue
        lower = [lowerB, lowerR, lowerZ]
        upper = [upperB, upperR, upperZ]
    if 'COSMICS_RATE' in filepath:
        real_keys = ['keys not applicable']
        lower = [threshold_data['lower']]
        upper = [threshold_data['upper']]
    
    if return_keys:
        return lower, upper, real_keys
    else:
        return lower, upper 
    

def get_timeseries_dataset(data_dir, start_date, end_date, hdu, aspect):
    '''reuses the timeseries function for the flask app, but with some changes'''
    
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

    filepath = pick_threshold_file(aspect, end_date)
    with open(filepath, 'r') as json_file:
        threshold_data = json.load(json_file)
    source_data = []
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
                if aspect in ['READNOISE', 'BIAS']:
                    amp = cam + str(row['SPECTRO']) + row['AMP']
                    data['lower'] = [threshold_data[amp]['lower']]*length
                    data['upper'] = [threshold_data[amp]['upper']]*length
                if aspect in ['COSMICS_RATE']:
                    data['lower'] = [threshold_data['lower']]*length
                    data['upper'] = [threshold_data['upper']]*length
                for col in group_by_list:
                    data[col] = [str(row[col])]*length
                source_data.append(data)          
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

def get_amp_rows(amps):  
    ids = []
    amp_vals = {'A':0, 'B':1, 'C':2, 'D':3}
    cam_vals = {'B':0, 'R':10, 'Z':20}
    for amp in amps:
        cam_val = cam_vals[amp[0]]
        spec_val = int(amp[1])
        amp_val = amp_vals[amp[2]]
        ids.append(((cam_val+spec_val)*4)+amp_val)
    return ids

def plot_timeseries(src, amps=None): 
    #amps = [cam+str(spec)+amp for cam in ['B', 'R', 'Z'] for spec in np.arange(0, 10) for amp in ['A', 'B', 'C', 'D']]
    ids = []
    if amps == None:
        ids += list(np.arange(0, len(src)))
    else:
        ids += get_amp_rows(amps)
    src_selected = np.array(src)[np.array(ids)]
    cam_figs = []
    for cam in ['B', 'R', 'Z']:
        colors = {'R': 'firebrick', 'B':'steelblue', 'Z':'green'}
        cam_src = [s for s in src_selected if s['CAM']==cam]
        fig = bk.figure(title=cam, plot_height=200, plot_width=600)
        if len(cam_src) == 0:
            continue
        else:
            for i in range(len(cam_src)):
                fig.circle(x=cam_src[i]['EXPIDZ'][1:], y=cam_src[i]['aspect_values'][1:], color=colors[cam], size=2)
                fig.line(x=cam_src[i]['EXPIDZ'][1:], y=cam_src[i]['aspect_values'][1:], line_color=colors[cam])
                fig.line(x=cam_src[i]['EXPIDZ'][1:], y=cam_src[i]['lower'][1:], line_dash='dashed', line_color='black')
                fig.line(x=cam_src[i]['EXPIDZ'][1:], y=cam_src[i]['upper'][1:], line_dash='dashed', line_color='black')
            cam_figs.append(fig)
    return column(cam_figs)

def get_threshold_table(filepath):
    #amps = [cam+str(spec)+amp for cam in ['B', 'R', 'Z'] for spec in np.arange(0, 10) for amp in ['A', 'B', 'C', 'D']]
    lower, upper, keys = get_thresholds(filepath, return_keys=True)
    if len(lower) != 1:
        lower = lower[0]+lower[1]+lower[2]
        upper = upper[0]+upper[1]+upper[2]
    
    src = ColumnDataSource(data=dict(
        amp=keys,
        lower=lower,
        upper=upper,
    ))
    
    if len(keys) == 1:
        columns = [
            TableColumn(field="lower", title="1st percentile", formatter=NumberFormatter(format="0.00")),
            TableColumn(field="upper", title="99th percentile", formatter=NumberFormatter(format="0.00")),
        ]
    else:    
        columns = [
        TableColumn(field="amp", title="Amp"),
        TableColumn(field="lower", title="Lower Threshold", formatter=NumberFormatter(format="0.00")),
        TableColumn(field="upper", title="Upper Threshold", formatter=NumberFormatter(format="0.00")),
        ]

    data_table = DataTable(source=src, columns=columns, width=800, selectable=True, sortable=True)
    return data_table
