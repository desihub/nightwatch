from astropy.table import Table#, vstack
import numpy as np
import os, re, sys
import fitsio
import bokeh.plotting as bk
from bokeh.layouts import column
from bokeh.models import TapTool as TapTool
from bokeh.models import OpenURL, ColumnDataSource, HoverTool, CustomJS
from qqa.qa.base import QA

def generate_timeseries(data_dir, start_date, end_date, hdu, aspect):
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
                    #list_tables += [Table.read(os.path.join(i, file), hdu=hdu)]
                    list_tables += [fitsio.read(os.path.join(i, file), hdu, columns=list(QA.metacols[hdu])+[aspect])]

    if list_tables == []:
        return None
    #table = vstack(list_tables, metadata_conflicts='silent')
    table = None
    for tab in list_tables:
        if table is None:
            table = tab
        else:
            table = np.append(table, tab)
    table = Table(table)

    lowest = min(table["EXPID"])
    highest = max(table["EXPID"])

    line_source = ColumnDataSource(data=dict(x=[lowest], lower=[lowest], upper=[highest]))

    # js code is used as the callback for the HoverTool
    js = '''
    /// get mouse data (location of pointer in the plot)
    var geometry = cb_data['geometry'];

    /// get the current value of x in line_source
    var data = line_source.data;
    var x = data['x'];

    /// if the mouse is indeed hovering over the plot, change the line_source value
    if (isFinite(geometry.x) && (geometry.x >= data['lower'][0]) && (geometry.x <= data['upper'][0])) {
      x[0] = geometry.x
      line_source.change.emit();
    }
    '''

    hover_follow = HoverTool(tooltips=None,
                          point_policy='follow_mouse',
                          callback=CustomJS(code=js, args={'line_source': line_source}))

    table.sort("EXPID") # axis

    metacols = QA.metacols

    group_by_list = list(metacols[hdu])
    group_by_list.remove("NIGHT")
    group_by_list.remove("EXPID")
    if group_by_list == []:
        table_by_amp = table
    else:
        table_by_amp = table.group_by(group_by_list).groups.aggregate(list)

    cam_figs = []
    if "CAM" in table_by_amp.colnames:
        colors = {"B":"blue", "R":"red", "Z":"green"}
        group_by_list.remove("CAM")
        for cam in ["B", "R", "Z"]:
            cam_table = table_by_amp[table_by_amp["CAM"] == cam]
            fig = bk.figure(title="CAM "+cam, plot_height = 200, plot_width = 500)
            max_y=None
            min_y=None
            for row in cam_table:
                length = len(row["EXPID"])
                data=dict(
                    EXPID = row["EXPID"],
                    EXPIDZ = [str(expid).zfill(8) for expid in row["EXPID"]],
                    NIGHT = row["NIGHT"],
                    aspect_values = row[aspect]
                )
                for col in group_by_list:
                    data[col] = [str(row[col])]*length
                source = ColumnDataSource(data=data)
                if max_y is None and min_y is None:
                    max_y = max(row[aspect])
                    min_y = min(row[aspect])

                if max(row[aspect]) > max_y:
                    max_y = max(row[aspect])

                if min(row[aspect]) < min_y:
                    min_y = min(row[aspect])
                fig.line("EXPID", "aspect_values", source=source, alpha=0.5, color=colors[cam], name="lines", nonselection_alpha=1, selection_alpha=1)
                fig.circle("EXPID", "aspect_values", size=7.5, source=source, alpha=0.5, color=colors[cam], name="dots", nonselection_fill_alpha=1,)

            tooltips = tooltips=[
                ("NIGHT", "@NIGHT"),
                ("EXPID", "@EXPID")
            ]

            for col in group_by_list:
                tooltips += [(col, "@"+col)]
            tooltips += [(aspect, "@aspect_values")]

            hover = HoverTool(
                names=["dots"],
                tooltips=tooltips
            )

            tap = TapTool(
                names = ["dots"],
                callback = OpenURL(url="../../../../../@NIGHT/@EXPIDZ/qa-amp-@EXPIDZ.html")
            )

            fig.segment(x0='x', y0=min_y, x1='x', y1=max_y, color='grey', line_width=1, source=line_source)
            fig.add_tools(hover)
            fig.add_tools(tap)
            fig.add_tools(hover_follow)
            cam_figs += [fig]

        fig = column(cam_figs)

    else:
        fig = bk.figure(plot_height = 300, plot_width = 750)
        for row in table_by_amp:
            length = len(row["EXPID"])
            data=dict(
                EXPID = row["EXPID"],
                EXPIDZ = [str(expid).zfill(8) for expid in row["EXPID"]],
                NIGHT = row["NIGHT"],
                aspect_values = row[aspect]
            )
            for col in group_by_list:
                data[col] = [str(row[col])]*length
            source = ColumnDataSource(data=data)

            if max_y is None and min_y is None:
                max_y = max(row[aspect])
                min_y = min(row[aspect])

            if max(row[aspect]) > max_y:
                max_y = max(row[aspect])

            if min(row[aspect]) < min_y:
                min_y = min(row[aspect])
            fig.line("EXPID", "aspect_values", source=source, alpha=0.5, name="lines", nonselection_alpha=1, selection_alpha=1)
            fig.circle("EXPID", "aspect_values", size=7.5, source=source, alpha=0.5, name="dots", nonselection_fill_alpha=1,)

        tooltips = tooltips=[
            ("NIGHT", "@NIGHT"),
            ("EXPID", "@EXPID"),
            (aspect, "@aspect_values")
        ]

        for col in group_by_list:
            tooltips += [(col, "@"+col)]
        tooltips += [(aspect, "@aspect_values")]

        hover = HoverTool(
            names=["dots"],
            tooltips=tooltips
        )

        tap = TapTool(
            names = ["dots"],
            callback = OpenURL(url="../../../../@NIGHT/@EXPIDZ/qa-amp-@EXPIDZ.html")
        )

        fig.segment(x0='x', y0=min_y, x1='x', y1=max_y, color='grey', line_width=1, source=line_source)
        fig.add_tools(hover)
        fig.add_tools(tap)
        fig.add_tools(hover_follow)

    return fig
