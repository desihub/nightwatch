import numpy as np

import bokeh
import bokeh.plotting as bk
from bokeh.models.tickers import FixedTicker
from bokeh.models.ranges import FactorRange
from bokeh.models import (
    LinearColorMapper, ColorBar, ColumnDataSource, OpenURL,
    NumeralTickFormatter, AdaptiveTicker,
    TapTool, Div, HoverTool, Range1d, BoxAnnotation, Whisker, Band,
    ResetTool, BoxZoomTool, OpenURL)
from bokeh.models.callbacks import CustomJS
import bokeh.palettes
from bokeh.layouts import column, gridplot

def get_amp_colors(data, lower_err, lower, upper, upper_err):
    '''takes in per amplifier data and the acceptable threshold for that metric.
    Args: 
        data: array of amplifier metric data 
        lower_err: array of lower thresholds that trigger errors
        lower: array of lower thresholds that trigger warnings
        upper: array of upper thresholds that trigger warnings
        upper_err: array of upper thresholds that trigger errors
    Output: array of colors to be put into a ColumnDataSource
    '''
    colors = []
    for i in range(len(data)):
        if lower[i] == None or upper[i] == None:
            continue
        if data[i] <= lower_err[i]:
            colors.append('red')
        if data[i] > lower_err[i] and data[i] <= lower[i]:
            colors.append('orange')
        if data[i] > lower[i] and data[i] < upper[i]:
            colors.append('black')
        if data[i] >= upper[i] and data[i] < upper_err[i]:
            colors.append('orange')
        if data[i] >= upper_err[i]:
            colors.append('red')
    return colors

def get_amp_size(data, lower_err, lower, upper, upper_err):
    '''takes in per amplifier data and the acceptable threshold for that metric
    Args: 
        data: array of amplifier metric data 
        lower_err: array of lower thresholds that trigger errors
        lower: array of lower thresholds that trigger warnings
        upper: array of upper thresholds that trigger warnings
        upper_err: array of upper thresholds that trigger errors
    Output: array of sizes for markers to be put into a ColumnDataSource
    '''
    sizes = []
    for i in range(len(data)):
        if lower[i] == None or upper[i] == None:
            continue
        if data[i] <= lower_err[i]:
            sizes.append('9')
        if data[i] > lower_err[i] and data[i] <= lower[i]:
            sizes.append('9')
        if data[i] > lower[i] and data[i] < upper[i]:
            sizes.append('5')
        if data[i] >= upper[i] and data[i] < upper_err[i]:
            sizes.append('9')
        if data[i] >= upper_err[i]:
            sizes.append('9')
    return sizes

def isolate_spec_lines(data_locs, data):
    '''function to generate isolated data sets so that each spectrograph has an isolated line.
    Inputs:
        data_locs: list of (spec, amp) pairs
        data: the metric data to be plotted (array)
    Output: 
        spec_groups (groupings of amplifiers per spec), data_groups (the data corresponding to those amps) (arrays)'''
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

