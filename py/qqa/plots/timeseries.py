from astropy.table import Table, vstack
import numpy as np
import os, re
import fitsio
import bokeh.plotting as bk
from bokeh.layouts import column
from bokeh.models import TapTool as TapTool
from bokeh.models import OpenURL, ColumnDataSource, HoverTool

def generate_timeseries(data_dir, start_date, end_date, aspect):
    """
    Include start_date and end_date in data generation
    """
    start_date = str(start_date).zfill(8)
    end_date = str(end_date).zfill(8)
    
    list_tables = []
    
    avaliable_dates = []
    i,j,y = os.walk(data_dir).__next__()
    for dir in j:
        if (start_date <= dir and end_date >= dir):
            avaliable_dates += [os.path.join(i, dir)]
 
    for date in avaliable_dates:
        for i,j,y in os.walk(date):
            for file in y:
                if re.match(r"qa-[0-9]{8}.fits", file):
                    #print(fitsio.FITS(os.path.join(i, file))[1].read())
                    list_tables += [fitsio.read(os.path.join(i, file), "PER_AMP", columns=["SPECTRO", "CAM", "AMP", "EXPID", "NIGHT", aspect])]
    
    if list_tables == []:
        return None
    #table = vstack(list_tables, metadata_conflicts='silent')
    table = None
    for tab in list_tables:
        if table is None:
            table = tab
        else:
            table = np.append(table, tab)

    #print(table["NIGHT"])
    table = Table(table)
    table.sort("EXPID") # axis
    table_by_amp = table.group_by(["SPECTRO", "CAM", "AMP"]).groups.aggregate(list)
    
    cam_figs = []
    for cam in ["B", "R", "Z"]:
        cam_table = table_by_amp[table_by_amp["CAM"] == cam]
        fig = bk.figure(title=cam, plot_height = 200, plot_width = 500)
        for row in cam_table:
            length = len(row["EXPID"])
            source = ColumnDataSource(data=dict(
                SPECTRO = [str(row["SPECTRO"])]*length,
                AMP = [row["AMP"]]*length,
                EXPID = row["EXPID"],
                NIGHT = row["NIGHT"],
                aspect_values = row[aspect]
            ))
            fig.line("EXPID", "aspect_values", source=source)
            fig.circle("EXPID", "aspect_values", size=7.5, source=source)
        hover = HoverTool(
            tooltips=[
                ("SPECTRO", "@SPECTRO"),
                ("AMP", "@AMP"),
                ("NIGHT", "@NIGHT"),
                ("EXPID", "@EXPID"),
                (aspect, "@aspect_values")
            ]
        )
        fig.add_tools(hover)
        cam_figs += [fig]
    
    return column(cam_figs)
