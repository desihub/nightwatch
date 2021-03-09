import numpy as np
import jinja2
import bokeh
from glob import glob
import fitsio
import scipy

from astropy.table import Table
from astropy import units as u
from astropy.coordinates import SkyCoord
import bokeh
import bokeh.plotting as bk
import bokeh.palettes as bp
from bokeh.models import TapTool, OpenURL

from ..plots.fiber import plot_fibers_focalplane, plot_fibernums
# from ..plots.core import get_colors


def plot_camfib_focalplane(cds, attribute, cameras, percentiles={},
                      zmaxs={}, zmins={}, titles={},
                      tools='pan,box_zoom,reset'):
    '''
    ARGS:
        cds : ColumnDataSource of data
        attribute : string corresponding to column name in DATA
        cameras : list of string representing unique camera values

    Options:
        percentiles : dictionary of cameras corresponding to (min,max)
            to clip data for histogram
        zmaxs : dictionary of cameras corresponding to hardcoded max values
            to clip data for histogram
        zmins : dictionary of cameras corresponding to hardcoded min values
            to clip data for histogram
        titles : dictionary of titles per camera for a group of camfiber plots
            where key-value pairs represent a camera-attribute plot title
        tools, tooltips : supported plot interactivity features
    '''
    if attribute not in list(cds.data.keys()):
        raise ValueError('{} not in cds.data.keys'.format(attribute))

    metric = np.array(cds.data.get(attribute), copy=True)



    #- for hover tool
    attr_formatted_str = "@" + attribute + '{(0.00 a)}'
    tooltips = [("FIBER", "@FIBER"), ("(X, Y)", "(@X, @Y)"),
                (attribute, attr_formatted_str)]

    figs_list = []
    hfigs_list = []

    for i in range(len(cameras)):
        c = cameras[i]

        first_x_range = bokeh.models.Range1d(-420, 420)
        first_y_range = bokeh.models.Range1d(-420, 420)

        #- shared ranges to support linked features
        if not figs_list:
            fig_x_range = first_x_range
            fig_y_range = first_y_range
        else:
            fig_x_range = figs_list[0].x_range
            fig_y_range = figs_list[0].y_range

        colorbar = True

        # adjusts for outliers on the scale of the camera

        in_cam = np.char.upper(np.array(cds.data['CAM']).astype(str)) == c.upper()
        cam_metric = metric[in_cam]


        pmin, pmax = np.percentile(cam_metric, (2.5, 97.5))

        hist_x_range = (pmin * 0.99, pmax * 1.01)

        fig, hfig = plot_fibers_focalplane(cds, attribute, cam=c,
                        percentile=percentiles.get(c),
                        zmin=zmins.get(c), zmax=zmaxs.get(c),
                        title=titles.get(c, {}).get(attribute),
                        tools=tools, hist_x_range=hist_x_range,
                        fig_x_range=fig_x_range, fig_y_range=fig_y_range,
                        colorbar=colorbar)

        figs_list.append(fig)
        hfigs_list.append(hfig)

    return figs_list, hfigs_list


