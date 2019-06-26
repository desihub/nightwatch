import numpy as np

import bokeh
import bokeh.plotting as bk
from bokeh.models.tickers import FixedTicker
from bokeh.models.ranges import FactorRange
from bokeh.models import LinearColorMapper, ColorBar, ColumnDataSource, OpenURL, TapTool, Div, HoverTool, Range1d, BoxAnnotation, Whisker
import bokeh.palettes
from bokeh.layouts import column, gridplot

import json
import os

def get_thresholds(name, night):
    '''TO DO: DOCUMENT'''
    file = '{name}-{night}.json'.format(name=name, night=night)
    startdir = os.getcwd()
    filepath = ''
    for i, j, k in os.walk(startdir):
        if file in k:
            filepath += os.path.join(i, file)
    with open(filepath, 'r') as json_file:
        threshold_data = json.load(json_file)
    keys = threshold_data.keys()
    if name in ['READNOISE', 'BIAS']:
        lowerB = []
        upperB = []
        lowerZ = []
        upperZ = []
        lowerR = []
        upperR = []
        for key in keys:
            if key[1] == 'B':
                if threshold_data[key]['lower'] == None:
                    continue
                else:
                    lowerB.append(threshold_data[key]['lower'])
                    upperB.append(threshold_data[key]['upper'])
            if key[1] == 'Z': 
                if threshold_data[key]['lower'] == None:
                    continue
                else:
                    lowerZ.append(threshold_data[key]['lower'])
                    upperZ.append(threshold_data[key]['upper'])
            if key[1] == 'R':
                if threshold_data[key]['lower'] == None:
                    continue
                else:
                    lowerR.append(threshold_data[key]['lower'])
                    upperR.append(threshold_data[key]['upper'])
            else:
                continue
        lower = [lowerB, lowerR, lowerZ]
        upper = [upperB, upperR, upperZ]
    if name in ['COSMICS_RATES']:
        lower = threshold_data['p10']
        upper = threshold_data['p90']
    return lower, upper

def get_amp_colors(data, lower, upper):
    '''takes in per amplifier data and the acceptable threshold for that metric (TO DO: update this once
    we allow for individual amplifiers to have different thresholds).
    Input: array of amplifier metric data, upper threshold (float)
    Output: array of colors to be put into a ColumnDataSource
    '''
    colors = []
    for i in range(len(data)):
        if lower[i] == None or upper[i] == None:
            continue
        if data[i] < lower[i]:
            colors.append('red')
        if data[i] >= lower[i] and data[i] < upper[i]:
            colors.append('black')
        if data[i] >= upper[i]:
            colors.append('red')
    return colors

def get_amp_size(data, lower, upper):
    '''takes in per amplifier data and the acceptable threshold for that metric (TO DO: update this once
    we allow for individual amplifiers to have different thresholds).
    Input: array of amplifier metric data, upper threshold (float)
    Output: array of sizes for markers to be put into a ColumnDataSource
    '''
    sizes = []
    for i in range(len(data)):
        if lower[i] == None or upper[i] == None:
            sizes.append(None)
        if data[i] < lower[i]:
            sizes.append(6)
        if data[i] >= lower[i] and data[i] < upper[i]:
            sizes.append(4)
        if data[i] >= upper[i]:
            sizes.append(6)
    return sizes

def isolate_spec_lines(data_locs, data):
    '''function to generate isolated data sets so that each spectrograph has an isolated line'''
    ids = [0]
    for i in range(len(data_locs)-1):
        if data_locs[i][0] == data_locs[i+1][0]:
            continue
        if data_locs[i][0] != data_locs[i+1][0]:
            ids.append(i+1)
    ids.append(len(data_locs))
    spec_groups = []
    data_groups = []
    for i in range(len(ids)-1):
        spec_groups.append(data_locs[ids[i]:ids[i+1]])
        data_groups.append(data[ids[i]:ids[i+1]])
    return spec_groups, data_groups

