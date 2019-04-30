import numpy as np

import jinja2

import bokeh
import bokeh.plotting as bk
from bokeh.embed import components
from bokeh.models.tickers import FixedTicker
from bokeh.models.ranges import FactorRange
from bokeh.models import LinearColorMapper, ColorBar
import bokeh.palettes

from .core import default_css

def write_amp_html(data, outfile, header):
    '''TODO: document'''
    
    night = header['NIGHT']
    expid = header['EXPID']
    flavor = header['FLAVOR'].rstrip()
    if "PROGRAM" not in header :
        program = "no program in header!"
    else :
        program = header['PROGRAM'].rstrip()
    exptime = header['EXPTIME']
    
    html_template = '''
    <!DOCTYPE html>
    <html lang="en-US">

    <link
        href="https://cdn.pydata.org/bokeh/release/bokeh-{version}.min.css"
        rel="stylesheet" type="text/css"
    >
    <link
        href="https://cdn.pydata.org/bokeh/release/bokeh-tables-{version}.min.css"
        rel="stylesheet" type="text/css"
    >
    <script src="https://cdn.pydata.org/bokeh/release/bokeh-{version}.min.js"></script>
    <script src="https://cdn.pydata.org/bokeh/release/bokeh-tables-{version}.min.js"></script>

    <head>
    <style>
    {default_css}
    </style>
    </head>

    <body>
    <h1>Night {night} exposure {expid}</h1>
    <p>{exptime:.0f} second {flavor} ({program}) exposure</p>
    <h2>Per-amplifier QA metrics</h2>

    '''.format(version=bokeh.__version__, night=night, expid=expid,
        exptime=exptime, flavor=flavor, program=program,
        default_css=default_css)
    
    html_template += '''
    <div>{{ READNOISE_script }} {{ READNOISE_div }}</div>
    <div>{{ BIAS_script }} {{ BIAS_div }}</div>
    <div>{{ COSMICS_RATE_script }} {{ COSMICS_RATE_div }}</div>
    </body>
    </html>
    '''
    
    #- Add a basic set of PER_AMP QA plots
    plot_components = dict()
    for qaname, qatitle in [
            ['READNOISE', 'CCD Amplifier Read Noise'],
            ['BIAS', 'CCD Amplifier Overscan Bias Level'],
        ]:
        fig = plot_amp_qa(data, qaname, title=qatitle)
        script, div = components(fig)
        plot_components[qaname+'_script'] = script
        plot_components[qaname+'_div'] = div
        
    #- COSMICS_RATE could have been in the loop above, but demonstrating the
    #- steps of adding a plot separately in case it needs any customization:
    
    #- Generate the bokeh figure
    fig = plot_amp_qa(data, 'COSMICS_RATE',
        title='CCD Amplifier cosmics per minute',
        palette=bokeh.palettes.all_palettes['RdYlGn'][11][1:-1],
        qamin=0, qamax=50)

    #- Get the components to embed in the HTML
    script, div = components(fig)

    #- Add those to the dictionary that will be passed to the HTML template
    plot_components['COSMICS_RATE_script'] = script
    plot_components['COSMICS_RATE_div'] = div

    #- Combine template + components -> HTML
    html = jinja2.Template(html_template).render(**plot_components)

    #- Write HTML text to the output file
    with open(outfile, 'w') as fx:
        fx.write(html)

def plot_amp_qa(data, name, title=None, palette="YlGn9", qamin=None, qamax=None):
    '''
    Plot a per-amp visualization of data[name]

    qamin/qamax: min/max ranges for the color scale
    '''
    if title is None:
        title = name
     
    #- Map data[name] into location on image to display
    img = np.zeros(shape=(4,30)) * np.nan
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
                    toolbar_location=None, title=title)

    if (qamin is not None) or (qamax is not None):
        if qamin is None:
            qamin = np.min(img)
        if qamax is None:
            qamax = np.max(img)
        color_mapper = LinearColorMapper(palette=palette, low=qamin, high=qamax)
        fig.image(image=[img,], x=0, y=0, dw=15, dh=4, color_mapper=color_mapper)
    else:
        fig.image(image=[img,], x=0, y=0, dw=15, dh=4, palette=palette)

    #
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
    
    return fig

