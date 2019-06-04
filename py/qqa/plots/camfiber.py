"""
Placeholder: per-camera per-fiber plots
"""
import numpy as np

import jinja2

import bokeh
import bokeh.plotting as bk
from bokeh.embed import components

from ..plots.fiber import plot_fibers


def plot_per_camfiber(data, attribute, cameras, components_dictionary, percentiles={}, extremes={}):
	figs_list, hfigs_list = [], []
	for c in cameras:
		fig, hfig = plot_fibers(data, attribute, cam=c, percentile=percentiles.get(c, None), 
			zmin=extremes.get(c[0], None), zmax=extremes.get(c[1], None))
		figs_list.append(fig)
		hfigs_list.append(hfig)
	figs = bk.gridplot([figs_list, hfigs_list], toolbar_location='right')
	script, div = components(figs)

	components_dictionary[attribute] = dict(script=script, div=div)
