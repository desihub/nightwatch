import jinja2
import bokeh

def write_placeholder_html(outfile, header, attr):
    '''Writes placeholder page for missing plots.
    Args:
        outfile: path to write html file to (str)
        header: header data for the exposure (night, expid, exptime, etc)
        attr: the type of missing plot (str); like PER_AMP, PER_CAMERA, etc.
   Returns html components.
        '''
    
    night = header['NIGHT']
    expid = header['EXPID']
    
    if 'OBSTYPE' in header :
        obstype = header['OBSTYPE'].rstrip().upper()
    else :
        log.warning('Use FLAVOR instead of missing OBSTYPE')
        obstype = header['FLAVOR'].rstrip().upper()
    if "PROGRAM" not in header :
        program = "no program in header!"
    else :
        program = header['PROGRAM'].rstrip()
    
    exptime = header['EXPTIME']
    
    env = jinja2.Environment(
        loader=jinja2.PackageLoader('nightwatch.webpages', 'templates')
    )
    template = env.get_template('placeholder.html')

    html_components = dict(
        bokeh_version=bokeh.__version__, exptime='{:.1f}'.format(exptime),
        night=night, expid=expid, zexpid='{:08d}'.format(expid),
        obstype=obstype, program=program, qatype=attr,
        num_dirs=2,
    )
    
    html = template.render(**html_components)

    #- Write HTML text to the output file
    with open(outfile, 'w') as fx:
        fx.write(html)

    return html_components

    
