import jinja2
import bokeh, os, re, sys

from ..plots.plotimage import main

def write_image_html(input, output, downsample):
    '''TODO: document'''

    env = jinja2.Environment(
        loader=jinja2.PackageLoader('qqa.webpages', 'templates')
    )
    template = env.get_template('plotimage.html')

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
        version=bokeh.__version__, downsample=str(downsample),
        basename=os.path.splitext(os.path.basename(input))[0],
        available=available, current=current, expid=expid
    )

    html = template.render(**html_components)

    #- Write HTML text to the output file
    with open(output, 'w') as fx:
        fx.write(html)

    print('Wrote {}'.format(output))
