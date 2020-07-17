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

from scipy.ndimage import rotate

from ..io import rot_dict

def get_all_values(d):
    vals = []
    for key in d.keys():
        for k in d[key].keys():
            vals.append(d[key][k])
    return vals

def subtract_medians(image_data, return_medians=False):
    scaled_images = dict()
    medians = dict()
    keys = image_data.keys()
    for key in keys:
        ims = image_data[key]
        ims_new = dict()
        meds = dict()
        for idx in ims.keys():
            im = ims[idx]
            med = np.median(im[10:40:, 10:40:])
            ims_new[idx] = im - med
            meds[idx] = med
        scaled_images[key] = ims_new
        medians[key] = meds
    
    if return_medians:
        return scaled_images, medians
    
    else:
        return scaled_images

def rotate_guide_images(image_data, rotdict):
    '''rotate images to align along same axis given dictionary of angles.'''
    images_rotated = dict()
    for key in image_data.keys():
        cam = key[5]
        angle = rotdict[cam]
        data = image_data[key]
        ims = dict()
        for idx in data.keys():
            zmin = np.percentile(data[idx], 5)
            im = rotate(data[idx], angle, reshape=False, mode='constant', cval=zmin)
            ims[idx] = im
        images_rotated[key] = ims
    return images_rotated
        

def guide_star_timelapse(image_data, height=170, width=170, title=None, ncols=8):
    '''
    Args:
        image_data: dictionary containing guide-rois image data
    Options:
        height: height of plot (default = 300)
        width: width of plot (default = 300)
        title: title of plot, only needed if you want a different one than is hardcoded(default = None)
    Returns bokeh layout object.'''
    
    scaled_data = subtract_medians(image_data, return_medians=False)
    
    #get dictionary of angles to rotate different GFAs to align images along same axis
    gfa_file = os.path.expandvars('$DESIMODEL/data/focalplane/gfa.ecsv')
    rotdict = rot_dict(gfa_file)
    
    #rotate images
    scaled_data = rotate_guide_images(scaled_data, rotdict)
    
    #data to rescale colors later for readability
    zmin, zmax = np.percentile(get_all_values(scaled_data), (1, 99))
    keys = list(scaled_data.keys())
    indices = range(len(scaled_data[keys[0]]))

    sources = {}

    for idx in indices:
        imgs = []
        image_names = []
        for key in keys:
            img = scaled_data[key][idx]
            u8img = (255*(img.clip(zmin, zmax) - zmin) / (zmax-zmin)).astype(np.uint8)
            colormap = LinearColorMapper(palette=gray(256), low=0, high=255)
            imgs.append([u8img])
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
