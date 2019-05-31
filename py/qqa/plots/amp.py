import numpy as np

import bokeh
import bokeh.plotting as bk
from bokeh.models.tickers import FixedTicker
from bokeh.models.ranges import FactorRange
from bokeh.models import LinearColorMapper, ColorBar, ColumnDataSource, OpenURL, TapTool
import bokeh.palettes

def plot_amp_qa(data, name, title=None, palette="YlGn9", qamin=None, qamax=None):
    '''
    Plot a per-amp visualization of data[name]

    qamin/qamax: min/max ranges for the color scale
    '''
    if title is None:
        title = name

    #- Map data[name] into location on image to display
    img = np.zeros(shape=(4,30)) * np.nan
    x_data = []
    y_data = []
    name_data = []
    for row in data:
        #- TODO: check rows for amp, spectro, and img plotting orientation
        if row['SPECTRO'] < 5:
            i = 2
        else:
            i = 0
        if row['AMP'] in ['C', 'D', b'C', b'D']:
            i += 1

        j = 6*(row['SPECTRO'] % 5)
        if row['CAM'].upper() in ('R', b'R'):
            j += 2
        elif row['CAM'].upper() in ('Z', b'Z'):
            j += 4

        if row['AMP'] in ['D', 'B', b'D', b'B']:
            j += 1

        x_data += [j/2+.25]
        y_data += [i+.5]
        name_data += [row['CAM'].lower().decode("utf-8") + str(row['SPECTRO'])]
        img[i,j] = row[name]

    splabels_top = list()
    for sp in range(0,5):
        for cam in ['B', 'R', 'Z']:
            splabels_top.append(cam+str(sp))

    splabels_bottom = list()
    for sp in range(5,10):
        for cam in ['B', 'R', 'Z']:
            splabels_bottom.append(cam+str(sp))

    fig = bk.figure(height=180, width=850, x_range=FactorRange(*splabels_bottom),
                    toolbar_location=None, title=title, tools='tap')

    if qamin is None:
        qamin = np.nanmin(img)
    if qamax is None:
        qamax = np.nanmax(img)

    color_mapper = LinearColorMapper(palette=palette, low=qamin, high=qamax,
                                     low_color='#CC1111', high_color='#CC1111')
    fig.image(image=[img,], x=0, y=0, dw=15, dh=4, color_mapper=color_mapper)

    # color_bar = ColorBar(color_mapper=color_mapper)
    # fig.add_layout(color_bar, 'right')
    #     # label_standoff=12, border_line_color=None, location=(0,0))

    for x in [0, 3, 6, 9, 12, 15]:
        fig.line([x,x], [0,4], line_color='black', line_width=4, alpha=0.6)
    for y in [0, 2, 4]:
        fig.line([0, 15], [y, y], line_color='black', line_width=4, alpha=0.6)
    for x in range(1, 15, 1):
        fig.line([x,x], [0,4], line_color='black', line_width=1, line_alpha=0.6)

    #- overplot values
    for y in range(img.shape[0]):
        x = np.arange(img.shape[1])
        text = list()
        for value in img[y]:
            if np.isnan(value):
                text.append('')
            else:
                text.append('{:.1f}'.format(value))

        fig.text(x/2+0.25, y+0.45, text, text_font_size='8pt', text_alpha=0.5, text_align='center', text_baseline='middle')

    # fig.x_range.start, fig.x_range.end = (-0.05, 30.05)
    fig.y_range.start, fig.y_range.end = (-0.05, 4.05)
    fig.yaxis.ticker = FixedTicker(ticks=[])
    fig.yaxis.minor_tick_line_color = None

    #- Add SP0 - SP4 labels along the top
    fig.extra_x_ranges = {"top_spectrographs": FactorRange(*splabels_top)}
    top_axis = bokeh.models.CategoricalAxis(x_range_name="top_spectrographs")

    fig.add_layout(top_axis, 'above')

    #- No ticks; make camera labels close to plot
    fig.xaxis.major_tick_out = 0
    fig.xaxis.major_label_standoff = 5

    source = ColumnDataSource(data=dict(
    x=x_data,
    y=y_data,
    name=name_data,
    ))
    fig.square('x', 'y', line_color='black', fill_alpha=0, size=29, source=source, name="squares")

    taptool = fig.select(type=TapTool)
    taptool.names = ["squares"]
    taptool.callback = OpenURL(url="@name-4x.html")

    return fig
