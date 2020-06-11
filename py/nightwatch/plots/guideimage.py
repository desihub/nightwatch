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

def guide_star_timelapse(infile, cam, height=300, width=300, title=None):
    '''
    Args:
        infile: file containing guide-rois image data
        cam: specify camera (int)
    Options:
        height: height of plot (default = 300)
        width: width of plot (default = 300)
        title: title of plot, only needed if you want a different one than is hardcoded(default = None)
    Returns bokeh layout object.'''
    
    name0 = 'GUIDE{cam}_{star}'.format(cam=cam, star=0)
    name1 = 'GUIDE{cam}_{star}'.format(cam=cam, star=1)
    name2 = 'GUIDE{cam}_{star}'.format(cam=cam, star=2)
    name3 = 'GUIDE{cam}_{star}'.format(cam=cam, star=3)
    #name = 'GUIDE{cam}'.format(cam=cam)

    image_data = dict()

    try:
        image_data['0'] = fits.getdata(infile, extname=name0)
    except KeyError:
        print('no images for {name}'.format(name=name0))
    try:
        image_data['1'] = fits.getdata(infile, extname=name1)
    except KeyError:
        print('no images for {name}'.format(name=name1))
    try:
        image_data['2'] = fits.getdata(infile, extname=name2)
    except KeyError:
        print('no images for {name}'.format(name=name2))
    try:
        image_data['3'] = fits.getdata(infile, extname=name3)
    except KeyError:
        print('no images for {name}'.format(name=name3))

    keys = list(image_data.keys())
    indices = range(len(image_data[keys[0]]))

    sources = {}

    for idx in indices:
        imgs = []
        image_names = []
        for key in keys:
            img = [image_data[key][idx]]
            imgs.append(img)
            image_names.append('image{}'.format(key))
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
        name_key = 'image{}'.format(key)
        title = 'Cam {} Star {}'.format(cam, key)
        im = bk.figure(plot_width=width, plot_height=height, x_range = (0, 50), y_range=(0, 50), title=title)
        im.xaxis.axis_label = 'pixels'
        im.yaxis.axis_label = 'pixels'
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
    slider = Slider(start=0, end=indices[-1], value=0, step=1, title="Frame", callback=callback, width=int(width*0.9))
    callback.args['renderer_source'] = renderer_source
    callback.args['slider'] = slider

    slider_row = [slider] + [None]*(len(ims)-1)
    layout = gridplot([slider_row, ims])
    return layout