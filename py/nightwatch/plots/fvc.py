#!/usr/bin/env python

"""
Tests with plotting fits images with bokeh
"""
import numpy as np
from astropy.visualization import ZScaleInterval

import bokeh
import bokeh.plotting as bk
from bokeh.models.mappers import LinearColorMapper
from bokeh.palettes import cividis, gray

from .plotimage import downsample_image


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

    # Separately normalize the left and right halves into 8-bit range, then rejoin.
    zmin, zmax = z.get_limits(img[:,:ny//2])
    u8img_left = (255*(img[:,:ny//2].clip(zmin, zmax) - zmin) / (zmax-zmin)).astype(np.uint8)

    zmin, zmax = z.get_limits(img[:,ny//2:])
    u8img_right = (255*(img[:,ny//2:].clip(zmin, zmax) - zmin) / (zmax-zmin)).astype(np.uint8)

    u8img = np.concatenate((u8img_left, u8img_right), axis=1)
    colormap = LinearColorMapper(palette=gray(256), low=0, high=255)

    # Create figure
    fig = bk.figure(width=width, height=width-50,
                    active_drag='box_zoom',
                    active_scroll='wheel_zoom',
                    tools='pan,box_zoom,wheel_zoom,save,reset')

    fig.image([u8img,], 0, 0, nx, ny, color_mapper=colormap)

    fig.x_range.start = 0
    fig.x_range.end = nx
    fig.y_range.start = 0
    fig.y_range.end = ny

    if title is not None:
        fig.title.text = title

    return fig

