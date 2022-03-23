#!/usr/bin/env python

"""
Tests with plotting fits images with bokeh
"""

import sys, os
import numpy as np
from bokeh.embed import components
import jinja2
#import fitsio
from astropy.io import fits
from astropy.visualization import ZScaleInterval

import bokeh
import bokeh.plotting as bk
from bokeh.layouts import layout, gridplot
from bokeh.models import HelpTool, Label
from bokeh.models.mappers import LinearColorMapper
from bokeh.palettes import cividis, gray

def downsample_image(image, n):
    '''Downsample input image n x n

    Returns resampled images with shape = image.shape//n
    '''
    ny, nx = image.shape
    ny = (ny//n) * n
    nx = (nx//n) * n
    result = image[0:ny, 0:nx].reshape(ny//n,n,nx//n,n).mean(axis=-1).mean(axis=-2)
    return result

def plot_image(image, mask=None, mask_alpha=0.7, width=800, downsample=2, title=None):
    """
    plots image downsampled, returning bokeh figure of requested width
    """
    #- Downsample image 2x2 (or whatever downsample specifies)
    ny, nx = image.shape
    image2 = downsample_image(image, downsample)

    #- Default image scaling
    zscale = ZScaleInterval()
    zmin, zmax = zscale.get_limits(image2)

    #- Experimental: rescale to uint8 to save space
    u8img = (255*(image2.clip(zmin, zmax) - zmin) / (zmax-zmin)).astype(np.uint8)
    colormap = LinearColorMapper(palette=gray(256), low=0, high=255)

    #- Set up mask if not None. For now, do not distinguish the mask bits
    if mask is not None:
        mask2 = downsample_image(mask, downsample)
        select = mask2 > 0
        mask2[select]  = 1.0
        mask2[~select] = 0.0
        u8mask = mask2.astype(np.uint8)
        yellowmap = LinearColorMapper(palette=['rgba(255, 255, 255, 0.0)',
                                               f'rgba(255, 255,   0, {mask_alpha})'],
                                               low=0.0, high=1.0)

    #- Create figure
    fig = bk.figure(width=width, height=width-50,
                    active_drag='box_zoom',
                    active_scroll='wheel_zoom',
                    tools='pan,box_zoom,wheel_zoom,save,reset')

    #- Redirect help button to DESI wiki
    fig.add_tools(HelpTool(help_tooltip='See the DESI wiki for details\non CCD image QA',
                           redirect='https://desi.lbl.gov/trac/wiki/DESIOperations/NightWatch/NightWatchDescription#CCDImages'))

    fig.image([u8img,], 0, 0, nx, ny, color_mapper=colormap)
    if mask is not None:
        fig.image([u8mask,], 0, 0, nx, ny, color_mapper=yellowmap)

    fig.x_range.start = 0
    fig.x_range.end = nx
    fig.y_range.start = 0
    fig.y_range.end = ny

    if title is not None:
        fig.title.text = title

    return fig

def plot_all_images(input_files, mask_alpha=0.3, width=200, downsample=32, title=None):

    for cam in 'z':
        input_cam_files = list(filter(lambda x: f'preproc-{cam}' in x, sorted(input_files)))
        print(input_cam_files)

    figs, rows = [], []

    for j, input_file in enumerate(input_cam_files):
        print(input_file)

        with fits.open(input_file) as hdul:
            image = hdul[0].data
            mask  = hdul[2].data

        ny, nx = image.shape
        image2 = downsample_image(image, downsample)

        #- Default image scaling
        zscale = ZScaleInterval()
        zmin, zmax = zscale.get_limits(image2)

        #- Experimental: rescale to uint8 to save space
        u8img = (255*(image2.clip(zmin, zmax) - zmin) / (zmax-zmin)).astype(np.uint8)
        colormap = LinearColorMapper(palette=gray(256), low=0, high=255)

        #- Set up mask if not None. For now, do not distinguish the mask bits
        if mask is not None:
            mask2 = downsample_image(mask, downsample)
            select = mask2 > 0
            mask2[select]  = 1.0
            mask2[~select] = 0.0
            u8mask = mask2.astype(np.uint8)
            yellowmap = LinearColorMapper(palette=['rgba(255, 255, 255, 0.0)',
                                                   f'rgba(255, 255,   0, {mask_alpha})'],
                                                   low=0.0, high=1.0)

        #- Create figure
        fig = bk.figure(width=width, height=width, toolbar_location=None)
        fig.xaxis.visible = False
        fig.yaxis.visible = False

        fig.image([u8img,], 0, 0, nx, ny, color_mapper=colormap)
        if mask is not None:
            fig.image([u8mask,], 0, 0, nx, ny, color_mapper=yellowmap)

        label = Label(x=10, y=10, x_units='screen', y_units='screen',
                      text=f'{cam}{j}', text_color='#00ff00', text_font_style='bold')
        fig.add_layout(label)

        fig.x_range.start = 0
        fig.x_range.end = nx
        fig.y_range.start = 0
        fig.y_range.end = ny

        if title is not None:
            fig.title.text = title

        rows.append(fig)

#        if j+1 == 2 or j+1 == 5 or j+1 == 8 or j+1==10:
        if j+1 == 5 or j+1 == 10:
            figs.append(rows)
            rows = []

    return gridplot(figs, toolbar_location='below')

def main(input_in = None, output_in = None, downsample_in = None):
    '''Downsamples image given a downsampling factor, writes to a given file. All args are optional (can be run from the
    command line as well).
    Options:
        input_in: input fits file
        output_in: output html file
        downsample_in: downsample image NxN
    Output:
        html components of a bokeh figure object'''
    # if run from command line
    if [input_in, output_in, downsample_in] == [None, None, None]:
        import argparse
        parser = argparse.ArgumentParser(usage = "{prog} [options]")
        parser.add_argument("-i", "--input", type=str, required=True, help="input image fits file")
        parser.add_argument("-o", "--output", type=str, help="output html file")
        parser.add_argument("-d", "--downsample", type=int, default=4, help="downsample image NxN")

        args = parser.parse_args()

        if args.output is None:
            base, ext = os.path.splitext(args.input)
            assert ext == '.fits'
            args.output = base + "-" + str(args.downsample) + 'x.html'

        input_in = args.input
        basename = os.path.basename(args.input)
        n = args.downsample
        output = args.output

    # if run from a different file and has provided arguments
    else:
        if np.isscalar(input_in):
            if input_in == None or downsample_in == None:
                return "input_in and/or downsample_in not provided"
            img_input = input_in
            basename = os.path.basename(input_in)
            n = downsample_in
            output = output_in

    #- Single input image for individual preproc plots.
    if np.isscalar(input_in):
        with fits.open(img_input) as hdul:
            image = hdul[0].data
            mask  = hdul[2].data

        short_title = '{basename} {n}x{n}'.format(basename=os.path.splitext(basename)[0], n=n)
        long_title = '{basename} downsampled {n}x{n}'.format(basename=basename, n=n)

        fig = plot_image(image, mask, downsample=n, title=long_title)

        if (output != None):
            bk.output_file(output, title=short_title, mode='inline')
            fig = plot_image(image, mask, downsample=n, title=long_title)
            bk.save(fig)
            print('Wrote {}'.format(output))
    #- List of input files for preproc summary plots.
    else:
        fig = plot_all_images(input_in)

    return components(fig)

if __name__ == '__main__':
    main()
