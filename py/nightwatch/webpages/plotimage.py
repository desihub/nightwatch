import jinja2
import bokeh, os, re, sys

from ..plots.plotimage import main

def write_image_html(input, output, downsample, night):
    '''
    Writes a downsampled image to a given output file.
    Inputs:
        input: image fits file to be plotted
        output: the filepath to write html file to 
        downsample: downsample image NxN
        night: the night YYYYMMDD the image belongs to
    '''

    env = jinja2.Environment(
        loader=jinja2.PackageLoader('nightwatch.webpages', 'templates'),
        autoescape=select_autoescape(disabled_extensions=('txt',),
                                     default_for_string=True, 
                                     default=True,
    )
    template = env.get_template('preproc.html')

    plot_script, plot_div = main(input, None, downsample)

    input_dir = os.path.dirname(input)
    available = []
    preproc_files = [i for i in os.listdir(input_dir) if re.match(r'preproc.*', i)]
    for file in preproc_files:
        available += [file.split("-")[1]]

    current = os.path.basename(input).split("-")[1]
    expid = os.path.basename(input).split("-")[2].split(".")[0]

    html_components = dict(
        plot_script = plot_script, plot_div = plot_div,
        bokeh_version=bokeh.__version__, downsample=str(downsample), preproc=True,
        basename=os.path.splitext(os.path.basename(input))[0], night=night,
        available=available, current=current, expid=int(str(expid)), zexpid=expid,
        num_dirs=2, qatype='amp',
    )

    html = template.render(**html_components)

    #- Write HTML text to the output file
    with open(output, 'w') as fx:
        fx.write(html)

    print('Wrote {}'.format(output))


def write_preproc_table_html(input_dir, night, expid, downsample, output):
    '''
    Writes html file with preproc navigation table
    Inputs:
        input_dir: directory containing subdirectories with preproc images
        night: YYYYMMDD
        expid: exposure preproc images belong to
        downsample: downsample image NxN
        output: write html file here
    '''
    env = jinja2.Environment(
        loader=jinja2.PackageLoader('nightwatch.webpages', 'templates'),
        autoescape=select_autoescape(disabled_extensions=('txt',),
                                     default_for_string=True, 
                                     default=True,
    )
    template = env.get_template('preproc.html')

    available = []
    preproc_files = [i for i in os.listdir(input_dir) if re.match(r'preproc.*', i)]
    for file in preproc_files:
        available += [file.split("-")[1]]

    html_components = dict(
        version=bokeh.__version__, downsample=str(downsample),
        preproc=True, night=night, available=available,
        current=None, expid=int(expid), zexpid='{:08d}'.format(expid),
        num_dirs=2, qatype='amp',
    )

    html = template.render(**html_components)

    #- Write HTML text to the output file
    with open(output, 'w') as fx:
        fx.write(html)

    print('Wrote {}'.format(output))
