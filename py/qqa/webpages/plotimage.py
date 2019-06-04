import jinja2
import bokeh, os

from ..plots.plotimage import main

def write_image_html(input, output, downsample):
    '''TODO: document'''

    env = jinja2.Environment(
        loader=jinja2.PackageLoader('qqa.webpages', 'templates')
    )
    template = env.get_template('plotimage.html')

    plot_script, plot_div = main(input, None, downsample)

    html_components = dict(
        plot_script = plot_script, plot_div = plot_div,
        version=bokeh.__version__, downsample=str(downsample), 
        basename=os.path.splitext(os.path.basename(input))[0]
    )

    html = template.render(**html_components)

    #- Write HTML text to the output file
    with open(output, 'w') as fx:
        fx.write(html)

    print('Wrote {}'.format(output))

