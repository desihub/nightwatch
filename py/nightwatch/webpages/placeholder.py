import jinja2
from jinja2 import select_autoescape
import bokeh
from desiutil.log import get_logger

def write_placeholder_html(outfile, header, attr, message=None):
    '''Writes placeholder page for missing plots.
    Args:
        outfile: path to write html file to (str)
        header: header data for the exposure (night, expid, exptime, etc)
        attr: the type of missing plot (str); like PER_AMP, PER_CAMERA, etc.

    Options:
        message (str): optional message to include in placeholder file

    Returns html components.
    '''

    log=get_logger()
    
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
        loader=jinja2.PackageLoader('nightwatch.webpages', 'templates'),
        autoescape=select_autoescape(disabled_extensions=('txt',),
                                     default_for_string=True, 
                                     default=True)
    )
    
    template = env.get_template('placeholder.html')

    html_components = dict(
        bokeh_version=bokeh.__version__, exptime='{:.1f}'.format(exptime),
        night=night, expid=expid, zexpid='{:08d}'.format(expid),
        obstype=obstype, program=program, qatype=attr,
        num_dirs=2,
    )
    if message is not None:
        html_components['message'] = message
    
    html = template.render(**html_components)

    #- Write HTML text to the output file
    with open(outfile, 'w') as fx:
        fx.write(html)

    return html_components

#- utility function to print tracebacks for failed plotting
def handle_failed_plot(htmlfile, header, qatype):
    """
    Write placeholder file with error traceback for a failed plot

    Args:
        htmlfile (str): filename to write
        header (dict-like): header metadata (NIGHT, EXPID, EXPTIME, etc)
        qatype (str): the type of missing plot, e.g. PER_AMP, PER_CAMERA, etc.

    Returns bokeh plot components dict from func:`web_placeholder`
    """
    import sys
    import traceback
    lines = traceback.format_exception(*sys.exc_info())
    msg = f'ERROR generating {htmlfile}\n' + ''.join(lines)
    print(msg)
    print('Proceeding with making other plots')
    pc = write_placeholder_html(
            htmlfile, header, "PER_CAMFIBER", message=msg)
    return pc
    
