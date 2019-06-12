import numpy as np

import bokeh
import bokeh.plotting as bk
from bokeh.models.tickers import FixedTicker
from bokeh.models.ranges import FactorRange
from bokeh.models import LinearColorMapper, ColorBar, ColumnDataSource, OpenURL, TapTool
import bokeh.palettes
from bokeh.layouts import column, gridplot

def plot_amp_qa(data, name, title=None, palette="YlGn9", 
                qamin=None, qamax=None, plot_height=100, 
                plot_width=500):
    '''Plot a per-amp visualization of data[name]
    qamin/qamax: min/max ranges for the color scale'''
    
    if title is None:
        title = name
        
    #unpacking data
    spec_labels = []
    amp_labels = []
    data_R = []
    data_B = []
    data_Z = []
    for row in data:
        if row['CAM'] in ('R', b'R'):
            amp_labels.append(row['AMP'].decode('utf-8'))
            spec_labels.append(str(row['SPECTRO']))
            data_R.append(row[name])
        if row['CAM'] in ('B', b'B'):
            data_B.append(row[name])
        if row['CAM'] in ('Z', b'Z'):
            data_Z.append(row[name])
    labels = [(spec, amp) for spec in np.unique(spec_labels) for amp in amp_labels]
    
    source = ColumnDataSource(data=dict(
        data_R=data_R,
        data_B=data_B,
        data_Z=data_Z,
        labels=labels,
    ))
    
    #x-axis
    axis = bk.figure(x_range=FactorRange(*labels), toolbar_location=None, 
                     plot_height=50, plot_width=plot_width,
                     y_axis_location=None)         
    axis.line(x=labels, y=0, line_color=None)
    axis.grid.grid_line_color=None
    axis.outline_line_color=None
    
    #R
    fig_R = bk.figure(x_range=axis.x_range, toolbar_location=None, 
               plot_height=plot_height, plot_width=plot_width,
               x_axis_location=None)

    if qamin is None:
        qamin = np.min(data[name])
    if qamax is None:
        qamax = np.max(data[name])
    
    color_mapper = LinearColorMapper(palette=palette, low=qamin, high=qamax,
                                     low_color='#CC1111', high_color='#CC1111')   

    fig_R.circle(x='labels', y='data_R', line_color=None, 
                 fill_color={'field':'data_R', 'transform':color_mapper}, size=8, source=source)
    fig_R.line(x='labels', y='data_R', line_color='black', source=source)
    fig_R.yaxis.axis_label = 'R'
    fig_R.yaxis.minor_tick_line_color=None
    fig_R.ygrid.grid_line_color=None

    #B
    fig_B = bk.figure(x_range=fig_R.x_range,
                   toolbar_location=None, x_axis_location=None,
                   plot_height=plot_height, plot_width=plot_width)
        
    fig_B.circle(x='labels', y='data_B', line_color=None, 
                 fill_color={'field':'data_B', 'transform':color_mapper}, size=8, source=source)
    fig_B.line(x='labels', y='data_B', line_color='black', source=source)
    fig_B.yaxis.axis_label = 'B'
    fig_B.ygrid.grid_line_color=None
    fig_B.yaxis.minor_tick_line_color=None

    #Z
    fig_Z = bk.figure(x_range=fig_R.x_range,
                   toolbar_location=None, x_axis_location=None,
                   plot_height=plot_height, plot_width=plot_width)

    fig_Z.circle(x='labels', y='data_Z', line_color=None, 
                 fill_color={'field':'data_Z', 'transform':color_mapper}, size=8, source=source)
    fig_Z.line(x='labels', y='data_Z', line_color='black', source=source)
    fig_Z.yaxis.axis_label = 'Z'
    fig_Z.ygrid.grid_line_color=None
    fig_Z.yaxis.minor_tick_line_color=None

    fig = gridplot([[fig_R], [fig_B], [fig_Z], [axis]])
    
    return fig
