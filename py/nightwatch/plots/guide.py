import numpy as np
import json

import bokeh
import bokeh.plotting as bk
from bokeh.models import ColumnDataSource, OpenURL, HoverTool, CustomJS, Slider, Image, Legend
from bokeh.layouts import column, gridplot
from bokeh.colors import RGB

import astropy
from astropy.table import Table
from astropy.io import fits as fits

def get_guide_data(night, expid):
    '''Given a night and exposure, dumps centroid-*.json file into a dictionary. Note: no padding zeros for expid argument.'''
      
    infile = "/global/cfs/cdirs/desi/spectro/data/{night}/{expid:08d}/centroids-{expid:08d}.json".format(night=night, expid=expid)

    with open(infile) as fx:
        guidedata = json.load(fx)
    
    return guidedata

def get_all_guide_scatter(data, cam, width=700, height=300, title=None):
    '''Returns plot of x and y errors for all guide stars on one guide camera for all frames taken during an exposure.
    Args:
        data: dictionary of centroid-*.json data, must have entries x_error and y_error.
        cam: camera to make plot for (int)
    Options:
        width: width of plot. Default = 700.
        height: height of plot. Default = 300.
        title: title for plot. Default is GUIDE {cam}.
    Returns bokeh figure object.'''
    
    if title==None:
        title = 'GUIDE {cam}'.format(cam=cam)
    
    fig = bk.figure(plot_width=width, plot_height=height, title=title)
    
    reddict = {0: RGB(150, 40, 27), 2: RGB(240, 52, 52), 1: RGB(219, 10, 91), 3: RGB(255, 148, 120)}
    bluedict = {0: RGB(77, 5, 232), 1: RGB(44, 130, 201), 2: RGB(0, 181, 204), 3: RGB(107, 185, 240)}
    
    for star in [0, 1, 2, 3]:
        
        key = 'GUIDE{cam}_{star}'.format(cam=cam, star=star) 
        
        try:
            x_error = [tmp[key]['x_error'] for tmp in data['frames'].values()]
            y_error = [tmp[key]['y_error'] for tmp in data['frames'].values()]
            
            framenumber = range(len(x_error))
    
            source = ColumnDataSource(data = dict(
                star = [star]*len(x_error),
                x_error = x_error,
                y_error = y_error,
                framenumber = framenumber
            ))
                  
            y_line = fig.line('framenumber', 'y_error', line_width=2, source=source, color=reddict[star], alpha=0.7)
            #y_circ = fig.circle('framenumber', 'y_error', size=1, source=source, color=reddict[star])
            x_line = fig.line('framenumber', 'x_error', line_width=2, source=source, color=bluedict[star], alpha=0.7)
            #x_circ = fig.circle('framenumber', 'x_error', size=1, source=source, color=bluedict[star])
            
            yhover = HoverTool(renderers = [y_line], tooltips=[("star", "@star"), ("frame", "@framenumber"), ("y error", "@y_error")])
            xhover = HoverTool(renderers = [x_line], tooltips=[("star", "@star"), ("frame", "@framenumber"), ("x error", "@x_error")])
            
            fig.add_tools(yhover)
            fig.add_tools(xhover)
            
        except KeyError:
            print('no data for GUIDE{cam}_{star}'.format(cam=cam, star=star))
            x_error = [0]
            y_error = [0]
            framenumber= [0]
            
            source = ColumnDataSource(data = dict(
                x_error = x_error,
                y_error = y_error,
                framenumber = framenumber
            ))
            
            y_line = fig.line('framenumber', 'y_error', line_width=2, source=source, color=reddict[star], alpha=0.7)
            #y_circ = fig.circle('framenumber', 'y_error', size=1, source=source, color=reddict[star])
            x_line = fig.line('framenumber', 'x_error', line_width=2, source=source, color=bluedict[star], alpha=0.7)
            #x_circ = fig.circle('framenumber', 'x_error', size=1, source=source, color=bluedict[star])
    
    fig.yaxis.axis_label = 'Error'
    fig.xaxis.axis_label = 'Frame Number'
    
    return fig

