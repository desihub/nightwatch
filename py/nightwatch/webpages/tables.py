"""
Pages summarizing QA results
"""

import os, json, re, time
from collections import OrderedDict, Counter

import numpy as np
import jinja2
from jinja2 import select_autoescape
from astropy.table import Table
from astropy.time import Time

import desiutil.log

from .. import io
from ..qa.status import get_status, Status

def write_calendar(outfile, nights):
    """
    Writes nights calendar html file

    Args:
        outfile: output HTML file
        nights: dict-like nights[night] = number_of_exposures

    Returns: HTML file written to outfile path
    """    
    env = jinja2.Environment(
        loader=jinja2.PackageLoader('nightwatch.webpages', 'templates'),
        autoescape=select_autoescape(disabled_extensions=('txt',),
                                     default_for_string=True, 
                                     default=True)
    )
    
    template = env.get_template('nights.html')

    # Split night YEARMMDD into YEAR, MM-1, DD
    nights_sep = list()
    for night, numexp in sorted(nights.items()):
        night = str(night)
        nights_sep.append({
            "name" : night,
            "year" : night[0:4],
            "month" : str(int(night[4:6])-1), # yes, JS months are 0-indexed
            "day" : night[6:],                #      and days are 1-indexed...
            "numexp" : numexp
            })

    html = template.render(nights=nights_sep)
    tmpfile = outfile + '.tmp' + str(os.getpid())
    with open(tmpfile, 'w') as fx:
        fx.write(html)

    os.rename(tmpfile, outfile)

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
    tmpfile = outfile + '.tmp' + str(os.getpid())
    with open(tmpfile, 'w') as fx:
        fx.write("""/*
Returns night prev/next links as a string

    nightlinks["prev_n"|"next_n"] = path-to-prev/next-night-exposure.html

where zexpid is the 8-character zero-padded exposure ID.
The first and last exposure have prev/next as [null, null]
*/
get_nightlinks({})
""".format(json.dumps(links, indent=2)))

    os.rename(tmpfile, outfile)


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
        tmpfile = outfile + '.tmp' + str(os.getpid())
        with open(tmpfile, 'w') as fx:
            fx.write("""/*
Returns exposure prev/next links for this night as a nested dictionary

    explinks[zexpid]["prev"|"next"] = [night, zexpid]

where zexpid is the 8-character zero-padded exposure ID.
The first and last exposure have prev/next as [null, null]
*/
get_explinks({})
""".format(json.dumps(links[night], indent=2)))

        os.rename(tmpfile, outfile)


def write_exposures_tables(indir, outdir, exposures, nights=None):
    """
    Writes exposures table for each night available
    Args:
        outfile: output HTML files to outdir/YEARMMDD/exposures.html
        exposures: table with columns NIGHT, EXPID
    Options:
        nights: optional list of nights to process
    """

    log = desiutil.log.get_logger()
    env = jinja2.Environment(
        loader=jinja2.PackageLoader('nightwatch.webpages', 'templates'),
        autoescape=select_autoescape(disabled_extensions=('txt',),
                                     default_for_string=True, 
                                     default=True)
    )
    
    template = env.get_template('exposures.html')

    if nights is None:
        nights = np.unique(exposures['NIGHT'])

    for night in nights:
        log.debug('{} Generating exposures table for {}'.format(
            time.asctime(), night))
        ii = (exposures['NIGHT'] == int(night))
        explist = list()
        
        night_exps = exposures[ii]
        night_exps.sort('EXPID')
        for row in night_exps:
            expid = row['EXPID']
            
            #- adds failed expid to table
            if row['FAIL'] == 1:
                link = '{expid:08d}/qa-summary-{expid:08}-logfiles_table.html'.format(night=night, expid=expid)
                expinfo = dict(night=night, expid=expid, link=link, fail=1)
                explist.append(expinfo)
                continue
            
                        
            qafile = io.findfile('qa', night, expid, basedir=indir)
            qadata = io.read_qa(qafile)
            status = get_status(qadata, night)
            if 'OBSTYPE' in qadata['HEADER'] :
                obstype = qadata['HEADER']['OBSTYPE'].rstrip().upper()
            else :
                log.warning('Use FLAVOR instead of missing OBSTYPE')
                obstype = qadata['HEADER']['FLAVOR'].rstrip().upper()
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

            expinfo = dict(night=night, expid=expid, obstype=obstype, link=link, 
                           exptime=exptime, spectros=spectros, fail=0)

            hdr = qadata['HEADER']
            expinfo['PROGRAM'] = hdr['PROGRAM'] if 'PROGRAM' in hdr else '?'

            #- TILEID with link to fiberassign QA
            if 'TILEID' in hdr:
                tileid = hdr['TILEID']
                expinfo['TILEID'] = tileid
                tilegroup = '{:03d}'.format(tileid//1000)
                expinfo['TILEID_LINK'] = f'https://data.desi.lbl.gov/desi/target/fiberassign/tiles/trunk/{tilegroup}/fiberassign-{tileid:06d}.png'
            else:
                expinfo['TILEID'] = -1
                expinfo['TILEID_LINK'] = 'na'

            #- KPNO local time (MST=Mountain Standard Time)
            if 'MJD-OBS' in hdr:
                expinfo['MST'] = Time(hdr['MJD-OBS']-7/24, format='mjd').strftime('%H:%M')
            else:
                expinfo['MST'] = '?'

            #- Adds qproc to the expid status
            #- TODO: add some catches to this for robustness, e.g. the '-' if QPROC is missing
            #if len(row['QPROC']) == 0 and row['QPROC_EXIT'] == 0:
            if len(row['QPROC']) == 0 and row['QPROC_EXIT'] == 0:
                expinfo['QPROC'] = 'ok'
            else:
                expinfo['QPROC'] = 'error'
            expinfo['QPROC_link'] = '{expid:08d}/qa-summary-{expid:08d}-logfiles_table.html'.format(expid=expid)

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
                    if qatype != 'QPROC':
                        expinfo[qatype + "_link"] = '{expid:08d}/qa-{name}-{expid:08d}.html'.format(expid=expid, name=short_name)            

            explist.append(expinfo)

        html = template.render(night=night, exposures=explist, autoreload=True,
            staticdir='../static')
        outfile = os.path.join(outdir, str(night), 'exposures.html')
        tmpfile = outfile + '.tmp' + str(os.getpid())
        with open(tmpfile, 'w') as fx:
            fx.write(html)

        os.rename(tmpfile, outfile)

    #- Update expid and night links only once at the end
    _write_expid_links(outdir, exposures, nights)
    _write_night_links(outdir)