def plot_amp_cam_qa(data, name, cam, labels, title, lower=None, upper=None,
    amp_keys=None, ymin=None, ymax=None, plot_height=80, plot_width=700):
    '''Plot a per-camera, per-amp visualization of data[name]
    Args:
        data: table of per_amp qa data
        name: metric being plotted (string)
        cam: camera being plotted ('B', 'R', 'Z')
        labels: list of (spec, amp) pairs for x-axis
        title: string
    Options:
        lower: list of lower thresholds per camera from get_thresholds()
            format: [[lower_errB, lowerB], [lower_errR, lowerR], [lower_errZ, lowerZ]]
        upper: list of upper thresholds per camera from get_thresholds()
            format : [[upperB, upper_errB], [upperR, upper_errR], [upperZ, upper_errZ]]
        amp_keys: list of amps that have data
        ymin/ymax: y-axis ranges *unless* the data exceeds those ranges
        plot_height, plot_width: height, width of graph in pixels
    Output:
        Bokeh figure object
        '''
    
    if title is None:
        title = name

    #unpacking data
    spec_loc = []
    amp_loc = []
    name_data = []
    data_val = []
    for row in data:
        if row['CAM'] in (cam, cam.encode('utf-8')):
            if isinstance(row['AMP'], bytes):
                amp_loc.append(row['AMP'].decode('utf-8'))
            else:
                amp_loc.append(row['AMP'])
            spec_loc.append(str(row['SPECTRO']))
            data_val.append(row[name])
            if isinstance(row['CAM'], bytes):
                cam_spect = row['CAM'].lower().decode("utf-8") + str(row['SPECTRO'])
            else:
                cam_spect = row['CAM'].lower() + str(row['SPECTRO'])
            name_data += ["preproc-{cam_spect}-{expid}".format(cam_spect=cam_spect, expid='%08d'%row['EXPID'])]
        else:
            continue
    _, ids = np.unique(spec_loc, return_index=True)
    spec_loc = np.array(spec_loc)[np.sort(ids)]
    _, ids = np.unique(amp_loc, return_index=True)
    amp_loc = np.array(amp_loc)[np.sort(ids)]
    
    locations_to_sort = [str(spec+amp) for spec in spec_loc for amp in amp_loc]
    sorted_ids = np.argsort(locations_to_sort)
    name_data = np.array(name_data)[sorted_ids]
    data_val = np.array(data_val)[sorted_ids]
    locations = [(spec, amp) for spec in np.sort(spec_loc) for amp in np.sort(amp_loc)]
    
    cam_vals = {'B':0, 'R':1, 'Z':2}
    colors = []
    sizes = []
    lower_err = []
    lower_warn = []
    upper_warn = []
    upper_err = []
    
    if (lower is not None) and (upper is not None) and (amp_keys is not None):
        cam_val = cam_vals[cam]
        lower_err += lower[cam_val][0]
        lower_warn += lower[cam_val][1]
        upper_warn += upper[cam_val][0]
        upper_err += upper[cam_val][1]
        cam_amp_keys = amp_keys[cam_val]
        
        if name in ['COSMICS_RATE']:
            lower_err = [lower_err]*len(data_val)
            lower_warn = [lower_warn]*len(data_val)
            upper_warn = [upper_warn]*len(data_val)
            upper_err = [upper_err]*len(data_val)
    
        if name in ['READNOISE', 'BIAS']:
            ids = []
            for i in range(len(cam_amp_keys)):
                if cam_amp_keys[i][0] == cam:
                    if (cam_amp_keys[i][1], cam_amp_keys[i][2]) in locations:
                        ids.append(i)
                else:
                    continue

            lower_warn = np.array(lower_warn)[ids]
            lower_err = np.array(lower_err)[ids]
            upper_warn = np.array(upper_warn)[ids]
            upper_err = np.array(upper_err)[ids]
        
        colors += get_amp_colors(data_val, lower_err, lower_warn, upper_warn, upper_err)
        sizes += get_amp_size(data_val, lower_err, lower_warn, upper_warn, upper_err)

    source = ColumnDataSource(data=dict(
        data_val=data_val,
        locations=locations,
        colors=colors,
        sizes=sizes,
        name=name_data,
        lower=lower_warn,
        upper=upper_warn,
    ))

    #plotting
    axis = bk.figure(x_range=FactorRange(*labels), toolbar_location=None, 
                     plot_height=50, plot_width=plot_width,
                     y_axis_location=None)
    
    hover= HoverTool(names=["circles"], tooltips = [
        ('(spec, amp)', '@locations'),
        ('{}'.format(name), '@data_val')],
                      line_policy='nearest')

    fig = bk.figure(x_range=axis.x_range, plot_height=plot_height,
                    plot_width=plot_width, x_axis_location=None, 
                    tools=[hover, 'tap', 'reset', 'box_zoom', 'pan'])

    spec_groups, data_groups = isolate_spec_lines(locations, data_val)
    for i in range(len(spec_groups)):
        fig.line(x=spec_groups[i], name='lines', y=data_groups[i], line_color='black', alpha=0.25)

    if len(colors) != 0 and len(sizes) != 0:
        fig.circle(x='locations', y='data_val', line_color=None, 
                   fill_color='colors', size='sizes', source=source, name='circles')
    else:
        fig.circle(x='locations', y='data_val', line_color=None, 
                   fill_color='black', size=4, source=source, name='circles')

    if len(data_val)>0 :
        plotmin = min(ymin, np.min(data_val)*0.9) if ymin is not None else np.min(data_val) * 0.9
        plotmax = max(ymax, np.max(data_val)*1.1) if ymax is not None else np.max(data_val) * 1.1
    else :
        plotmin = ymin
        plotmax = ymax
    fig.y_range = Range1d(plotmin, plotmax)
    
    #- style visual attributes
    fig.yaxis.axis_label = cam
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
    
    if lower is not None and upper is not None:
        #fig.add_layout(Whisker(source=source, base='locations', upper='upper', lower='lower', line_alpha=0.3))
        fig.add_layout(Band(base='locations', lower='lower', upper='upper', source=source, level='underlay',
            fill_alpha=0.2, fill_color='green', line_width=0.7, line_color='black'))
    
