import numpy as np
import os

import jinja2
import bokeh
import bokeh.plotting as bk
from bokeh.embed import components
from bokeh.models import ColumnDataSource

from ..plots.nightlyqa import find_night, get_timeseries, plot_timeseries, get_nightlytable, get_moonloc, get_skypathplot, overlaid_hist, overlaid_hist_fine, get_exptype_counts, plot_timeseries_fine

def get_nightlyqa_html(night, exposures, fine_data, tiles, outdir, link_dict, height=250, width=250):
    '''outdir: same as directory where nightwatch files are generated. will be created in a new surveyqa subdirectory.'''
    
    summary_str = "summaryqa.html"
    last_str = link_dict['last']
    first_str = link_dict['first']
    night_links = link_dict['n{}'.format(night)]
    next_str = night_links['next']
    prev_str = night_links['prev']

    #- Filter exposures to just this night and adds columns DATETIME and MJD_hour
    night_exposures = find_night(exposures, night)
    night_fine_data = find_night(fine_data, night)

    html_components = dict(
        bokeh_version=bokeh.__version__, night=night, 
        summary_str = summary_str, next_str = next_str, 
        prev_str = prev_str, first_str = first_str, 
        last_str = last_str)
    
    #- Plot options
    #title='Airmass, Seeing, Exptime vs. Time for {}/{}/{}'.format(night[4:6], night[6:], night[:4])
    TOOLS = ['box_zoom', 'reset', 'wheel_zoom']
    TOOLTIPS = [("EXPID", "@EXPID"), ("TILEID", "@TILEID"), ("Exposure Time", "@EXPTIME"), ("Airmass", "@AIRMASS"), 
                ("Seeing", "@SEEING"), ("Transparency", "@TRANSP"), ('Hour Angle', '@HOURANGLE')]
    
    #- Create ColumnDataSource for linking timeseries plots
    COLS = ['EXPID', 'TIME', 'AIRMASS', 'SEEING', 'EXPTIME', 'TRANSP', 'SKY', 'HOURANGLE', "TILEID", "RA", "DEC"]
    fine_COLS = ['EXPID', 'TIME', 'AIRMASS', 'SEEING', 'TRANSP', 'SKY', 'HOURANGLE']
    exp_src = ColumnDataSource(data={c:np.array(night_exposures[c]) for c in COLS})
    fine_src = ColumnDataSource(data={c:np.array(night_fine_data[c]) for c in fine_COLS})

    #- Get timeseries plots for several variables
    min_border_right_time = 0
    min_border_left_time = 60
    min_border_right_hist = 0
    min_border_left_hist = 70
    min_border_right_count = 0
    min_border_left_count = 70
    min_border_right_sky = 0
    min_border_left_sky = 60

    time_hist_plot_height = 160
    
    airmass = plot_timeseries_fine(fine_src, exp_src, 'AIRMASS', 'green', tools=TOOLS, 
                                   x_range=None, title=None, tooltips=TOOLTIPS, width=600, 
                                   height=time_hist_plot_height, min_border_left=min_border_left_time,
                                   min_border_right=min_border_right_time, y_range=(1, 2.5))
    
    seeing = plot_timeseries_fine(fine_src, exp_src, 'SEEING', 'navy', tools=TOOLS, 
                                  x_range=airmass.x_range, tooltips=TOOLTIPS, width=600, 
                                  height=time_hist_plot_height, min_border_left=min_border_left_time,
                                  min_border_right=min_border_right_time, y_range=(0, 3.5))
    
    transp = plot_timeseries_fine(fine_src, exp_src, 'TRANSP', 'purple', tools=TOOLS, 
                                  x_range=airmass.x_range, tooltips=TOOLTIPS, width=600, 
                                  height=time_hist_plot_height, min_border_left=min_border_left_time,
                                  min_border_right=min_border_right_time, y_range=(0, 2.5))
    
    hourangle = plot_timeseries_fine(fine_src, exp_src, 'HOURANGLE', 'maroon', tools=TOOLS, 
                                     x_range=airmass.x_range, tooltips=TOOLTIPS, width=600, 
                                     height=time_hist_plot_height, min_border_left=min_border_left_time,
                                     min_border_right=min_border_right_time)
    
    brightness = plot_timeseries_fine(fine_src, exp_src, 'SKY', 'pink', tools=TOOLS, 
                                      x_range=airmass.x_range, tooltips=TOOLTIPS, width=600, 
                                      height=time_hist_plot_height, min_border_left=min_border_left_time,
                                      min_border_right=min_border_right_time, y_range=(17, 23))
    
    if len(exposures) != 0:
        exptime = plot_timeseries(exp_src, 'EXPTIME', 'darkorange', tools=TOOLS, x_range=airmass.x_range,
                                  tooltips=TOOLTIPS, width=600, height=time_hist_plot_height, y_range=(0, 950),
                                  min_border_left=min_border_left_time, min_border_right=min_border_right_time)
        
        #adding in the skyplot components
        skyplot = get_skypathplot(exp_src, tiles, night, width=600, height=250, tools=TOOLS, 
                                  tooltips=TOOLTIPS, min_border_left=min_border_left_sky,
                                  min_border_right=min_border_right_sky)
        
        #- Convert these to the components to include in the HTML
        script, div = components(bk.Column(skyplot, exptime, airmass, seeing, transp, hourangle, brightness))
        html_components['TIMESERIES'] = dict(script=script, div=div)
    
    else:
        #- Convert these to the components to include in the HTML
        script, div = components(bk.Column(airmass, seeing, transp, hourangle, brightness))
        html_components['TIMESERIES'] = dict(script=script, div=div)
        
    if len(exposures) != 0:
        #making the nightly table of values
        nightlytable = get_nightlytable(night_exposures)
        script, div = components(nightlytable)
        html_components['TABLE'] = dict(script=script, div=div)

    #adding in the components of the exposure types bar plot
    #exptypecounts = get_exptype_counts(exposures, calibs, width=250, height=250, min_border_left=min_border_left_count, min_border_right=min_border_right_count)
    #exptypecounts_script, exptypecounts_div = components(exptypecounts)

    #- Get overlaid histograms for several variables
    airmasshist = overlaid_hist_fine(fine_data, night_fine_data, 'AIRMASS', 'green', 250, 
                                     time_hist_plot_height, min_border_left=min_border_left_hist,
                                     min_border_right=min_border_right_hist, hist_min=1, hist_max=2.5)
    
    seeinghist = overlaid_hist_fine(fine_data, night_fine_data, 'SEEING', 'navy', 250, 
                                    time_hist_plot_height, min_border_left=min_border_left_hist,
                                    min_border_right=min_border_right_hist, hist_min=0, hist_max=3.2)
    
    transphist = overlaid_hist_fine(fine_data, night_fine_data, 'TRANSP', 'purple', 250, 
                                    time_hist_plot_height, min_border_left=min_border_left_hist,
                                    min_border_right=min_border_right_hist, hist_min=0, hist_max=2)
    
    hourangle = overlaid_hist_fine(fine_data, night_fine_data, "HOURANGLE", "maroon", 250, 
                                   time_hist_plot_height, min_border_left=min_border_left_hist,
                                   min_border_right=min_border_right_hist)
    
    brightnesshist = overlaid_hist_fine(fine_data, night_fine_data, 'SKY', 'pink', 250, 
                                        time_hist_plot_height, min_border_left=min_border_left_hist,
                                        min_border_right=min_border_right_hist, hist_min=0, hist_max=23)
    
    if len(exposures) != 0:
        exptimehist = overlaid_hist(exposures, night_exposures, 'EXPTIME', 'darkorange', 250, 
                                    time_hist_plot_height, min_border_left=min_border_left_hist,
                                    min_border_right=min_border_right_hist, hist_min=0)
        
        empty_plot = bk.figure(plot_width=250, plot_height=250)
        empty_plot.outline_line_color = None
        empty_plot.toolbar_location = None

        #adding in the components of the overlaid histograms
        script, div = components(bk.Column(empty_plot, exptimehist, airmasshist, seeinghist, transphist, hourangle, brightnesshist))
        html_components['HIST'] = dict(script=script, div=div)
    
    else:
        script, div = components(bk.Column(airmasshist, seeinghist, transphist, hourangle, brightnesshist))
        html_components['HIST'] = dict(script=script, div=div)
    
    env = jinja2.Environment(
        loader=jinja2.PackageLoader('nightwatch.webpages', 'templates')
    )
    
    template = env.get_template('nightlyqa.html')
    
     #- Combine template + components -> HTML
    html = template.render(**html_components)

    #- Write HTML text to the output file
    outfile = os.path.join(outdir, 'surveyqa/nightqa-{}.html'.format(night))
    
    with open(outfile, 'w') as fx:
        fx.write(html)
    
    print('Wrote {}'.format(outfile))

    return html_components