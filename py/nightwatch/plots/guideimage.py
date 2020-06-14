import sys, os
import numpy as np
from bokeh.embed import components
import jinja2
from astropy.io import fits

import bokeh
import bokeh.plotting as bk
from bokeh.models import ColumnDataSource, OpenURL, HoverTool, CustomJS, Slider, Image, Legend
from bokeh.layouts import column, gridplot
from bokeh.palettes import gray

def guide_star_timelapse(image_data, height=170, width=170, title=None, ncols=8):
    '''
    Args:
        image_data: dictionary containing guide-rois image data
    Options:
        height: height of plot (default = 300)
        width: width of plot (default = 300)
        title: title of plot, only needed if you want a different one than is hardcoded(default = None)
    Returns bokeh layout object.'''
    
    keys = list(image_data.keys())
    indices = range(len(image_data[keys[0]]))

    sources = {}

    for idx in indices:
        imgs = []
        image_names = []
        for key in keys:
            img = [image_data[key][idx]]
            imgs.append(img)
            image_names.append(key)
        sources['_' + str(idx)] = ColumnDataSource(data = dict(zip(
            [name for name in image_names],
            [img for img in imgs],
        )))

    dict_of_sources = dict(zip(
        [idx for idx in indices],
        ['_%s' % idx for idx in indices]
    ))

    js_source_array = str(dict_of_sources).replace("'", "")
    renderer_source = sources['_%s' % indices[0]]

    ims = []
    im_glyphs = []
    im_renderers = []

    for key in keys:
        name_key = key
        title = 'Cam {} Star {}'.format(key[5], key[7])
        im = bk.figure(plot_width=width, plot_height=height+15, x_range = (0, 50), y_range=(0, 50), title=title)
        im.xaxis.visible = False
        im.yaxis.visible = False
        im_glyph = Image(image=name_key, x=0, y=0, dw=50, dh=50)
        im_renderer = im.add_glyph(renderer_source, im_glyph)

        ims.append(im)
        im_glyphs.append(im_glyphs)
        im_renderers.append(im_renderer)

    code = """
        var idx = cb_obj.value,
            sources = %s,
            new_source_data = sources[idx].data;
        renderer_source.data = new_source_data;
    """ % js_source_array

    callback = CustomJS(args=sources, code=code)
    slider = Slider(start=0, end=indices[-1], value=0, step=1, title="Frame", callback=callback, width=width*4)
    callback.args['renderer_source'] = renderer_source
    callback.args['slider'] = slider

    ims_plot = gridplot(ims, ncols=ncols, toolbar_location=None)
    layout = column([slider, ims_plot])
    
    return layout