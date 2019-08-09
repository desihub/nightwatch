import jinja2
import bokeh
from bokeh.embed import components

from ..plots.timeseries import generate_timeseries

def generate_timeseries_html(data, start_date, end_date, hdu, attribute, dropdown):
    '''
    Writes timeseries html file.
    Inputs:
        data: directory with night/exposure/qa-exposure.fits files
        start_date: start date for plotting (YYYYMMDD)
        end_date: end date for plotting (YYYYMMDD) 
        hdu: the qa level (PER_AMP, PER_CAMERA, etc)
        attribute: the metric being plotted
        dropdown: 
    Returns rendered Jinja template
    '''

    env = jinja2.Environment(
        loader=jinja2.PackageLoader('qqa.webpages', 'templates')
    )
    template = env.get_template('timeseries.html')

    html_components = dict(
        bokeh_version=bokeh.__version__, attribute=attribute,
        start=start_date, end=end_date, hdu=hdu,
        dropdown_hdu=dropdown,
    )

    fig = generate_timeseries(data, start_date, end_date, hdu, attribute)
    if fig is None:
        return "No data between {} and {}".format(start_date, end_date)

    script, div = components(fig)
    html_components['timeseries'] = dict(script=script, div=div)

    return template.render(html_components)
