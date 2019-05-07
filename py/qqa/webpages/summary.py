"""
Pages summarizing QA results
"""

import numpy as np
import jinja2

from .. import io

def write_summary_html(outfile, plot_components):
    """Write the most important QA plots to outfile
    
    Args:
        outfile: output HTML file
        plot_components: dictionary with keys night, expid, flavor, program,
            and QA plots
    """

    env = jinja2.Environment(
        loader=jinja2.PackageLoader('qqa.webpages', 'templates')
    )
    template = env.get_template('summary.html')
        
    #- TODO: Add links to whatever detailed QA pages exist
    
    html = template.render(**plot_components)

    #- Write HTML text to the output file
    with open(outfile, 'w') as fx:
        fx.write(html)
