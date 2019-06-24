import sys, os
import numpy as np
import json
import csv

def get_prev_nights(currentnightdir, n):
    '''returns n previously processed nights given the path to the current night directory. 
    If there is only one night, or not enough nights with the given n, returns maximum number 
    of nights possible. If there is only one night, returns that night.'''
    nightsdir, currentnight = os.path.split(currentnightdir)
    nights = np.sort(os.listdir(path=nightsdir))
    current_id = list(nights).index(currentnight)
    prev_nights = []
    if current_id == 0:
        prev_nights += [currentnight]
    if current_id <= n:
        prev_nights += list(nights[0:current_id])
    if current_id > n:
        prev_nights += list(nights[(current_id-n):current_id])
    return prev_nights

def write_threshold_json(indir, outdir, prev_nights, name):
    '''
    Inputs:
        indir: contains summary.json files, 
        outdir: where the thresholds files should be generated
        prev_nights: array of previous nights to base thresholds on
        name: the metric thresholds are being generated for
    Output:
        writes a json file with thresholds for each amp to the specified directory
        (NOTE: if amp is not in previous nights summary files, the thresholds generated 
        will be None and will need to be manually input)'''
    prev_nights = get_prev_nights(currentnightdir, n)
    datadict = dict()
    amps = []
    for night in prev_nights:
        with open(os.path.join(indir,'{night}/summary.json'.format(night=night))) as json_file:
            data = json.load(json_file)
        amps += data['PER_AMP'][name].keys()
        datadict[night] = data
    all_amps = [spec+cam+amp for spec in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'] for cam in ['B', 'R', 'Z'] for amp in ['A', 'B', 'C', 'D']]
    print(all_amps)
    rest_amps = np.setdiff1d(all_amps, amps)
    thresholds = dict()
    if name in ["READNOISE", "BIAS"]:
        for amp in all_amps:
            num_exps = []
            meds = []
            stds = []
            if amp in amps:
                for night in prev_nights:
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
    if name in ['COSMICS_RATES']:
        num_exps = []
        p95 = []
        p90 = []
        for night in prev_nights:
            p95.append(datadict[night]['PER_AMP'][name]['p95'])
            p90.append(datadict[night]['PER_AMP'][name]['p90'])
            num_exps.append(datadict[night]['PER_AMP'][name]['num_exp'])
        weights = np.array(num_exps)/np.sum(num_exps)
        p95_avg = np.average(p95, weights=weights)
        p90_avg = np.average(p90, weights=weights)
        thresholds = dict(p95=p95_avg, p90=p90_avg)
    threshold_file = os.path.join(outdir, '{name}-{night}.json'.format(name=name, night=prev_nights[-1]))
    with open(threshold_file, 'w') as out:
        json.dump(thresholds, out, indent=4)
    print('Wrote {}'.format(threshold_file))

        