#         if name in ['COSMICS_RATE']:
#             fig.add_layout(BoxAnnotation(bottom=lower_warn[0][0], top=upper_warn[0][0], fill_alpha=0.1, fill_color='green'))
    
    url = '@name'+'-4x.html'
    taptool = fig.select(type=TapTool)
    taptool.names = ['circles']
    taptool.callback = OpenURL(url=url)
    
    return fig

def plot_amp_qa(data, name, lower=None, upper=None, amp_keys=None, title=None, plot_height=80, plot_width=700, ymin=None, ymax=None):
    '''Creates gridplot of 3 camera separated amp plots
    Args:
        data: table of per_amp qadata
        name: metric being plotted (str)
    Options:
        lower: list of lower thresholds per camera from get_thresholds()
            format: [[lower_errB, lowerB], [lower_errR, lowerR], [lower_errZ, lowerZ]]
        upper: list of upper thresholds per camera from get_thresholds()
            format : [[upperB, upper_errB], [upperR, upper_errR], [upperZ, upper_errZ]]
        amp_keys: list of amps that have data
        title: title for plot, if different than name (str)
        plot_height, plot_width: height, width of graph in pixels
        ymin/ymax: lists of y axis ranges for B, R, Z plots, unless data exceeds these
    Output:
        Bokeh gridplot object'''
    
    if title == None:
        title = name
        
    labels = [(spec, amp) for spec in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'] for amp in ['A', 'B', 'C', 'D']]
    
    figs = []
    for cam in ['B', 'R', 'Z']:
        if cam == 'B':
            fig = plot_amp_cam_qa(data, name, cam, labels, title, lower=lower, upper=upper, amp_keys=amp_keys, plot_height=plot_height+25, plot_width=plot_width, ymin=ymin[0], ymax=ymax[0])
        if cam == 'R':
            fig = plot_amp_cam_qa(data, name, cam, labels, title, lower=lower, upper=upper, amp_keys=amp_keys, plot_height=plot_height, plot_width=plot_width, ymin=ymin[1], ymax=ymax[1])
        if cam == 'Z':
            fig = plot_amp_cam_qa(data, name, cam, labels, title, lower=lower, upper=upper, amp_keys=amp_keys, plot_height=plot_height, plot_width=plot_width, ymin=ymin[2], ymax=ymax[2])
            
        
        if name == "BIAS":
            fig.yaxis.ticker = AdaptiveTicker(base=10, desired_num_ticks=5, 
                                              mantissas=np.arange(1, 5.5, 0.5), 
                                              min_interval=1)
            fig.yaxis.formatter = NumeralTickFormatter(format='e')
        else:
            fig.yaxis.ticker = AdaptiveTicker(base=10, desired_num_ticks=5, 
                                              mantissas=np.arange(1, 5.5, 0.5), 
                                              min_interval=1)
            fig.yaxis.formatter = NumeralTickFormatter(format='a')
        figs.append(fig)
    
    # x-axis labels for spectrograph 0-9 and amplifier A-D
    axis = bk.figure(x_range=FactorRange(*labels), toolbar_location=None,
                     plot_height=50, plot_width=plot_width,
                     y_axis_location=None)
    axis.line(x=labels, y=0, line_color=None)
    axis.grid.grid_line_color=None
    axis.outline_line_color=None

    fig = gridplot([[figs[0]], [figs[1]], [figs[2]], [axis]], toolbar_location='right')

    return fig