def plot_camfib_fot(cds, attribute, cameras, percentiles={},
                      zmaxs={}, zmins={}, titles={},
                      tools='pan,box_zoom,reset'):
    '''
    ARGS:
        cds : ColumnDataSource of data
        attribute : string corresponding to column name in DATA
        cameras : list of string representing unique camera values

    Options:
        percentiles : dictionary of cameras corresponding to (min,max)
            to clip data for histogram
        zmaxs : dictionary of cameras corresponding to hardcoded max values
            to clip data for histogram
        zmins : dictionary of cameras corresponding to hardcoded min values
            to clip data for histogram
        titles : dictionary of titles per camera for a group of camfiber plots
            where key-value pairs represent a camera-attribute plot title
        tools, tooltips : supported plot interactivity features
    '''
    if attribute not in list(cds.data.keys()):
        raise ValueError('{} not in cds.data.keys'.format(attribute))

    metric = np.array(cds.data.get(attribute), copy=True)



    #- for hover tool
    attr_formatted_str = "@" + attribute + '{(0.00 a)}'
    tooltips = [("FIBER", "@FIBER"), ("(X, Y)", "(@X, @Y)"),
                (attribute, attr_formatted_str)]

    figs_list = []

    for i in range(len(cameras)):
        c = cameras[i]

        first_x_range = bokeh.models.Range1d(-420, 420)
        first_y_range = bokeh.models.Range1d(-420, 420)

        #- shared ranges to support linked features
        if not figs_list:
            fig_x_range = first_x_range
            fig_y_range = first_y_range
        else:
            fig_x_range = figs_list[0].x_range
            fig_y_range = figs_list[0].y_range

        # adjusts for outliers on the scale of the camera

        in_cam = np.char.upper(np.array(cds.data['CAM']).astype(str)) == c.upper()
        cam_metric = metric[in_cam]


        pmin, pmax = np.percentile(cam_metric, (2.5, 97.5))

        colorbar = True

        hist_x_range = (pmin * 0.99, pmax * 1.01)

        fig, hfig = plot_fibers_focalplane(cds, attribute, cam=c,
                        percentile=percentiles.get(c),
                        zmin=zmins.get(c), zmax=zmaxs.get(c),
                        title=titles.get(c, {}).get(attribute),
                        palette = list(np.flip(bp.YlGnBu[5])),
                        tools=tools, hist_x_range=hist_x_range,
                        fig_x_range=fig_x_range, fig_y_range=fig_y_range,
                        colorbar=False, on_target=True)

        figs_list.append(fig)


    return figs_list

def plot_camfib_posacc(pcd,attribute,percentiles={},
                      tools='pan,box_zoom,reset'):

    figs_list = []
    hfigs_list = []
    metric = np.array(pcd.data.get(attribute), copy=True)
    metric = metric[np.where(metric>0)] #removed nan values
    pmin, pmax = np.percentile(metric, (2.5, 97.5))

    if attribute == 'BLIND':
        title = "Max Blind Move: {:.2f}um".format(np.max(metric))
        zmax = 200
    elif attribute == 'FINAL_MOVE':
        title = 'RMS Final Move: {:.2f}um'.format(np.sqrt(np.square(metric).mean()))
        zmax = 30


    attr_formatted_str = "@" + attribute + '{(0.00 a)}'
    tooltips = [("FIBER", "@FIBER"), ("(X, Y)", "(@X, @Y)"),
                (attribute, attr_formatted_str)]


    first_x_range = bokeh.models.Range1d(-420, 420)
    first_y_range = bokeh.models.Range1d(-420, 420)

    if not figs_list:
        fig_x_range = first_x_range
        fig_y_range = first_y_range
    else:
        fig_x_range = figs_list[0].x_range
        fig_y_range = figs_list[0].y_range

    hist_x_range = (pmin * 0.99, zmax)
    c = '' # So not to change plot_fibers_focalplane code
    fig, hfig = plot_fibers_focalplane(pcd, attribute,cam=c, 
                        percentile=percentiles.get(c),
                        palette = bp.Magma256,
                        title=title,zmin=0, zmax=zmax,
                        tools=tools, hist_x_range=hist_x_range,
                        fig_x_range=fig_x_range, fig_y_range=fig_y_range,
                        colorbar=True)

    figs_list.append(fig)
    hfigs_list.append(hfig)
    return figs_list, hfigs_list


