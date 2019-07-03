"""
Pages summarizing QA results
"""

import os, json, re
from collections import OrderedDict, Counter

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


    expo = Table(exposures)

    # Count exposures per night
    expcounter = Counter(expo["NIGHT"])

    # Split night YEARMMDD into YEAR, MM-1, DD
    nights_sep = list()
    for night, numexp in sorted(expcounter.items()):
        night = str(night)
        nights_sep.append({
            "name" : night,
            "year" : night[0:4],
            "month" : str(int(night[4:6])-1), # yes, JS months are 0-indexed
            "day" : night[6:],                #      and days are 1-indexed...
            "numexp" : numexp
            })

    html = template.render(nights=nights_sep)
    with open(outfile, 'w') as fx:
        fx.write(html)

def _write_night_links(outdir):
    all_files = os.listdir(outdir)
    regex = re.compile(r'[0-9]{8}')
    list_nights = []
    for fil in all_files:
        if regex.match(fil):
            list_nights += [fil]
    list_nights.sort()

    links = dict()
    for i in range(len(list_nights)):
        night = list_nights[i]
        prev_n = None
        next_n = None

        if i != len(list_nights)-1:
            next_n = os.path.join("..", list_nights[i+1], "exposures.html")

        if i != 0:
            prev_n = os.path.join("..", list_nights[i-1], "exposures.html")

        links[night] = dict(prev_n = prev_n, next_n = next_n)

    outfile = os.path.join(outdir, 'nightlinks.js')
    with open(outfile, 'w') as fx:
        fx.write("""/*
Returns night prev/next links as a string

    nightlinks["prev_n"|"next_n"] = path-to-prev/next-night-exposure.html

where zexpid is the 8-character zero-padded exposure ID.
The first and last exposure have prev/next as [null, null]
*/
get_nightlinks({})
""".format(json.dumps(links, indent=2)))


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
            exptime = qadata['HEADER']['EXPTIME']
            
            from ..plots.core import parse_numlist
            peramp = status.get('PER_AMP')
            if peramp:
                list_specs = list(set(peramp['SPECTRO']))
                spectros = parse_numlist(list_specs)
            else:
                spectros = '???'
            
            link = '{expid:08d}/qa-summary-{expid:08d}.html'.format(
                night=night, expid=expid)

            expinfo = dict(night=night, expid=expid, flavor=flavor, link=link, 
                           exptime=exptime, spectros=spectros)

            #- TODO: have actual thresholds
            for i, qatype in enumerate(['PER_AMP', 'PER_CAMERA', 'PER_FIBER',
                                        'PER_CAMFIBER', 'PER_SPECTRO', 'PER_EXP']):
                if qatype not in status:
                    expinfo[qatype] = '-'
                    expinfo[qatype + "_link"] = "na"
                else:
                    qastatus = Status(np.max(status[qatype]['QASTATUS']))
                    short_name = qatype.split("_")[1].lower()

                    expinfo[qatype] = qastatus.name
                    expinfo[qatype + "_link"] = '{expid:08d}/qa-{name}-{expid:08d}.html'.format(
                        expid=expid, name=short_name)
            
            
            #- Adds qproc to the expid status
            #- TODO: add some catches to this for robustness, e.g. the '-' if QPROC is missing
            qproc_fails = exposures[ii][exposures[ii]['EXPID']==expid]['QPROC'][0]
            if qproc_fails == 0:
                expinfo['QPROC'] = 'ok'
            else:
                expinfo['QPROC'] = 'error'

            expinfo['QPROC_link'] = '{expid:08d}/qa-summary-{expid:08d}-logfiles_table.html'.format(expid=expid)

            explist.append(expinfo)

        html = template.render(night=night, exposures=explist, autoreload=True,
            staticdir='../cal_files')
        outfile = os.path.join(outdir, str(night), 'exposures.html')
        with open(outfile, 'w') as fx:
            fx.write(html)

        _write_expid_links(outdir, exposures, nights)

    _write_night_links(outdir)
