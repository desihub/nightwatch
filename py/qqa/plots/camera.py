import bokeh.plotting as bk
from bokeh.models import ColumnDataSource, Whisker
from bokeh.layouts import column

def plot_camera_qa(table_by_camfiber, attribute, title=None):
    if title is None:
        title=attribute

    cam_figs=[]
    for cam in ["B", "R", "Z"]:
        cam_table = table_by_camfiber[table_by_camfiber["CAM"]==cam]
        fig = bk.figure(plot_height=250, title = title+" "+cam)
        source = ColumnDataSource(data=dict(
            SPECTRO = cam_table["SPECTRO"],
            MEANattr = cam_table["MEAN"+attribute],
            MINattr = cam_table["MIN"+attribute],
            MAXattr = cam_table["MAX"+attribute]
        ))
        fig.circle(source=source, x="SPECTRO", y="MEANattr", size=10)
        fig.circle(source=source, x="SPECTRO", y="MAXattr", fill_alpha=0, line_alpha=0)
        fig.circle(source=source, x="SPECTRO", y="MINattr", fill_alpha=0, line_alpha=0)
        fig.line(source=source, x="SPECTRO", y=0)
        fig.add_layout(
            Whisker(source=source, base="SPECTRO", upper="MAXattr", lower="MINattr")
        )
        cam_figs += [fig]
    return column(cam_figs)
