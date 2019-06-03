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

def plot_image(image, width=700, downsample=2, title=None):
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

    #- Create figure
    fig = bk.figure(width=width, height=width-50,
        active_drag='box_zoom', active_scroll='wheel_zoom')
    fig.image([u8img,], 0, 0, nx, ny, color_mapper=colormap)
    fig.x_range.start = 0
    fig.x_range.end = nx
    fig.y_range.start = 0
    fig.y_range.end = ny

    if title is not None:
        fig.title.text = title

    return fig

def main(input_in = None, output_in = None, downsample_in = None):

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

        image = args.input
        basename = os.path.basename(args.input)
        n = args.downsample
        output = args.output

    # if run from a different file and has provided arguments
    else:
        if input_in == None or downsample_in == None:
            return "input_in and/or downsample_in not provided"
        if output_in is None:
            base, ext = os.path.splitext(input_in)
            assert ext == '.fits'
            output_in = base + "-" + str(n_in) + 'x.html'
        image = input_in
        basename = os.path.basename(input_in)
        n = downsample_in
        output = output_in

    image = fits.getdata(image)

    short_title = '{basename} {n}x{n}'.format(basename=os.path.splitext(basename)[0], n=n)
    long_title = '{basename} downsampled {n}x{n}'.format(basename=basename, n=n)

    fig = plot_image(image, downsample=n, title=long_title)
    plot_script, plot_div = components(fig)
    html = """
    <html>
    <link
        href="https://cdn.pydata.org/bokeh/release/bokeh-{version}.min.css"
        rel="stylesheet" type="text/css"
    >
    <link
        href="https://cdn.pydata.org/bokeh/release/bokeh-tables-{version}.min.css"
        rel="stylesheet" type="text/css"
    >
    <script
        src="https://cdn.pydata.org/bokeh/release/bokeh-{version}.min.js"
    ></script>

    <script src="https://cdn.pydata.org/bokeh/release/bokeh-tables-{version}.min.js"
    ></script>
    <body>
    <div>{plot_script} {plot_div}</div>
    <div>Downsample: <input size="4" type="number" id = "down" value={downsample}></div>
    <button onclick='
        var url = "{basename}-" + document.getElementById("down").value + "x.html"
        window.open(url, "_top")
    '>Generate</button>
    </body>
    <script>
        var input = document.getElementById("down");
            input.addEventListener("keyup", function(event) {{
                if (event.keyCode === 13) {{
                    event.preventDefault();
            var url = "{cam}-" + document.getElementById("down").value + "x.html"
            window.open(url, "_top")
            }}
        }});
    </script>
    </html>
    """.format(plot_script = plot_script, plot_div = plot_div, version=bokeh.__version__, basename=os.path.splitext(basename)[0], downsample=n)

    with open(output, 'w') as fx:
        fx.write(html)
    #bk.output_file(output, title=short_title, mode='inline')

    #fig = plot_image(image, downsample=n, title=long_title)
    #bk.save(fig)
    print('Wrote {}'.format(output))

if __name__ == '__main__':
    main()
