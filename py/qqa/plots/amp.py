import numpy as np

import bokeh
import bokeh.plotting as bk
from bokeh.models.tickers import FixedTicker
from bokeh.models.ranges import FactorRange
from bokeh.models import LinearColorMapper, ColorBar, ColumnDataSource, OpenURL, TapTool, Div
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
    spec_loc = []
    amp_loc = []
    data_R = []
    data_B = []
    data_Z = []
    for row in data:
        if row['CAM'] in ('R', b'R'):
            amp_loc.append(row['AMP'].decode('utf-8'))
            spec_loc.append(str(row['SPECTRO']))
            data_R.append(row[name])
        if row['CAM'] in ('B', b'B'):
            data_B.append(row[name])
        if row['CAM'] in ('Z', b'Z'):
            data_Z.append(row[name])
    
    locations = [(spec, amp) for spec in np.unique(spec_loc) for amp in amp_loc]
    
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
        locations=locations,
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
    fig_R = bk.figure(x_range=axis.x_range, 
                      toolbar_location=None, plot_height=plot_height, 
                      plot_width=plot_width, x_axis_location=None)
    fig_R.circle(x='locations', y='data_R', line_color=None, 
                 fill_color='colors_R', size='sizes_R', source=source)
    fig_R.line(x='locations', y='data_R', line_color='black', source=source)
    fig_R.yaxis.axis_label = 'R'
    fig_R.yaxis.minor_tick_line_color=None
    fig_R.ygrid.grid_line_color=None

    #B
    fig_B = bk.figure(x_range=axis.x_range, toolbar_location=None, x_axis_location=None,
                   plot_height=plot_height+25, plot_width=plot_width, title=title)
        
    fig_B.circle(x='locations', y='data_B', line_color=None, 
                 fill_color='colors_B', size='sizes_B', source=source)
    fig_B.line(x='locations', y='data_B', line_color='black', source=source)
    fig_B.yaxis.axis_label = 'B'
    fig_B.ygrid.grid_line_color=None
    fig_B.yaxis.minor_tick_line_color=None

    #Z
    fig_Z = bk.figure(x_range=axis.x_range, toolbar_location=None, x_axis_location=None,
                   plot_height=plot_height, plot_width=plot_width)

    fig_Z.circle(x='locations', y='data_Z', line_color=None, 
                 fill_color='colors_Z', size='sizes_Z', source=source)
    fig_Z.line(x='locations', y='data_Z', line_color='black', source=source)
    fig_Z.yaxis.axis_label = 'Z'
    fig_Z.ygrid.grid_line_color=None
    fig_Z.yaxis.minor_tick_line_color=None

    fig = gridplot([[fig_B], [fig_R], [fig_Z], [axis]], toolbar_location=None)
    
    return fig
