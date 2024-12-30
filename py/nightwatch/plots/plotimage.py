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
from bokeh.models import HelpTool, Label, ColumnDataSource, Range1d
from bokeh.models.widgets import Panel, Tabs
from bokeh.models.mappers import LinearColorMapper
from bokeh.palettes import cividis, gray

from packaging import version
_is_bokeh23 = version.parse(bokeh.__version__) >= version.parse('2.3.0')


def downsample_image(image, n):
    """Downsample input image to n x n.

    Parameters
    ----------
    image : ndarray
        Input image of size nx x ny.
    n : int
        Downsampling factor to produce image of size nx//n x ny//n.

    Returns
    -------
    image2 : ndarray
        Resampled image of shape image.shape//n.
    """
    ny, nx = image.shape
    ny = (ny//n) * n
    nx = (nx//n) * n
    result = image[0:ny, 0:nx].reshape(ny//n,n,nx//n,n).mean(axis=-1).mean(axis=-2)
    return result


def plot_image(image, mask=None, imghdr=None, mask_alpha=0.7, width=800, downsample=2, title=None):
    """Plot a spectrograph CCD image.

    Parameters
    ----------
    image : ndarray
        Input image from CCD, e.g., from FITS output of preproc.
    mask : ndarray or None
        Image pixel mask bits after preprocessing.
    imghdr : astropy.header or None
        Header of the image HDU.
    mask_alpha : float
        Alpha level to use in plotting the pixel mask.
    width : int
        Width of the image, in pixels.
    downsample : int
        Downsampling factor for the input.
    title : str or None
        Output figure title.

    Returns
    -------
    fig : bokeh.Figure
        Figure containing image.
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

        # Masked pixels are set to 2, unmasked pixels to 0.
        select = mask2 > 0
        mask2[select]  = 2.0
        mask2[~select] = 0.0

        # DARK exposures with bright unmasked pixels are set to 1.
        if imghdr is not None:
            if 'OBSTYPE' in imghdr:
                if imghdr['OBSTYPE'] == 'DARK':
                    mask2[(mask2==0) & (image2 > 100)] = 1.0

        u8mask = mask2.astype(np.uint8)

        # Masked pixels are set to yellow. Unmasked but very bright pixels are
        # set to red.
        maskmap = LinearColorMapper(palette=['rgba(255, 255, 255, 0.0)',
                                            f'rgba(255,  0,  0, {mask_alpha})',
                                            f'rgba(255, 255, 0, {mask_alpha})'],
                                             low=0, high=2)

    #- Create figure
    fig = bk.figure(width=width, height=width-50,
                    active_drag='box_zoom',
                    active_scroll='wheel_zoom',
                    tools='pan,box_zoom,wheel_zoom,save,reset')

    #- Redirect help button to DESI wiki
    if _is_bokeh23:
        fig.add_tools(HelpTool(description='See the DESI wiki for details\non CCD image QA',
                               redirect='https://desi.lbl.gov/trac/wiki/DESIOperations/NightWatch/NightWatchDescription#CCDImages'))
    else:
        fig.add_tools(HelpTool(help_tooltip='See the DESI wiki for details\non CCD image QA',
                               redirect='https://desi.lbl.gov/trac/wiki/DESIOperations/NightWatch/NightWatchDescription#CCDImages'))

    fig.image([u8img,], 0, 0, nx, ny, color_mapper=colormap)
    if mask is not None:
        fig.image([u8mask,], 0, 0, nx, ny, color_mapper=maskmap)

    fig.x_range.start = 0
    fig.x_range.end = nx
    fig.y_range.start = 0
    fig.y_range.end = ny

    if title is not None:
        fig.title.text = title

    #- Plot a histogram of CCD pixel values (not downsampled).
    #  First determine histogram binning.
    cmin, cmax = 1e99, -1e99
    for (i1,i2) in zip([0, nx//2], [nx//2, nx]):
        for (j1,j2) in zip([0, ny//2], [ny//2, ny]):
            data = image[i1:i2, j1:j2].flatten()
            p1, p2 = np.percentile(data, [0.01, 99.99])
            cmin = np.minimum(cmin, np.floor(p1))
            cmax = np.maximum(cmax, np.ceil(p2))
    cmin = cmin if cmin < -30. else -30.
    cmax = cmax if cmax >  30. else  30.
    nbin = 201

    px = np.linspace(start=cmin, stop=cmax, num=nbin)
    pxc = 0.5*(px[1:] + px[:-1])

    fig_h = bk.figure(title='CCD values', y_axis_type='log')
    amps, colors, k = 'ABCD', ['mediumblue', 'darkorange', 'limegreen', 'crimson'], 0

    #- Loop over amps and plot the data.
    for (i1,i2) in zip([0, nx//2], [nx//2, nx]):
        for (j1,j2) in zip([0, ny//2], [ny//2, ny]):
            data = image[i1:i2, j1:j2].flatten()
            hist, _ = np.histogram(data, bins=px)

            source = ColumnDataSource(data=dict(
                        pixels = pxc,
                        data = hist,
                        amp = [amps[k]]*len(hist),
                    ))
            s = fig_h.step('pixels', 'data', source=source, color=colors[k],
                           legend_label=f'amp {amps[k]}', alpha=0.7, line_width=2, mode='center')
            k += 1

    fig_h.legend.location = 'top_right'
    fig_h.xaxis.axis_label = 'CCD charge'
    fig_h.yaxis.axis_label = 'Count'
    fig_h.x_range = Range1d(cmin, cmax)

    histtabs = [Panel(child=fig, title='CCD'), Panel(child=fig_h, title='Histogram')]
    return Tabs(tabs=histtabs)


def plot_all_images(input_files, mask_alpha=0.3, width=200, downsample=32, title=None):
    """Generate summary images given a set of preproc FITS files.

    Parameters
    ----------
    input_files : list or ndarray
        List of paths to preproc input FITS files.
    mask_alpha : float
        Alpha level to use for masked pixels.
    width : int
        Output image width, in pixels.
    downsample : int
        Image downsampling factor.
    title : str or None
        Output figure title.

    Returns
    -------
    tabs : bokeh.model.widgets.Tabs
        Set of tabs with CCD image gridplots for the b, r, and z cameras.
    """

    #- Loop over cameras (b, r, z).
    camtabs = []
    for cam in 'brz':
        input_cam_files = list(filter(lambda x: f'preproc-{cam}' in x, sorted(input_files)))

        #- Loop over spectrographs (0-9).
        figs, rows = [], []
        for j in range(10):

            input_file = list(filter(lambda x: f'{cam}{j}' in x, input_cam_files))

            #- Check that the input file exists for this camera + spectrograph.
            if input_file:
                with fits.open(input_file[0]) as hdul:
                    image  = hdul[0].data
                    imghdr = hdul[0].header
                    mask   = hdul[2].data

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
                    mask2[select]  = 2.0    # Masked pixels = 2.
                    mask2[~select] = 0.0    # Unmasked pixels = 0.

                    # DARK exposures with bright unmasked pixels are set to 1.
                    if 'OBSTYPE' in imghdr:
                        if imghdr['OBSTYPE'] == 'DARK':
                            mask2[(mask2==0) & (image2 > 100)] = 1.0

                    u8mask = mask2.astype(np.uint8)

                    # Masked pixels are set to yellow. Unmasked but very bright
                    # pixels are set to red in DARK exposures.
                    maskmap = LinearColorMapper(palette=['rgba(255, 255, 255, 0.0)',
                                                        f'rgba(255,  0,  0, {mask_alpha})',
                                                        f'rgba(255, 255, 0, {mask_alpha})'],
                                                         low=0, high=2)

                #- Create figure of CCD
#                fig = bk.figure(width=width, height=width, toolbar_location=None)
                fig = bk.figure(width=width, height=width, tools='pan,box_zoom,wheel_zoom,reset')

                #- Redirect help button to DESI wiki
                if _is_bokeh23:
                    fig.add_tools(HelpTool(description='See the DESI wiki for details\non CCD image QA',
                                           redirect='https://desi.lbl.gov/trac/wiki/DESIOperations/NightWatch/NightWatchDescription#CCDImages'))
                else:
                    fig.add_tools(HelpTool(help_tooltip='See the DESI wiki for details\non CCD image QA',
                                           redirect='https://desi.lbl.gov/trac/wiki/DESIOperations/NightWatch/NightWatchDescription#CCDImages'))

                #- Remove axis labels
                fig.xaxis.visible = False
                fig.yaxis.visible = False

                fig.image([u8img,], 0, 0, nx, ny, color_mapper=colormap)
                if mask is not None:
                    fig.image([u8mask,], 0, 0, nx, ny, color_mapper=maskmap)

                # Label spectrograph ID
                label = Label(x=10, y=160, x_units='screen', y_units='screen',
                              text=f'SM{imghdr["SPECID"]}', text_color='#00ffff', text_font_style='bold')
                fig.add_layout(label)

                # Label camera
                label = Label(x=10, y=10, x_units='screen', y_units='screen',
                              text=f'{cam}{j}', text_color='#00ff00', text_font_style='bold')
                fig.add_layout(label)

                fig.x_range.start = 0
                fig.x_range.end = nx
                fig.y_range.start = 0
                fig.y_range.end = ny

                if title is not None:
                    fig.title.text = title

            #- No input found for this camera and spectrograph.
            else:
                fig = None

            rows.append(fig)

            #- Plot a row of 5 spectrographs: 0-4 and 5-9.
            if j+1 == 5 or j+1 == 10:
                figs.append(rows)
                rows = []

        #- Add a tab for this camera.
        gp = gridplot(figs, toolbar_location='below', merge_tools=True)
        tab = Panel(child=gp, title=f'{cam} Cameras')
        camtabs.append(tab)

    return Tabs(tabs=camtabs)


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
            imhdr = hdul[0].header
            mask  = hdul[2].data

        short_title = '{basename} {n}x{n}'.format(basename=os.path.splitext(basename)[0], n=n)
        long_title = '{basename} downsampled {n}x{n}'.format(basename=basename, n=n)

        fig = plot_image(image, mask, imhdr, downsample=n, title=long_title)

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
