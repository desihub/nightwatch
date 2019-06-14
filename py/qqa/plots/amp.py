import numpy as np

import bokeh
import bokeh.plotting as bk
from bokeh.models.tickers import FixedTicker
from bokeh.models.ranges import FactorRange
from bokeh.models import LinearColorMapper, ColorBar, ColumnDataSource, OpenURL, TapTool, Div, HoverTool
import bokeh.palettes
from bokeh.layouts import column, gridplot

def get_amp_colors(data, threshold):
    '''takes in per amplifier data and the acceptable threshold for that metric (TO DO: update this once
    we allow for individual amplifiers to have different thresholds).
    Input: array of amplifier metric data, upper threshold (float)
    Output: array of colors to be put into a ColumnDataSource
    '''
    colors = []
    for i in range(len(data)):
        if data[i] < threshold:
            colors.append('black')
        if data[i] >= threshold:
            colors.append('red')
    return colors

def get_amp_size(data, threshold):
    '''takes in per amplifier data and the acceptable threshold for that metric (TO DO: update this once
    we allow for individual amplifiers to have different thresholds).
    Input: array of amplifier metric data, upper threshold (float)
    Output: array of sizes for markers to be put into a ColumnDataSource
    '''
    sizes = []
    for i in range(len(data)):
        if data[i] < threshold:
            sizes.append(4)
        if data[i] >= threshold:
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

