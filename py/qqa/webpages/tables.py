"""
Pages summarizing QA results
"""

import os, json
from collections import OrderedDict

import numpy as np
import jinja2
from astropy.table import Table

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

def _write_expid_links(outdir, exposures, nights=None):
    """
    Write outdir/YEARMMDD/EXPID/explinks.js with info about prev/next exp
    
    may re-sort input exposures list by NIGHT,EXPID
    """
    
    exposures = Table(exposures)
    exposures.sort(keys=['NIGHT', 'EXPID'])

    if nights is None:
        nights = set(np.unique(exposures['NIGHT']))
    else:
        nights = set(nights)

    #- Determine links for all nights, including those not in `nights`,
    #- since the prev/next night extend into a non-listed night

    #- links[night][zexpid]['prev'|'next'] = dict(night, zexpid)
    links = dict()
    nexp = len(exposures)
    for i in range(nexp):
        night = int(exposures['NIGHT'][i])

        if night not in links:
            links[night] = dict()
        
        zexpid = '{:08d}'.format(exposures['EXPID'][i])
        assert zexpid not in links[night]

        if i == 0:
            prevlink = None
        else:
            prevnight = int(exposures['NIGHT'][i-1])
            prevzexpid = '{:08d}'.format(exposures['EXPID'][i-1])
            prevlink = dict(night=prevnight, zexpid=prevzexpid)
    
        if i+1 < nexp:
            nextnight = int(exposures['NIGHT'][i+1])
            nextzexpid = '{:08d}'.format(exposures['EXPID'][i+1])
            nextlink = dict(night=nextnight, zexpid=nextzexpid)
        else:
            nextlink = None

        links[night][zexpid] = dict(prev=prevlink, next=nextlink)

    #- Only update explinks files for nights in the nights list
    for night in nights:
        outfile = os.path.join(outdir, str(night), 'explinks-{}.js'.format(night))
        with open(outfile, 'w') as fx:
            fx.write("""/*
Returns exposure prev/next links for this night as a nested dictionary

    explinks[zexpid]["prev"|"next"] = [night, zexpid]

where zexpid is the 8-character zero-padded exposure ID.
The first and last exposure have prev/next as [null, null]
*/
get_explinks({})
""".format(json.dumps(links[night], indent=2)))

def write_exposures_tables(indir,outdir, exposures, nights=None):
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
            
            qafile = io.findfile('qa', night, expid, basedir=indir)
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

        _write_expid_links(outdir, exposures, nights)