def get_all_stars_hist(data, cam, width=300, height=300, title=None):
    '''Returns histograms of x and y errors for guide star positions for a single camera. 
   Args:
        data: dictionary of centroid-*.json data, must have entries x_error and y_error.
        cam: camera to make plot for (int)
    Options:
        width: width of plot. Default = 700.
        height: height of plot. Default = 300.
        title: title for plot. Default is GUIDE {cam}.
    Returns bokeh figure object.'''
    
    xfig = bk.figure(plot_width=width, plot_height=height, title=title)
    yfig = bk.figure(plot_width=width, plot_height=height, title=title)
    
    reddict = {0: RGB(150, 40, 27), 2: RGB(240, 52, 52), 1: RGB(219, 10, 91), 3: RGB(255, 148, 120)}
    bluedict = {0: RGB(77, 5, 232), 1: RGB(44, 130, 201), 2: RGB(0, 181, 204), 3: RGB(107, 185, 240)}
    
    for star in [0, 1, 2, 3]:
        key = 'GUIDE{cam}_{star}'.format(cam=cam, star=star) 
        
        try:
            x_error = [tmp[key]['x_error'] for tmp in data['frames'].values()]
            y_error = [tmp[key]['y_error'] for tmp in data['frames'].values()]
            
        except KeyError:
            print('no data for GUIDE{cam}_{star}'.format(cam=cam, star=star))
            continue
        
        framenumber = np.arange(len(x_error))
    
        xhist, xedges = np.histogram(x_error, density=True, bins=30)
        yhist, yedges = np.histogram(y_error, density=True, bins=30)
    
        xfig.quad(top=xhist, bottom=0, left=xedges[:-1], right=xedges[1:], color=bluedict[star], fill_alpha=0.25)
        yfig.quad(top=yhist, bottom=0, left=yedges[:-1], right=yedges[1:], fill_alpha=0.25, color=reddict[star])
        
    xfig.toolbar_location = None
    xfig.yaxis.visible = False 
    yfig.toolbar_location = None
    yfig.yaxis.visible = False  
    xfig.xgrid.grid_line_color = None
    xfig.ygrid.grid_line_color = None
    yfig.xgrid.grid_line_color = None
    yfig.ygrid.grid_line_color = None
    xfig.x_range = yfig.x_range
        
    return xfig, yfig

def guide_scatter_combined(night, expid, cams, width=600, height=300, ncols=2):
    '''Returns a multi-plot with both line plots and histograms, across all guide cameras and all guide stars.
    Args:
        night:
        expid:
        cams:
    Options:
        width:
        height:
        ncols: 
    Returns bokeh Layout object.'''
    
    data = get_guide_data(night, expid)
    
    figs = []
    xhists = []
    yhists = []
    for idx in range(len(cams)):
        xhist, yhist = get_all_stars_hist(data, cams[idx], height = int(height*0.5), width = int(width*0.25))
        xhists.append(xhist)
        yhists.append(yhist)
        if idx%ncols == 0:
            fig = get_all_guide_scatter(data, cams[idx], width=width, height=height)
            figs.append(fig)
        else:
            fig = get_all_guide_scatter(data, cams[idx], width=width, height=height)
            fig.yaxis.axis_label = None
            figs.append(fig)
    
    figs[0].x_range = figs[1].x_range = figs[2].x_range = figs[3].x_range = figs[4].x_range = figs[5].x_range
    figs[0].y_range = figs[1].y_range = figs[2].y_range = figs[3].y_range = figs[4].y_range = figs[5].y_range
    
    xhists[0].x_range = xhists[1].x_range = xhists[2].x_range = xhists[3].x_range = xhists[4].x_range = xhists[5].x_range
    yhists[0].x_range = yhists[1].x_range = yhists[2].x_range = yhists[3].x_range = yhists[4].x_range = yhists[5].x_range
    
    #for fig in figs[1:len(figs)]:
        #fig.legend.visible = False
    for fig in figs[0:-ncols]:
        fig.xaxis.axis_label = None
    for fig in figs[-ncols:len(figs)]:
        fig.plot_height += 20
        
    figs_combined = []
    for idx in range(len(cams)):
        figs_combined.append(figs[idx])
        figs_combined.append(column(xhists[idx], yhists[idx]))
    
    grid = gridplot(figs_combined, ncols=2*ncols)
    return grid

def guide_star_timelapse(night, expid, cam, star, height=400, width=400, title=None):
    '''
    Args:
        night: YYYYMMDD
        expid: no padding zeros (int)
        cam: specify camera (int)
        star: specify star (int)
    Options:
        height:
        width:
        title:
    Returns bokeh layout object.'''

    filename = '/global/cfs/cdirs/desi/spectro/data/{night}/{expid:08d}/guide-rois-{expid:08d}.fits.fz'.format(night=night, expid=expid)
    name = 'GUIDE{cam}_{star}'.format(cam=cam, star=star)
    
    try:
        image_data = fits.getdata(filename, extname=name)
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

    #im.x_range.range_padding = im.y_range.range_padding = 0
    im.xaxis.axis_label = 'arc seconds'
    im.yaxis.axis_label = 'arc seconds'

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
