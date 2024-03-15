#!/usr/bin/env python

"""
Tests with plotting fits images with bokeh
"""
import numpy as np
from astropy.visualization import ZScaleInterval

import bokeh
import bokeh.plotting as bk
from bokeh.models import HelpTool
from bokeh.models.mappers import LinearColorMapper
from bokeh.palettes import cividis, gray

from .plotimage import downsample_image

from packaging import version
_is_bokeh23 = version.parse(bokeh.__version__) >= version.parse('2.3.0')


def plot_fvc_image(image, imghdr=None, width=800, downsample=4, title=None):
    """Plot downsampled FVC image, returning bokeh figure of requested width.
    
    Parameters
    ----------
    image: ndarray
        Image data from FVC FITS HDU.
    imghdr: astropy.header or None
        Header data from the image HDU.
    width: int
        Width of the final image in pixels.
    downsample: int
        Downsampling factor.
    title: str or None
        Figure title.

    Returns
    -------
    fig: bokeh.Figure
        Figure containing the image.
    """
    img = downsample_image(image, downsample)
    nx, ny = img.shape

    # Image scaling. Note that the FVC seems to have a different dynamic
    # ranges in the left and right halves of the image.
    z = ZScaleInterval()

    # Output image: downsampled and scaled to 8-bit dynamic range (0-255).
    u8img = np.zeros_like(img, dtype=np.uint8)

    for (i1, i2) in zip([0, nx//2], [nx//2, nx]):
        for (j1, j2) in zip([0, ny//2], [ny//2, ny]):
            # Normalize and reescale image by CCD quadrants.
            zmin, zmax = z.get_limits(img[i1:i2, j1:j2])
            u8img[i1:i2, j1:j2] = (255*(img[i1:i2, j1:j2].clip(zmin, zmax) - zmin) / (zmax-zmin)).astype(np.uint8)

    colormap = LinearColorMapper(palette=cividis(256), low=0, high=255)

    # Create figure
    fig = bk.figure(width=width, height=width-50,
                    active_drag='box_zoom',
                    active_scroll='wheel_zoom',
                    tools='pan,box_zoom,wheel_zoom,save,reset')

    # Redirect help button to DESI wiki
    if _is_bokeh23:
        fig.add_tools(HelpTool(description='See the DESI wiki for details\non FVC images',
                               redirect='https://desi.lbl.gov/trac/wiki/DESIOperations/NightWatch/NightWatchDescription#FVCImages'))
    else:
        fig.add_tools(HelpTool(help_tooltip='See the DESI wiki for details\non FVC images',
                               redirect='https://desi.lbl.gov/trac/wiki/DESIOperations/NightWatch/NightWatchDescription#FVCImages'))

    fig.image([u8img,], 0, 0, nx, ny, color_mapper=colormap)

    fig.x_range.start = 0
    fig.x_range.end = nx
    fig.y_range.start = 0
    fig.y_range.end = ny

    if title is not None:
        fig.title.text = title

    return fig

