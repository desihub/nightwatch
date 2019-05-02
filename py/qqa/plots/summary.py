"""
Pages summarizing QA results
"""

import os
from collections import OrderedDict
import numpy as np
import jinja2

from .. import io
from ..qa.status import get_status, Status

def write_exp_summary(outfile, qadata, plot_components, header):
    """TODO: document"""
    from .core import bokeh_html_preamble
    template = bokeh_html_preamble
    
    header = dict(header)
    if 'PROGRAM' not in header:
        header['PROGRAM'] = 'Unknown'
    
    template += '''
    <body>
    <h1>QA Summary of {NIGHT} exposure {EXPID}</h1>
    <p>{EXPTIME:.0f} second {FLAVOR} (program {PROGRAM}) exposure</p>
    <p><a href="../qa-exposures.html">List of exposures</a><p>
    '''.format(**header)
    
    flavor = header['FLAVOR'].rstrip().upper()
    if flavor in ('ZERO', 'DARK', 'ARC', 'FLAT'):
        template += '''
        <div>{{ READNOISE_script }} {{ READNOISE_div }}</div>
        <div>{{ COSMICS_RATE_script }} {{ COSMICS_RATE_div }}</div>        
        '''
    elif flavor == 'SCIENCE':
        template += '''
        <div>{{ READNOISE_script }} {{ READNOISE_div }}</div>
        <h2>Integrated raw flux per fiber per camera</h2>
        <div>{{ INTEG_RAW_FLUX_script }} {{ INTEG_RAW_FLUX_div }}</div>
        '''
        
    #- Add links to whatever detailed QA pages exist
    details_links = OrderedDict()
    dirname = os.path.dirname(outfile)
    expid = header['EXPID']
    for qaname in ['amp', 'cam', 'fiber', 'camfiber', 'spectro', 'exp']:
        qafile = os.path.join(dirname, 'qa-{}-{:08d}.html'.format(qaname, expid))
        if os.path.exists(qafile):
            details_links[qaname] = os.path.basename(qafile)
    
    if len(details_links) > 0:
        template += "<h2>Details</h2>"
        for qaname, qafile in details_links.items():
            template += '<p><a href="{qafile}">{qaname}</a></p>'.format(
                qafile=qafile, qaname=qaname,
            )
    
    template += '</body></html>'
    
    html = jinja2.Template(template).render(**plot_components)

    #- Write HTML text to the output file
    with open(outfile, 'w') as fx:
        fx.write(html)
    

def write_night_expid(outdir, exposures):
    """
    outdir: write QA html output in outdir/YEARMMDD/EXPID/
    exposures: table with columns NIGHT, EXPID
    """
    nightsfile = os.path.join(outdir, 'qa-nights.html')
    write_nights_table(nightsfile, exposures)
    write_exposures_table(outdir, exposures)

def write_nights_table(outfile, exposures):
    """
    outfile: output HTML file
    exposures: table with columns NIGHT, EXPID
    """

    from .core import default_css
    html = """
    <!DOCTYPE html>
    <html lang="en-US">

    <head>
    <style>
    {default_css}
    </style>
    </head>

    <body>
    <h1>Nights with QA Data</h1>
    """.format(default_css=default_css)

    for night in np.unique(exposures['NIGHT']):
        link = '{}/qa-exposures.html'.format(night)
        html += '<p><a href="{}">{}</a></p>\n'.format(link, night)
    
    html += """
    </body>
    </html>
    """

    with open(outfile, 'w') as fx:
        fx.write(html)

def write_exposures_table(outdir, exposures, nights=None):
    """
    outfile: output HTML files to outdir/YEARMMDD/qa-exposures.html
    exposures: table with columns NIGHT, EXPID
    nights: optional list of nights to process
    """
    
    from .core import default_css
    
    if nights is None:
        nights = np.unique(exposures['NIGHT'])
        
    for night in sorted(nights):
        html = """
        <!DOCTYPE html>
        <html lang="en-US">

        <head>
        <style>
        {default_css}
        </style>
        </head>

        <body>
        <h1>Exposures on night {night}</h1>
        <p><a href="../qa-nights.html">List of nights</a></p>
        """.format(default_css=default_css, night=night)
        
        html += """
        <table>
        <tr>
          <th colspan="3">Metadata</th>
          <th colspan="6">QA Status</th>
        <tr>
          <th>NIGHT</th>
          <th>EXPID</th>
          <th>FLAVOR</th>
          <th>Amp</th>
          <th>Camera</th>
          <th>Fiber</th>
          <th>CamFib</th>
          <th>Spectro</th>
          <th>Exp</th>
        </tr>
        """
        
        ii = (exposures['NIGHT'] == night)
        for expid in sorted(exposures['EXPID'][ii]):
            
            qafile = io.findfile('qa', night, expid, basedir=outdir)
            qadata = io.read_qa(qafile)
            status = get_status(qadata)
            
            explink = '{expid:08d}/qa-summary-{expid:08d}.html'.format(
                night=night, expid=expid)
            flavor = qadata['HEADER']['FLAVOR'].rstrip()
            html += '''
                <tr>
                    <td>{night}</td>
                    <td><a href="{explink}">{expid}</a></td>
                    <td>{flavor}</td>
                '''.format(
                night=night, expid=expid, explink=explink, flavor=flavor)
            
            #- TODO: have actual thresholds
            for i, qatype in enumerate(['PER_AMP', 'PER_CAMERA', 'PER_FIBER',
                                        'PER_CAMFIBER', 'PER_SPECTRO', 'PER_EXP']):
                if qatype not in status:
                    html += "<td>-</td>\n"
                else:
                    qastatus = Status(np.max(status[qatype]['QASTATUS']))
                    html += "<td>{}</td>\n".format(qastatus.name)
                
            html += "</tr>\n"
    
        html += """
        </body>
        </html>
        """

        outfile = os.path.join(outdir, str(night), 'qa-exposures.html')
        with open(outfile, 'w') as fx:
            fx.write(html)

