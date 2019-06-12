import numpy as np
import bokeh.plotting as bk
from bokeh.models import ColumnDataSource, Whisker
from bokeh.layouts import column
from bokeh.models.tickers import FixedTicker
from astropy.table import Table

def plot_camera_qa(table, attribute, height=225, width=450, title=None, line0 = True, minmax=None):
    astrotable = Table(table)
    if title is None:
        title=attribute

    cam_figs=[]
    colors = {"B":"blue", "R":"red", "Z":"green"}
    for cam in ["B", "R", "Z"]:
        cam_table = astrotable[astrotable["CAM"]==cam]
        fig = bk.figure(plot_height=height, plot_width=width, title = title+" "+cam)
        source = ColumnDataSource(data=dict(
            SPECTRO = cam_table["SPECTRO"],
            MEANattr = cam_table["MEAN"+attribute],
            MINattr = cam_table["MIN"+attribute],
            MAXattr = cam_table["MAX"+attribute]
        ))
        fig.circle(source=source, x="SPECTRO", y="MEANattr", size=10, color=colors[cam])
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
        fig.yaxis.axis_label = attribute
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
                from bokeh.models import BoxAnnotation
                fig.add_layout(BoxAnnotation(
                    bottom=ymin, top=ymax,
                    fill_color='green', fill_alpha=0.1)
                    )
                tmp = max(abs(attrmin), abs(attrmax))
                fig.y_range.start = -tmp * 1.1
                fig.y_range.end = tmp * 1.1

        cam_figs += [fig]
    return column(cam_figs)
