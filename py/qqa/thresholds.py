import sys, os
import numpy as np
import json
import csv

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

def get_thresholds(filepath):
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
        for key in keys:
            if key[0] == 'B':
                if threshold_data[key]['lower'] == None:
                    continue
                else:
                    lowerB.append(threshold_data[key]['lower'])
                    upperB.append(threshold_data[key]['upper'])
            if key[0] == 'Z': 
                if threshold_data[key]['lower'] == None:
                    continue
                else:
                    lowerZ.append(threshold_data[key]['lower'])
                    upperZ.append(threshold_data[key]['upper'])
            if key[0] == 'R':
                if threshold_data[key]['lower'] == None:
                    continue
                else:
                    lowerR.append(threshold_data[key]['lower'])
                    upperR.append(threshold_data[key]['upper'])
            else:
                continue
        lower = [lowerB, lowerR, lowerZ]
        upper = [upperB, upperR, upperZ]
    if 'COSMICS_RATE' in filepath:
        print(threshold_data)
        lower = threshold_data['lower']
        upper = threshold_data['upper']
    return lower, upper

        