def plot_per_fibernum(cds, attribute, cameras, titles={},
        tools='pan,box_zoom,tap,reset', width=700, height=80,
        ymin=None, ymax=None):
    '''
    ARGS:
        cds : ColumnDataSource of data
        attribute : string corresponding to column name in DATA
        cameras : list of string representing unique camera values
        width : width of individual camera plots in pixels
        height : height of individual camera plots in pixels
        ymin/ymax : y-axis ranges unless data exceed those ranges

    Options:
        titles : dictionary of titles per camera for a group of camfiber plots
            where key-value pairs represent a camera-attribute plot title
        tools, tooltips : supported plot interactivity features
    '''
    if attribute not in list(cds.data.keys()):
        return

    metric = np.array(cds.data.get(attribute), copy=True)

    #- for hover tool
    attr_formatted_str = "@" + attribute + '{(0.00 a)}'
    tooltips = [("FIBER", "@FIBER"), ("(X, Y)", "(@X, @Y)"),
                (attribute, attr_formatted_str)]

    figs_list = []

    for i in range(len(cameras)):
        c = cameras[i]

        min_fiber = max(0, min(list(cds.data['FIBER'])))
        max_fiber = min(5000, max(list(cds.data['FIBER'])))
        first_x_range = bokeh.models.Range1d(min_fiber-1, max_fiber+1)

        #- shared ranges to support linked features, additional plot features
        if i == 0:
            fig_x_range = first_x_range
            toolbar_location='above'
            heightpad = 25 #- extra space for title & toolbar
        else:
            fig_x_range = figs_list[0].x_range
            toolbar_location=None
            heightpad = 0
        
        #- axis labels for the last camera
        if i == (len(cameras) - 1):
            xaxislabels = True
            heightpad = 50
        else:
            xaxislabels = False
        
        #- focused y-ranges unless outliers in data
        cam_metric = metric[np.array(cds.data.get('CAM')) == c]

        if len(cam_metric) == 0:
            #- create a blank plot as a placeholder
            fig = bokeh.plotting.figure(plot_width=width, plot_height=height)
            figs_list.append(fig)
            continue

        plotmin = min(ymin, np.min(cam_metric) * 0.9) if ymin else np.min(cam_metric) * 0.9
        plotmax = max(ymax, nnp.max(cam_metric) * 1.1) if ymax else np.max(cam_metric) * 1.1

        fig_y_range = bokeh.models.Range1d(plotmin, plotmax)

        
        fig = plot_fibernums(cds, attribute, cam=c, title=titles.get(c, {}).get(attribute),
                             tools=tools,tooltips=tooltips, toolbar_location=toolbar_location,
                             fig_x_range=fig_x_range, fig_y_range=fig_y_range,
                             width=width, height=height+heightpad, xaxislabels=xaxislabels,
                            )

        taptool = fig.select(type=TapTool)
        #- Default to qcframe upon click, unless raw camfiber plot
        if "RAW" in attribute:
            taptool.callback = OpenURL(url="spectra/input/@FIBER/qframe/4x/")
        else:
            taptool.callback = OpenURL(url="spectra/input/@FIBER/qcframe/4x/")
        figs_list.append(fig)
        
    return figs_list

def linregress_iter(x,y,sigclip=5):
    sel = np.full(len(x), True)
    for j in range(3):
        linfit = scipy.stats.linregress(x[sel],y[sel])
        residual = y-linfit.intercept-linfit.slope*x
        sel = (residual<sigclip*np.std(residual[sel]))
    return linfit

def galactic_coord(header):
    # Compute Galactic longitude and latitude
    loc = SkyCoord(ra=header["SKYRA"]*u.degree, dec=header["SKYDEC"]*u.degree, frame='icrs')
    return loc.galactic

def radec_to_xyz(ra,dec):
    ra = ra*np.pi/180.0
    dec = dec*np.pi/180.0
    return np.array([np.cos(ra)*np.cos(dec), np.sin(ra)*np.cos(dec), np.sin(dec)])

def moon_elevation(header):
    # Compute the elevation of the moon
    lst = header["TCSST"].split(":")
    zenith = radec_to_xyz(15*(float(lst[0])+float(lst[1])/60.0+float(lst[2])/3600.0), float(header["OBS-LAT"]))
    moon = radec_to_xyz(header["MOONRA"], header["MOONDEC"])
    return np.arcsin(np.dot(zenith,moon))*180.0/np.pi

def sun_elevation(header):
    # Compute the elevation of the sun and phase of moon
    lst = header["TCSST"].split(":")
    zenith = radec_to_xyz(15*(float(lst[0])+float(lst[1])/60.0+float(lst[2])/3600.0), float(header["OBS-LAT"]))
    try: sun = radec_to_xyz(header["SUNRA"], header["SUNDEC"])
    except:
        # These keywords were only added in mid-February 2021; return False if not available.
        return False, False
    moon = radec_to_xyz(header["MOONRA"], header["MOONDEC"])
    phase = (1.0-np.arccos(np.dot(moon,sun))/np.pi)   # 0 = moon, sun together; 1 = opposed.
    return np.arcsin(np.dot(zenith,sun))*180.0/np.pi, phase

