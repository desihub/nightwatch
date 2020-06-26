import sys, os
import numpy as np
from bokeh.embed import components
import jinja2
from astropy.io import fits
from astropy.visualization import ZScaleInterval

import bokeh
import bokeh.plotting as bk
from bokeh.models import ColumnDataSource, OpenURL, HoverTool, CustomJS, Slider, Image, Legend
from bokeh.models.mappers import LinearColorMapper
from bokeh.layouts import column, gridplot
from bokeh.palettes import gray

def get_all_values(d):
    vals = []
    for key in d.keys():
        for k in d[key].keys():
            vals.append(d[key][k])
    return vals

def subtract_medians(image_data):
    scaled_images = dict()
    for key in image_data.keys():
        ims = image_data[key]
        ims_new = dict()
        for idx in ims.keys():
            im = ims[idx]
            med = np.median(im[10:40:, 10:40:])
            ims_new[idx] = im - med
        scaled_images[key] = ims_new
    return scaled_images

def guide_star_timelapse(image_data, height=170, width=170, title=None, ncols=8):
    '''
    Args:
        image_data: dictionary containing guide-rois image data
    Options:
        height: height of plot (default = 300)
        width: width of plot (default = 300)
        title: title of plot, only needed if you want a different one than is hardcoded(default = None)
    Returns bokeh layout object.'''
    
    scaled_data = subtract_medians(image_data)
    zmin, zmax = np.percentile(get_all_values(scaled_data), (1, 99))
    keys = list(scaled_data.keys())
    indices = range(len(scaled_data[keys[0]]))

    sources = {}

    for idx in indices:
        imgs = [[(255*(scaled_data[key][idx].clip(zmin, zmax) - zmin) / (zmax-zmin)).astype(np.uint8)] for key in keys]
        image_names = [key for key in keys]
#         image_names = []
#         for key in keys:
#             img = scaled_data[key][idx]
#             u8img = (255*(img.clip(zmin, zmax) - zmin) / (zmax-zmin)).astype(np.uint8)
#             colormap = LinearColorMapper(palette=gray(256), low=0, high=255)
#             imgs.append([u8img])
#             image_names.append(key)
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