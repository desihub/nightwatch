#!/usr/bin/env python

"""
Tests with plotting fits images with bokeh
"""

import sys, os
import numpy as np
from bokeh.embed import components
import jinja2
import fitsio
from astropy.io import fits
# from astropy.visualization import ZScaleInterval

import bokeh
# import bokeh.plotting as bk
# from bokeh.models.mappers import LinearColorMapper
# from bokeh.palettes import cividis, gray

from glob import glob

from plotimage import plot_image

def plot_fvc(expos, hdu="F0000", downsample=2):
    '''Plots FVC image
    ARGS:
        expos : string representing NightWatch exposure directory "day/exposure"

    Options:
        hdu: HDU of FVC image, default to "F0000"
        downsample: downsample image NxN
    '''
    night, expid = expos.split("/")
    spectrodata = "/global/cfs/cdirs/desi/spectro/data/" # HARDCODED
    try: fvcfile = glob(spectrodata+night+'/'+expid+'/'+"fvc-*.fits.fz")[0]
    except:
        print("No FVC file found in ", expid)
        return

    print("\nReading FVC images from file: ", fvcfile)


    fvc = fitsio.FITS(fvcfile)

    dat = readchip(fvc, hdu)

    fvcimage = dat[1]
    print("The medians in each quadrant has been subtracted, then a sqrt stretch applied.")
    print("No corrections for dark current, flat fielding, or anything else.\n\n")

    n = downsample
    plottitle = "FVC (HDU={hdu}, Square Root Stretch) {expos} downsampled {n}x{n}".format(hdu=hdu, expos=expos, n=n)
    fig = plot_image(fvcimage, downsample=n, title=plottitle)

    return fig

def sqrt_stretch(x):
    return x/np.sqrt(np.abs(x+1e-10))

def readchip(fitsfile, hdu):
    im = fitsfile[hdu].read()
    print("Found images of size", np.shape(im), "in HDU", hdu)
    if (len(np.shape(im))==3):
        stack = np.mean(im, axis=0)
        print("Averaging into a stack of this form: ",np.shape(stack))
    else:
        stack = im
        print("One frame.  Not averaging")
    halfX = np.int(np.shape(stack)[0]/2)
    halfY = np.int(np.shape(stack)[1]/2)
    stack_eq = stack.astype('float32')

    median = np.zeros([2,2])
    median[0][0] = np.median(stack_eq[:halfX, :halfY])
    median[0][1] = np.median(stack_eq[:halfX, halfY:])
    median[1][0] = np.median(stack_eq[halfX:, :halfY])
    median[1][1] = np.median(stack_eq[halfX:, halfY:])

    stack_eq[:halfX,:halfY] = stack_eq[:halfX,:halfY]-median[0][0]
    stack_eq[:halfX,halfY:] = stack_eq[:halfX,halfY:]-median[0][1]
    stack_eq[halfX:,:halfY] = stack_eq[halfX:,:halfY]-median[1][0]
    stack_eq[halfX:,halfY:] = stack_eq[halfX:,halfY:]-median[1][1]

    print("Quadrant Medians:", np.ndarray.flatten(median))

    return stack, sqrt_stretch(stack_eq)

