"""
Pages summarizing QA results
"""

import os
from collections import OrderedDict
import numpy as np
import jinja2

from .. import io
from ..qa.status import get_status, Status

def write_nights_table(outfile, exposures):
    """
    outfile: output HTML file
    exposures: table with columns NIGHT, EXPID
    """

    env = jinja2.Environment(
        loader=jinja2.PackageLoader('qqa.webpages', 'templates')
    )
    template = env.get_template('nights.html')

    html = template.render(nights=np.unique(exposures['NIGHT']))
    with open(outfile, 'w') as fx:
        fx.write(html)

def write_exposures_tables(outdir, exposures, nights=None):
    """
    outfile: output HTML files to outdir/YEARMMDD/exposures.html
    exposures: table with columns NIGHT, EXPID
    nights: optional list of nights to process
    """
    
    env = jinja2.Environment(
        loader=jinja2.PackageLoader('qqa.webpages', 'templates')
    )
    template = env.get_template('exposures.html')

    if nights is None:
        nights = np.unique(exposures['NIGHT'])    

    for night in nights:
        ii = (exposures['NIGHT'] == night)
        explist = list()
        for expid in sorted(exposures['EXPID'][ii]):
            
            qafile = io.findfile('qa', night, expid, basedir=outdir)
            qadata = io.read_qa(qafile)
            status = get_status(qadata)
            flavor = qadata['HEADER']['FLAVOR'].rstrip()
            link = '{expid:08d}/qa-summary-{expid:08d}.html'.format(
                night=night, expid=expid)

            expinfo = dict(night=night, expid=expid, flavor=flavor, link=link)
            
            #- TODO: have actual thresholds
            for i, qatype in enumerate(['PER_AMP', 'PER_CAMERA', 'PER_FIBER',
                                        'PER_CAMFIBER', 'PER_SPECTRO', 'PER_EXP']):
                if qatype not in status:
                    expinfo[qatype] = '-'
                else:
                    qastatus = Status(np.max(status[qatype]['QASTATUS']))
                    expinfo[qatype] = qastatus.name

            explist.append(expinfo)
                    
        html = template.render(night=night, exposures=explist)
        outfile = os.path.join(outdir, str(night), 'exposures.html')
        with open(outfile, 'w') as fx:
            fx.write(html)