def plot_fractionalresidual(fiber, header, expos, position=False, plot_height=500, plot_width=500):
    if position==False: position = expos
    bfiber = fiber[np.where(fiber['CAM']=='B')]
    rfiber = fiber[np.where(fiber['CAM']=='R')]
    zfiber = fiber[np.where(fiber['CAM']=='Z')]
    bfiber.sort(order="FIBER")
    rfiber.sort(order="FIBER")
    zfiber.sort(order="FIBER")
    #print(file,len(rfiber))

    limit = 0.05
    bright_neighbor = (bfiber["MEDIAN_RAW_FLUX"]<limit*np.roll(bfiber["MEDIAN_RAW_FLUX"], 1)) \
        |(bfiber["MEDIAN_RAW_FLUX"]<limit*np.roll(bfiber["MEDIAN_RAW_FLUX"],-1)) \
        |(rfiber["MEDIAN_RAW_FLUX"]<limit*np.roll(rfiber["MEDIAN_RAW_FLUX"], 1)) \
        |(rfiber["MEDIAN_RAW_FLUX"]<limit*np.roll(rfiber["MEDIAN_RAW_FLUX"],-1)) \
        |(zfiber["MEDIAN_RAW_FLUX"]<limit*np.roll(zfiber["MEDIAN_RAW_FLUX"], 1)) \
        |(zfiber["MEDIAN_RAW_FLUX"]<limit*np.roll(zfiber["MEDIAN_RAW_FLUX"],-1))
    print("Excluding", np.sum(bright_neighbor), "fibers with bright neighbors.")

    spectrodata = "/global/cfs/cdirs/desi/spectro/data/" # hardcoded
    desidata = "/global/cfs/cdirs/desi/users/benjikan/nightwatch/" # HARDCODED

    # position = os.path.join('{:08d}'.format(night), '{:08d}'.format(expid))

    file = glob(desidata+position+"/coordinates-*.fits")[0]
    fits = fitsio.FITS(file)
    coords = fits["DATA"].read()
    coords = coords[np.isfinite(coords['FA_FIBER'])]
    print(file, len(coords))
    coords.sort(order='FA_FIBER')
    dx = coords["FIBER_DX"]*1000
    dy = coords["FIBER_DY"]*1000
    dr = np.sqrt(dx*dx+dy*dy)
    goodfiber = ((coords["FLAGS_COR_1"]&4)>0)&(coords["FLAGS_COR_1"]<65535)&(dr<30)&~bright_neighbor

    file = glob(spectrodata+position+"/fiberassign-*")[0]
    fits = fitsio.FITS(file)
    fa = fits["FIBERASSIGN"].read()
    fa.sort(order="FIBER")
    print(file, len(fa))
    try:
        standard = goodfiber&(fa["OBJTYPE"]=='TGT')&((fa['SV1_DESI_TARGET']&0xe00000000)>0)    # Bits 33..35
    except:
        print("This plugmap has no field SV1_DESI_TARGET.  Skipping!")
        return

    gaia_volunteer = (fa["MORPHTYPE"]=="GPSF")|(fa["MORPHTYPE"]=="GGAL")
    print("Excluding",np.sum(gaia_volunteer),"GAIA-catalog targets from analysis; no FIBERFLUX available.")
    
    sky = goodfiber&(fa["OBJTYPE"]=='SKY')
    good = goodfiber&(fa["OBJTYPE"]=='TGT')&~gaia_volunteer
    # Objects of MORPHTYPE GPSF and GGAL do not have FIBERFLUX_R set.
    # if len(rfiber)!=len(fa): return
    print("Found", np.sum(good),"usable target fibers,", np.sum(standard),"standard stars, and", np.sum(sky), "skies.")

    exptime = header['EXPTIME']
    exptime_ksec = header['EXPTIME']/1000.0
    linfit = linregress_iter(fa["FIBERFLUX_R"][good|sky], rfiber["MEDIAN_RAW_FLUX"][good|sky])
    rskycounts = linfit.intercept/exptime_ksec

    linfit = linregress_iter(fa["FIBERFLUX_R"][standard], rfiber["MEDIAN_RAW_FLUX"][standard])
    rstarcountrate = linfit.slope*10/exptime_ksec    # We'll scale this to fiberflux=10, which is r_fiber = 20 mag.

    sel = standard&(fa["FIBERFLUX_R"]>1)
    flux = fa["FIBERFLUX_R"][sel]
    snr = rfiber["MEDIAN_CALIB_SNR"][sel]
    counts = rfiber["MEDIAN_CALIB_FLUX"][sel]

    linfit = linregress_iter(flux, counts)
    ratio = counts/(linfit.intercept+linfit.slope*flux)
    rsn2 = rstarcountrate**2/rskycounts
    ratio_quantiles = np.quantile(ratio,[0.16,0.84])
    ratio_rms_robust = (ratio_quantiles[1]-ratio_quantiles[0])/2.0
    
    moon_el = moon_elevation(header)
    sun_el, phase = sun_elevation(header)
    galactic = galactic_coord(header)
    
    # skipping snr calculations

    # TODO: move imports to top of file once final
    from bokeh.plotting import figure#, show
    from bokeh.models import ColorBar, LinearColorMapper, BasicTicker, NumeralTickFormatter
    from bokeh.models import ColumnDataSource, CDSView, BooleanFilter
    from bokeh.palettes import Viridis256
    from bokeh.transform import linear_cmap

    source = bk.ColumnDataSource(data=dict(
        ratio=ratio,
        GOODFIBER_X=coords["FIBER_X"][sel],
        GOODFIBER_Y=coords["FIBER_Y"][sel],
        FIBERFLUX_R=flux,
        MEDIAN_CALIB_FLUX=counts,
     ))

    fig = bk.figure(title="Fractional residuals of standard star R counts vs flux", plot_height=plot_height-50, plot_width=plot_width+25)#, toolbar_location=None)
    fig.scatter(coords["FIBER_X"],coords["FIBER_Y"],size=0.5, color='gray')
    mapper = linear_cmap('ratio', palette="Viridis256", low=0.5, high=1.5, nan_color='gray')
    fig.scatter('GOODFIBER_X', 'GOODFIBER_Y', source=source, size=5, color=mapper)
    color_bar = ColorBar(color_mapper=mapper['transform'], label_standoff=12, ticker=BasicTicker(), width=10, formatter=NumeralTickFormatter(format='0.0a'))
    fig.add_layout(color_bar, 'right')

    fig2 = bk.figure(title="Median Calibrated Flux vs Fiberflux for Standard Stars", x_axis_label='FIBERFLUX_R', y_axis_label='MEDIAN_CALIB_FLUX(R)', plot_height=plot_height-50, plot_width=plot_width)#, toolbar_location=None)
    fig2.scatter(flux, counts, size=4)

    moontext = ("Moon is " + f'{phase*100:4.1f}' + "% full, " + f'{header["MOONSEP"]:5.1f}' + " deg away, " + f'{moon_el:5.1f}' + " deg above the horizon") if moon_el>-6 else ("Moon is set")
    summarytext = \
    "Tile " + f'{header["TILEID"]:05d}' + " at RA,Dec " + f'{header["SKYRA"]:5.1f}' + " " + f'{header["SKYDEC"]:+4.1f}' + " and Galactic l,b " + f'{galactic.l.degree:3.1f}' + " " + f'{galactic.b.degree:+2.1f}' + "\n" \
    + "Airmass " + f'{header["AIRMASS"]:4.2f}' + ", Hour Angle " + f'{header["MOUNTHA"]:+2.0f}' + " deg at UTC " + str(header["DATE-OBS"][11:19]) + "\n" \
    + moontext + "\n" \
    + "r=20 stars yielding " + f'{rstarcountrate:5.1f}' + " counts/ks in R with " + f'{ratio_rms_robust:5.3f}' + " fractional residual" + "\n" \
    + "Sky yielding " + f'{rskycounts:5.1f}' + " counts/ks in R"


    return fig, fig2, summarytext