def plot_amp_qa(data, name, title=None, palette="YlGn9", qamin=None, qamax=None, plot_height=80, 
                plot_width=700):
    '''Plot a per-amp visualization of data[name]
    qamin/qamax: min/max ranges for the color scale'''
    
    if title is None:
        title = name
    if qamin is None:
        qamin = np.min(data[name])
    if qamax is None:
        qamax = np.max(data[name])    
    
    #unpacking data
    spec_loc_R = []
    amp_loc_R = []
    spec_loc_B = []
    amp_loc_B = []
    spec_loc_Z = []
    amp_loc_Z = []
    data_R = []
    data_B = []
    data_Z = []
    for row in data:
        if row['CAM'] in ('R', b'R'):
            amp_loc_R.append(row['AMP'].decode('utf-8'))
            spec_loc_R.append(str(row['SPECTRO']))
            data_R.append(row[name])
        if row['CAM'] in ('B', b'B'):
            amp_loc_B.append(row['AMP'].decode('utf-8'))
            spec_loc_B.append(str(row['SPECTRO']))
            data_B.append(row[name])
        if row['CAM'] in ('Z', b'Z'):
            amp_loc_Z.append(row['AMP'].decode('utf-8'))
            spec_loc_Z.append(str(row['SPECTRO']))
            data_Z.append(row[name])
    
    spec_loc, ids = np.unique(spec_loc_R, return_index=True)
    spec_loc_R = np.array(spec_loc_R)[np.sort(ids)]
    amp_loc, ids = np.unique(amp_loc_R, return_index=True)
    amp_loc_R = np.array(amp_loc_R)[np.sort(ids)]
    spec_loc, ids = np.unique(spec_loc_B, return_index=True)
    spec_loc_B = np.array(spec_loc_B)[np.sort(ids)]
    amp_loc, ids = np.unique(amp_loc_B, return_index=True)
    amp_loc_B = np.array(amp_loc_B)[np.sort(ids)]
    spec_loc, ids = np.unique(spec_loc_Z, return_index=True)
    spec_loc_Z = np.array(spec_loc_Z)[np.sort(ids)]
    amp_loc, ids = np.unique(amp_loc_Z, return_index=True)
    amp_loc_Z = np.array(amp_loc_Z)[np.sort(ids)]
    
    locations_R = [(spec, amp) for spec in spec_loc_R for amp in amp_loc_R]
    locations_B = [(spec, amp) for spec in spec_loc_B for amp in amp_loc_B]
    locations_Z = [(spec, amp) for spec in spec_loc_Z for amp in amp_loc_Z]
    
    colors_Z = get_amp_colors(data_Z, qamax)
    colors_R = get_amp_colors(data_R, qamax)
    colors_B = get_amp_colors(data_B, qamax)
    sizes_Z = get_amp_size(data_Z, qamax)
    sizes_R = get_amp_size(data_R, qamax)
    sizes_B = get_amp_size(data_B, qamax)
   
    source = ColumnDataSource(data=dict(
        data_R=data_R,
        data_B=data_B,
        data_Z=data_Z,
        locations_R=locations_R,
        locations_B = locations_B,
        locations_Z = locations_Z,
        colors_Z=colors_Z,
        colors_B=colors_B,
        colors_R=colors_R,
        sizes_Z=sizes_Z,
        sizes_B=sizes_B,
        sizes_R=sizes_R,
    ))
    
    #x-axis
    labels = [(spec, amp) for spec in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'] for amp in ['A', 'B', 'C', 'D']]
    axis = bk.figure(x_range=FactorRange(*labels), toolbar_location=None, 
                     plot_height=50, plot_width=plot_width,
                     y_axis_location=None)         
    axis.line(x=labels, y=0, line_color=None)
    axis.grid.grid_line_color=None
    axis.outline_line_color=None
    
    #R
    hover_R= HoverTool(tooltips = [
        ('(spec, amp)', '@locations_R'),
        ('{}'.format(name), '$y')],
                      line_policy='next')
    fig_R = bk.figure(x_range=axis.x_range, 
                      toolbar_location=None, plot_height=plot_height, 
                      plot_width=plot_width, x_axis_location=None, tools=[hover_R])
    
    spec_groups, data_groups = isolate_spec_lines(locations_R, data_R)
    for i in range(len(spec_groups)):
        fig_R.line(x=spec_groups[i], y=data_groups[i], line_color='black', alpha=0.25)
        
    fig_R.circle(x='locations_R', y='data_R', line_color=None, 
                 fill_color='colors_R', size='sizes_R', source=source)

    fig_R.yaxis.axis_label = 'R'
    fig_R.yaxis.minor_tick_line_color=None
    fig_R.ygrid.grid_line_color=None
    fig_R.outline_line_color='firebrick'
    fig_R.outline_line_alpha=0.7

    #B
    hover_B= HoverTool(tooltips = [
        ('(spec, amp)', '@locations_B'),
        ('{}'.format(name), '$y')],
                      line_policy='next')
    fig_B = bk.figure(x_range=axis.x_range, toolbar_location=None, x_axis_location=None,
                   plot_height=plot_height+25, plot_width=plot_width, title=title, tools=[hover_B])
        
    spec_groups, data_groups = isolate_spec_lines(locations_B, data_B)
    for i in range(len(spec_groups)):
        fig_B.line(x=spec_groups[i], y=data_groups[i], line_color='black', alpha=0.25)
    
    circle_B = fig_B.circle(x='locations_B', y='data_B', line_color=None, 
                 fill_color='colors_B', size='sizes_B', source=source)
        
    fig_B.yaxis.axis_label = 'B'
    fig_B.ygrid.grid_line_color=None
    fig_B.yaxis.minor_tick_line_color=None
    fig_B.outline_line_color='steelblue'
    fig_B.outline_line_alpha=0.7

    #Z
    hover_Z= HoverTool(tooltips = [
        ('(spec, amp)', '@locations_Z'),
        ('{}'.format(name), '$y')],
                      line_policy='next')
    fig_Z = bk.figure(x_range=axis.x_range, toolbar_location=None, x_axis_location=None,
                   plot_height=plot_height, plot_width=plot_width, tools=[hover_Z])
        
    spec_groups, data_groups = isolate_spec_lines(locations_Z, data_Z)
    for i in range(len(spec_groups)):
        fig_Z.line(x=spec_groups[i], y=data_groups[i], line_color='black', alpha=0.25)
    
    circle_Z = fig_Z.circle(x='locations_Z', y='data_Z', line_color=None, 
                 fill_color='colors_Z', size='sizes_Z', source=source)
    
    fig_Z.yaxis.axis_label = 'Z'
    fig_Z.ygrid.grid_line_color=None
    fig_Z.yaxis.minor_tick_line_color=None
    fig_Z.outline_line_color='grey'
    fig_Z.outline_line_alpha=0.7

    fig = gridplot([[fig_B], [fig_R], [fig_Z], [axis]], toolbar_location=None)
    
    return fig