def plot_amp_cam_qa(data, name, cam, labels, lower, upper, title, plot_height=80, plot_width=700):
    '''Plot a per-amp visualization of data[name]
    qamin/qamax: min/max ranges for the color scale'''
    
    if title is None:
        title = name   
    
    #unpacking data
    spec_loc = []
    amp_loc = []
    name_data = []
    data_val = []
    for row in data:
        if row['CAM'] in (cam, cam.encode('utf-8')):
            amp_loc.append(row['AMP'].decode('utf-8'))
            spec_loc.append(str(row['SPECTRO']))
            data_val.append(row[name])
            cam_spect = row['CAM'].lower().decode("utf-8") + str(row['SPECTRO'])
            name_data += ["preproc-{cam_spect}-{expid}".format(cam_spect=cam_spect, expid='%08d'%row['EXPID'])]
        else:
            continue
    _, ids = np.unique(spec_loc, return_index=True)
    spec_loc = np.array(spec_loc)[np.sort(ids)]
    _, ids = np.unique(amp_loc, return_index=True)
    amp_loc = np.array(amp_loc)[np.sort(ids)]
    
    if name in ['COSMICS_RATE']:
        lower = [lower]*len(data_val)
        upper = [upper]*len(data_val)
    
    locations = [(spec, amp) for spec in spec_loc for amp in amp_loc]
    colors = get_amp_colors(data_val, lower, upper)
    sizes = get_amp_size(data_val, lower, upper)
    
    source = ColumnDataSource(data=dict(
        data_val=data_val,
        locations=locations,
        colors=colors,
        sizes=sizes,
        name=name_data,
        lower=lower,
        upper=upper,
    ))
    
    axis = bk.figure(x_range=FactorRange(*labels), toolbar_location=None, 
                     plot_height=50, plot_width=plot_width,
                     y_axis_location=None)      
    #plotting
    hover= HoverTool(tooltips = [
        ('(spec, amp)', '@locations'),
        ('{}'.format(name), '@data_val')],
                      line_policy='nearest')
    
    fig = bk.figure(x_range=axis.x_range, 
                      toolbar_location=None, plot_height=plot_height, 
                      plot_width=plot_width, x_axis_location=None, tools=[hover, 'tap'])
    
    spec_groups, data_groups = isolate_spec_lines(locations, data_val)
    for i in range(len(spec_groups)):
        fig.line(x=spec_groups[i], y=data_groups[i], line_color='black', alpha=0.25)
        
    fig.circle(x='locations', y='data_val', line_color=None, 
                 fill_color='colors', size='sizes', source=source, name='circles')

    fig.yaxis.axis_label = cam
    fig.y_range = Range1d(np.min(data_val)*0.9, np.max(data_val)*1.1)
    fig.yaxis.minor_tick_line_color=None
    fig.ygrid.grid_line_color=None
    if cam == 'R':
        fig.outline_line_color='firebrick'
    if cam == 'B':
        fig.outline_line_color='steelblue'
        fig.title.text = title
    if cam =='Z':
        fig.outline_line_color='green'
    fig.outline_line_alpha=0.7
    
    if name in ['READNOISE', 'BIAS']:
        fig.add_layout(Whisker(source=source, base='locations', upper='upper', lower='lower'))
    if name in ['COSMICS_RATE']:
        fig.add_layout(BoxAnnotation(bottom=lower[0], top=upper[0], fill_alpha=0.1, fill_color='green'))
    
    taptool = fig.select(type=TapTool)
    taptool.names = ['circles']
    taptool.callback = OpenURL(url='@name-4x.html')

    return fig

def plot_amp_qa(data, name, lower, upper, title=None, plot_height=80, plot_width=700):

    if title == None:
        title = name
    labels = [(spec, amp) for spec in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'] for amp in ['A', 'B', 'C', 'D']]
    
    if name in ['READNOISE', 'BIAS']:
        fig_B = plot_amp_cam_qa(data, name, 'B', labels, lower[0], upper[0], title, plot_height=plot_height+25, plot_width=plot_width)
        fig_R = plot_amp_cam_qa(data, name, 'R', labels, lower[1], upper[1], title, plot_height=plot_height, plot_width=plot_width)
        fig_Z = plot_amp_cam_qa(data, name, 'Z', labels, lower[2], upper[2], title, plot_height=plot_height, plot_width=plot_width)
    if name in ['COSMICS_RATE']:
        fig_B = plot_amp_cam_qa(data, name, 'B', labels, lower, upper, title, plot_height=plot_height+25, plot_width=plot_width)
        fig_R = plot_amp_cam_qa(data, name, 'R', labels, lower, upper, title, plot_height=plot_height, plot_width=plot_width)
        fig_Z = plot_amp_cam_qa(data, name, 'Z', labels, lower, upper, title, plot_height=plot_height, plot_width=plot_width)
    
    #x-axis
    axis = bk.figure(x_range=FactorRange(*labels), toolbar_location=None, 
                     plot_height=50, plot_width=plot_width,
                     y_axis_location=None)         
    axis.line(x=labels, y=0, line_color=None)
    axis.grid.grid_line_color=None
    axis.outline_line_color=None
    
    fig = gridplot([[fig_B], [fig_R], [fig_Z], [axis]], toolbar_location=None)
    
    return fig
        
        
