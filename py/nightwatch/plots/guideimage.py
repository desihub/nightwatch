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

def guide_star_timelapse(infile, cam, star, height=400, width=400, title=None):
    '''
    Args:
        infile: file containing guide-rois image data
        cam: specify camera (int)
        star: specify star (int)
    Options:
        height:
        width:
        title:
    Returns bokeh layout object.'''
    
    name = 'GUIDE{cam}_{star}'.format(cam=cam, star=star)
    
    try:
        image_data = fits.getdata(infile, extname=name)
    except KeyError:
        print('no images for {name}'.format(name=name))
        return
    
    indices = range(len(image_data))

    if title==None:
        title = 'GFA {cam} Star {star}'.format(cam=cam, star=star)

    sources = {}
    
    for idx in indices:
        img = [image_data[idx]]
        sources['_' + str(idx)] = ColumnDataSource(data = dict(
            image = img
        ))

    dict_of_sources = dict(zip(
        [idx for idx in indices],
        ['_%s' % idx for idx in indices]
    ))

    js_source_array = str(dict_of_sources).replace("'", "")

    im = bk.figure(plot_width=width, plot_height=height, x_range = (0, 50), y_range=(0, 50), title=title)

    renderer_source = sources['_%s' % indices[0]]
    im_glyph = Image(image='image', x=0, y=0, dw=50, dh=50)
    im_renderer = im.add_glyph(renderer_source, im_glyph)

    tooltips = [
            ('(x, y)', '($x, $y)'),
        ]
    im.add_tools(HoverTool(
        tooltips=tooltips,
        renderers = [im_renderer]
    ))

    code = """
        var idx = cb_obj.value,
            sources = %s,
            new_source_data = sources[idx].data;
        renderer_source.data = new_source_data;
    """ % js_source_array

    callback = CustomJS(args=sources, code=code)

    slider = Slider(start=0, end=indices[-1], value=0, step=1, title="Frame", callback=callback, width=int(width*0.9))
    #slider.js_on_change('value', callback)

    callback.args['renderer_source'] = renderer_source
    callback.args['slider'] = slider

    layout = column(slider, im)
    
    return layout

def all_stars_timelapse(infile, cam, height=300, width=300, title=None):
    
    figs = []
    for star in range(4):
        try:
            fig = guide_star_timelapse(infile, cam, star, height=height, width=width)
            figs.append(fig)
        except:
            continue
    grid = gridplot(figs, ncols=len(figs))
    return grid