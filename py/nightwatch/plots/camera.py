import numpy as np
import bokeh.plotting as bk
from bokeh.models import ColumnDataSource, Whisker, BoxAnnotation
from bokeh.layouts import column
from bokeh.models.tickers import FixedTicker
from astropy.table import Table


def get_qa_colors(data, lower_err, lower, upper, upper_err, basecolor='black'):
    '''takes in camera QA data and the acceptable threshold for that metric.
    Args: 
        data: array of QA data 
        lower_err: array of lower thresholds that trigger errors
        lower: array of lower thresholds that trigger warnings
        upper: array of upper thresholds that trigger warnings
        upper_err: array of upper thresholds that trigger errors
    Output: array of colors to be put into a ColumnDataSource
    '''
    colors = []
    for i in range(len(data)):
        if lower == None or upper == None:
            continue
        if data[i] <= lower_err:
            colors.append('red')
        if data[i] > lower_err and data[i] <= lower:
            colors.append('orange')
        if data[i] > lower and data[i] < upper:
            colors.append(basecolor)
        if data[i] >= upper and data[i] < upper_err:
            colors.append('orange')
        if data[i] >= upper_err:
            colors.append('red')
    return colors


def get_qa_size(data, lower_err, lower, upper, upper_err):
    '''takes in camera QA data and the acceptable threshold for that metric
    Args: 
        data: array of QA data
        lower_err: array of lower thresholds that trigger errors
        lower: array of lower thresholds that trigger warnings
        upper: array of upper thresholds that trigger warnings
        upper_err: array of upper thresholds that trigger errors
    Output: array of sizes for markers to be put into a ColumnDataSource
    '''
    sizes = []
    for i in range(len(data)):
        if lower == None or upper == None:
            continue
        if data[i] <= lower_err:
            sizes.append('9')
        if data[i] > lower_err and data[i] <= lower:
            sizes.append('9')
        if data[i] > lower and data[i] < upper:
            sizes.append('4')
        if data[i] >= upper and data[i] < upper_err:
            sizes.append('9')
        if data[i] >= upper_err:
            sizes.append('9')
    return sizes


def plot_camera_qa(table, attribute, unit=None, lower=None, upper=None, height=225, width=450, title=None, line0 = True, minmax=None):
    '''
    Creates 3 plots of an attribute vs Spectrograph number, corresponding to
    R, B, Z cameras.

    Args :
        table : PER_CAMERA table (can be astropy table or just numpy matrix)
        attribute : string that is a column name of table

    Options :
        unit : string that gives the column units
        lower : list of lower per_camera thresholds from thresholds.get_thresholds()
            format: [[lower_errB, lowerB], [lower_errR, lowerR], [lower_errZ, lowerZ]]
        upper : list of upper per_camera thresholds from thresholds.get_thresholds() 
            format : [[upperB, upper_errB], [upperR, upper_errR], [upperZ, upper_errZ]]
        height : height of each plot
        width : width of each plot
        title : title + " " + cam is the title for each figure
        line0 : if True, plot a line at x=0
        minmax : range of fixed y range

    Returns :
        Bokeh figure that contains three vertically stacked plots
    '''
    astrotable = Table(table)
    if title is None:
        title=attribute

    cam_figs=[]

    camcolors = {"B":"blue", "R":"red", "Z":"green"}
    keys = {'B':0, 'R':1, 'Z':2}
    for cam in 'BRZ':
        
        cam_table = astrotable[astrotable["CAM"]==cam]

        if len(cam_table) == 0:
            #- Create placeholder fig if not data for this camera
            fig = bk.figure(plot_height=height, plot_width=width, title='No {} data'.format(cam))
            continue

        fig = bk.figure(plot_height=height, plot_width=width, title = title+" "+cam, tools=['reset', 'box_zoom', 'pan'])

        if attribute == 'DX' or attribute == 'DY':
            k = keys[cam]
            lower_err  = lower[k][0][0]
            lower_warn = lower[k][1][0]
            upper_warn = upper[k][0][0]
            upper_err  = upper[k][1][0]

            colors = get_qa_colors(cam_table['MEAN'+attribute], lower_err, lower_warn, upper_warn, upper_err, basecolor=camcolors[cam])
            sizes = get_qa_size(cam_table['MEAN'+attribute], lower_err, lower_warn, upper_warn, upper_err)

            source = ColumnDataSource(data=dict(
                SPECTRO = cam_table["SPECTRO"],
                MEANattr = cam_table["MEAN"+attribute],
                MINattr = cam_table["MIN"+attribute],
                MAXattr = cam_table["MAX"+attribute],
                colors = colors,
                sizes = sizes
            ))

            fig.circle(source=source, x="SPECTRO", y="MEANattr", color='colors', size='sizes')
        else:
            source = ColumnDataSource(data=dict(
                SPECTRO = cam_table["SPECTRO"],
                MEANattr = cam_table["MEAN"+attribute],
                MINattr = cam_table["MIN"+attribute],
                MAXattr = cam_table["MAX"+attribute]
            ))
            fig.circle(source=source, x="SPECTRO", y="MEANattr", color=camcolors[cam])

        fig.circle(source=source, x="SPECTRO", y="MAXattr", fill_alpha=0, line_alpha=0)
        fig.circle(source=source, x="SPECTRO", y="MINattr", fill_alpha=0, line_alpha=0)
        if line0:
            fig.line(source=source, x="SPECTRO", y=0)
        fig.add_layout(
            Whisker(source=source, base="SPECTRO", upper="MAXattr", lower="MINattr")
        )
        fig.xaxis.ticker = FixedTicker(ticks=[i for i in range(0, 10, 1)])
        if cam == 'Z':
            fig.xaxis.axis_label = "Spectrograph number"
            fig.plot_height = height+25

        if unit is None:
            fig.yaxis.axis_label = attribute
        else:
            fig.yaxis.axis_label = f'{attribute}  ({unit})'
        
        if lower is not None and upper is not None:
            mean_range = BoxAnnotation(bottom=lower[keys[cam]][1][0], top=upper[keys[cam]][0][0], fill_color='green', fill_alpha=0.1)
            max_range = BoxAnnotation(bottom=upper[keys[cam]][0][0], top=upper[keys[cam]][1][0], fill_color='yellow', fill_alpha=0.1)
            min_range = BoxAnnotation(bottom=lower[keys[cam]][0][0], top=lower[keys[cam]][1][0], fill_color='yellow', fill_alpha=0.1)
            fig.add_layout(mean_range)
            fig.add_layout(min_range)
            fig.add_layout(max_range)
        
        if minmax is not None:
            ymin, ymax = minmax
            attrmin = np.min(cam_table["MIN"+attribute])
            attrmax = np.max(cam_table["MAX"+attribute])

            #- Data ranges are within minmax
            if ymin < attrmin and ymax > attrmax:
                fig.y_range.start = ymin
                fig.y_range.end = ymax
            #- Otherwise default to using data range
            else:
                tmp = max(abs(attrmin), abs(attrmax))
                fig.y_range.start = -tmp * 1.1
                fig.y_range.end = tmp * 1.1

        cam_figs += [fig]
    return column(cam_figs)
