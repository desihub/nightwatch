import numpy as np
import bokeh.plotting as bk
from bokeh.models import ColumnDataSource, Whisker, BoxAnnotation
from bokeh.layouts import column
from bokeh.models.tickers import FixedTicker
from astropy.table import Table

def plot_camera_qa(table, attribute, lower=None, upper=None, height=225, width=450, title=None, line0 = True, minmax=None):
    '''
    Creates 3 plots of an attribute vs Spectrograph number, corresponding to
    R, B, Z cameras.

    Args :
        table : PER_CAMERA table (can be astropy table or just numpy matrix)
        attribute : string that is a column name of table

    Options :
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

    colors = {"B":"blue", "R":"red", "Z":"green"}
    keys = {'B':0, 'R':1, 'Z':2}
    for cam in ["B", "R", "Z"]:
        
        cam_table = astrotable[astrotable["CAM"]==cam]

        if len(cam_table) == 0:
            #- Create placeholder fig if not data for this camera
            fig = bk.figure(plot_height=height, plot_width=width, title='No {} data'.format(cam))
            continue

        fig = bk.figure(plot_height=height, plot_width=width, title = title+" "+cam, tools=['reset', 'box_zoom', 'pan'])
        source = ColumnDataSource(data=dict(
            SPECTRO = cam_table["SPECTRO"],
            MEANattr = cam_table["MEAN"+attribute],
            MINattr = cam_table["MIN"+attribute],
            MAXattr = cam_table["MAX"+attribute]
        ))
        fig.circle(source=source, x="SPECTRO", y="MEANattr", color=colors[cam])
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
        fig.yaxis.axis_label = attribute
        
        if lower is not None and upper is not None:
            mean_range = BoxAnnotation(bottom=lower[keys[cam]][1][0], top=upper[keys[cam]][0][0], fill_color='green', fill_alpha=0.1)
            max_range = BoxAnnotation(bottom=upper[keys[cam]][0][0], top=upper[keys[cam]][0][0]+upper[keys[cam]][1][0], fill_color='yellow', fill_alpha=0.1)
            min_range = BoxAnnotation(bottom=lower[keys[cam]][0][0]+lower[keys[cam]][1][0], top=lower[keys[cam]][1][0], fill_color='yellow', fill_alpha=0.1)
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
#                 fig.add_layout(BoxAnnotation(
#                     bottom=ymin, top=ymax,
#                     fill_color='green', fill_alpha=0.1)
#                     )
                tmp = max(abs(attrmin), abs(attrmax))
                fig.y_range.start = -tmp * 1.1
                fig.y_range.end = tmp * 1.1

        cam_figs += [fig]
    return column(cam_figs)
