"""
Pages summarizing QA results
"""

import os
import numpy as np
import jinja2

from .. import io
from ..plots.camfiber import plot_per_fibernum
from ..plots.amp import plot_amp_qa
from ..plots.spectra import plot_spectra_input
from . import camfiber

import bokeh
from bokeh.embed import components
from bokeh.layouts import gridplot, layout

def get_summary_plots(qadata, qprocdir=None):
    '''TODO: document'''

    header = qadata['HEADER']
    night = header['NIGHT']
    expid = header['EXPID']
    flavor = header['FLAVOR'].rstrip()
    if "PROGRAM" not in header :
        program = "no program in header!"
    else :
        program = header['PROGRAM'].rstrip()
    exptime = header['EXPTIME']

    html_components = dict(
        bokeh_version=bokeh.__version__, exptime='{:.1f}'.format(exptime),
        night=night, expid=expid, zexpid='{:08d}'.format(expid),
        flavor=flavor, program=program,
    )

    plot_width = 500

    #- CCD Read Noise
    fig = plot_amp_qa(qadata['PER_AMP'], 'READNOISE', title='CCD Amplifier Read Noise',
        qamin=1.5, qamax=4.0, ymin=0, ymax=5.0,
        plot_width=plot_width, plot_height=110)
    script, div = components(fig)
    html_components['READNOISE'] = dict(script=script, div=div)

    #- Raw flux
    if flavor.upper() in ['ARC', 'FLAT']:
        cameras = ['B', 'R', 'Z']  #- TODO: derive from data
        cds = camfiber.get_cds(qadata['PER_CAMFIBER'], ['INTEG_RAW_FLUX',], cameras)
        figs_list = camfiber.plot_per_fibernum(cds, 'INTEG_RAW_FLUX', cameras,
            height=120, ymin=0, width=plot_width)
        figs_list[0].title = bokeh.models.Title(text="Integrated Raw Flux Per Fiber")
        fn_camfiber_layout = layout(figs_list)

        script, div = components(fn_camfiber_layout)
        html_components['RAWFLUX'] = dict(script=script, div=div)

    #- Calib flux
    if flavor.upper() in ['SCIENCE']:
        cameras = ['B', 'R', 'Z']  #- TODO: derive from data
        cds = camfiber.get_cds(qadata['PER_CAMFIBER'], ['INTEG_CALIB_FLUX',], cameras)
        figs_list = camfiber.plot_per_fibernum(cds, 'INTEG_CALIB_FLUX', cameras,
            height=120, ymin=0, width=plot_width)
        figs_list[0].title = bokeh.models.Title(text="Integrated Sky-sub Calib Flux Per Fiber")
        fn_camfiber_layout = layout(figs_list)

        script, div = components(fn_camfiber_layout)
        html_components['CALIBFLUX'] = dict(script=script, div=div)

    #- Random Spectra
    if flavor.upper() in ['ARC', 'FLAT', 'SCIENCE'] and \
            'PER_CAMFIBER' in qadata and \
            qprocdir is not None:
        downsample = 4
        nfib = min(5, len(qadata['PER_CAMFIBER']))
        fibers = sorted(np.random.choice(qadata['PER_CAMFIBER']['FIBER'], size=nfib, replace=False))
        fibers = ','.join([str(tmp) for tmp in fibers])

        nightdir = os.path.dirname(os.path.normpath(qprocdir))
        specfig = plot_spectra_input(nightdir, expid, downsample,
            fibers, height=300, width=plot_width*2)
        script, div = components(specfig)
        html_components['SPECTRA'] = dict(script=script, div=div, fibers=fibers)

    return html_components

def write_summary_html(outfile, qadata, qprocdir):
    """Write the most important QA plots to outfile

    Args:
        outfile: output HTML file
        qadata : dict of QA tables, keys PER_AMP, PER_CAMFIBER, etc.
        qprocdir : directory containing qproc outputs (qframe*.fits, etc.)
    """

    plot_components = get_summary_plots(qadata, qprocdir)
    plot_components['qatype'] = 'summary'

    update_camfib_pc(plot_components, qadata)

    env = jinja2.Environment(
        loader=jinja2.PackageLoader('qqa.webpages', 'templates')
    )
    template = env.get_template('summary.html')
        
    #- TODO: Add links to whatever detailed QA pages exist
    
    html = template.render(**plot_components)

    #- Write HTML text to the output file
    with open(outfile, 'w') as fx:
        fx.write(html)

        
def update_camfib_pc(pc, qadata, 
                     metrics=['INTEG_RAW_FLUX', 'MEDIAN_RAW_SNR'], 
                     cameras=['B', 'R', 'Z'], 
                     titlespercam={'B':{'INTEG_RAW_FLUX':'Integrated Raw Counts', 'MEDIAN_RAW_SNR':'Median Raw S/N'}}, 
                     tools='pan,box_zoom,reset',
                    ):
    
    if 'PER_CAMFIBER' not in qadata:
        return
    
    data = qadata['PER_CAMFIBER']
    cds = camfiber.get_cds(data, metrics, cameras)

    fibernum_gridlist = []
    for attr in metrics:
        if attr in list(cds.data.keys()):
            figs_list = plot_per_fibernum(cds, attr, cameras, titles=titlespercam, tools=tools)

            fibernum_gridlist.extend(figs_list)

    camfiber_layout = layout(fibernum_gridlist)
    
    script, div = components(camfiber_layout)
    pc['CAMFIBER_METRICS'] = dict(script=script, div=div)

