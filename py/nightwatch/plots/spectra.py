import fitsio

import bokeh
import bokeh.plotting as bk
from bokeh.layouts import column, gridplot
from bokeh.models import BoxAnnotation, ColumnDataSource, Range1d, Band, Title, HoverTool, NumeralTickFormatter, OpenURL, TapTool, HelpTool
from glob import glob

import numpy as np
import numpy.lib.recfunctions as rfn
import random, os, sys, re

from desitarget.targets import desi_mask

from .. import io

from packaging import version
_is_bokeh23 = version.parse(bokeh.__version__) >= version.parse('2.3.0')


def downsample(data, n, agg=np.mean):
    '''
    Produces downsampled data of data

    Args:
        data: an array or list of elements able to be aggregated by agg
        n: int of downsample size

    Options:
        agg: aggregate function; default is np.mean

    Returns a list of the downsampled data
    '''
    length = len(data)
    resultx = [agg(data[j:(j+n)]) if (j+n <= length) else agg(data[j:length]) for j in range(0, length, n)]
    return resultx


def get_spectrum_objname(objtype, desi_target):
    '''
    Convert object type and bit masks from fibermap into a user-friendly string.

    Args:
        objtype: str or list or ndarray containing "TGT," "SKY", or ""
        desi_target: DESI target bitmask(s).

    Returns: str or nd.array with object types and target info.
    '''
    # Cleanup OBJTYPE and DESITARGET into a single string.
    # - if OBJTYPE is TGT, return the first name of DESI_TARGET from desi_mask.
    # - else if OBJTYPE is not empty, return OBJTYPE.
    # - else return the string 'None'
    get_names = lambda ot, dt: 'None' if not ot else (f'{desi_mask.names(dt)[0]}' if 'TGT' in ot and dt>0 else ot)

    # Extract object type (TGT or SKY) and bitmask info.
    if isinstance(desi_target, (list, np.ndarray)):
        objnames = [get_names(ot, dt) for ot, dt in zip(objtype, desi_target)]
        return np.asarray(objnames)
    else:
        objname = get_names(objtype, desi_target)
        return objname


def plot_spectra_spectro(data, expid_num, frame, n, num_fibs=3, height=220, width=240):
    '''
    Produces a gridplot of 10 different spectra plots, each displaying a number of randomly
    selected fibers that correspond to the 10 different spectrographs.

    Args:
        data: night directory that contains the expid we want to process spectra for
        expid_num: string or int of the expid we want to process spectra for
        frame: filename header to look for ("qframe" or "qcframe")
        n: int of downsample size

    Options:
        num_fibs: number of fibers per spectrograph spectra plot
        height: height of each plot
        width: height of each plot

    Returns bokeh.layouts.gridplot object containing all 10 plots
    '''
    p1 = []
    p2 = []
    first = None
    expid = str(expid_num).zfill(8)
    spectrorange = range(0, 10, 1)
    for spectro in spectrorange:
        colors = {}
        fib = []

        # Read fibers from the B cameras.
        qframe_b = os.path.join(data, expid, f'{frame}-b{spectro}-{expid}.fits')
        try:
            fib += [list(fitsio.read(qframe_b, columns=['FIBER'], ext='FIBERMAP')['FIBER'])]
            colors['B'] = 'steelblue'
        except:
            print(f'could not find {qframe_b}', file=sys.stderr)

        # Read fibers from the R cameras.
        qframe_r = os.path.join(data, expid, f'{frame}-r{spectro}-{expid}.fits')
        try:
            fib += [list(fitsio.read(qframe_r, columns=['FIBER'], ext='FIBERMAP')['FIBER'])]
            colors['R'] = 'crimson'
        except:
            print(f'could not find {qframe_r}', file=sys.stderr)

        # Read fibers from the Z cameras.
        qframe_z = os.path.join(data, expid, f'{frame}-z{spectro}-{expid}.fits')
        try:
            fib += [list(fitsio.read(qframe_z, columns=['FIBER'], ext='FIBERMAP')['FIBER'])]
            colors['Z'] = 'forestgreen'
        except:
            print(f'could not find {qframe_z}', file=sys.stderr)

        if (len(colors) == 0 and spectro == np.max(spectrorange) and first is None):
            print("no supported {}-*.fits files".format(frame))
            return None

        common = []
        for fiber in fib:
            if common == []:
                common = fiber
            else:
                common = list(set(common).intersection(fiber))
        if len(common) > num_fibs:
            common = random.sample(common, k=num_fibs)
        if len(fib) > 0:
            indexes = [fib[0].index(i) for i in common]
        else:
            indexes = []
        fig=bk.figure(plot_height = height, plot_width = width+50)
        # fig.add_layout(Title(text= "Downsample: {}".format(n), text_font_style="italic"), 'above')
        # fig.add_layout(Title(text= "Fibers: {}".format(common), text_font_style="italic"), 'above')
        # fig.add_layout(Title(text="Spectro: {}".format(spectro), text_font_size="12pt"), 'above')
        title = 'sp{} fibers {}'.format(spectro, ', '.join(map(str, common)))
        fig.add_layout(Title(text=title, text_font_style='italic'), 'above')

        # Add tool tips to the figure during mouseover.
        tooltips = tooltips=[
            ('Fiber', '@fiber'),
            ('Cam', '@cam'),
            ('Objtype', '@objtype'),
            ('Wavelength', '@wave'),
            ('Flux', '@flux')
        ]

        hover = HoverTool(
            tooltips=tooltips
        )
        fig.add_tools(hover)

        if spectro not in [0, 5]:
            fig.yaxis.visible = False
            fig.plot_width = width

        flux_total = []
        for cam in colors:
            camfile = os.path.join(data, expid, f'{frame}-{cam.lower()}{spectro}-{expid}.fits')
            wavelength = fitsio.read(camfile, ext='WAVELENGTH')
            flux = fitsio.read(camfile, ext='FLUX')
            fmap = fitsio.read(camfile, columns=['OBJTYPE','DESI_TARGET','TARGET_RA','TARGET_DEC'], ext='FIBERMAP')

            for i in indexes:
                dwavelength = downsample(wavelength[i], n)
                dflux = downsample(flux[i], n)
                if first is None:
                    flux_total += dflux
                length = len(dwavelength)

                # Object type and position for the Legacy Survey picker.
                objtype = get_spectrum_objname(fmap['OBJTYPE'][i], fmap['DESI_TARGET'][i])
                ra  = fmap['TARGET_RA'][i]
                dec = fmap['TARGET_DEC'][i]

                source = ColumnDataSource(data=dict(
                            fiber = [fib[0][i]]*length,
                            cam = [cam]*length,
                            objtype = [objtype]*length,
                            ra = [ra]*length,
                            dec = [dec]*length,
                            wave = dwavelength,
                            flux = dflux,
                        ))
                fig.line('wave', 'flux', source=source, alpha=0.5, color=colors[cam])

#        # Open link to Legacy Survey when the user left-clicks the spectrum.
#        # NOT WORKING: see https://github.com/desihub/nightwatch/issues/321
#        url = "https://www.legacysurvey.org/viewer-desi?ra=@ra&dec=@dec&layer=ls-dr9&zoom=15&mark=@ra,@dec"
#        taptool = fig.select(type=TapTool)
#        taptool.callback = OpenURL(url=url)

        if first is None:
            if len(colors) == 3:
                if len(flux_total) == 0:
                    upper = 1
                else:
                    upper = int(np.percentile(flux_total, 99.99))
                fig.y_range = Range1d(int(-0.02*upper), upper)
                first = fig

        if (spectro<5):
            p1 += [fig]
        else:
            p2 += [fig]

    #print(flux_total, file=sys.stderr)
    for fig in p1:
        fig.x_range=first.x_range
        fig.y_range=first.y_range

    for fig in p2:
        fig.x_range=first.x_range
        fig.y_range=first.y_range

    grid = gridplot([p1, p2], sizing_mode='fixed')
    return grid


def plot_spectra_objtype(data, expid_num, frame, n, num_fibs=5, height=500, width=1000):
    '''
    Produces a gridplot of different spectra plots, each displaying a number of randomly selected fibers that correspond to each unique OBJTYPE.

    Args:
        data: night directory that contains the expid we want to process.
        expid_num: string or int of the expid we want to process spectra.
        frame: filename header to look for ("qframe" or "qcframe")
        n: int of downsample size

    Options:
        num_fibs: number of fibers per objtype spectra plot
        height: height of each plot
        width: height of each plot

    Returns bokeh.layouts.gridplot object containing the objtype plots
    '''
    colors = { 'B':'steelblue', 'R':'crimson', 'Z':'forestgreen' }
    expid = str(expid_num).zfill(8)

    # Find a list of files corresponding to the desired frame.
    qframes = sorted(glob(os.path.join(data, expid, f'{frame}*.fits')))
    if len(qframes) == 0:
        print(f'no supported {frame}-*.fits files')
        return None

    # Get target information for all fibers in this exposure.
    # - Extract TARGETID, OBJTYPE, DESI_TARGET, and PETAL_LOC.
    # - Produce a unique table, then convert DESI_TARGET to object type.
    fibtab = None
    keys = ['TARGETID', 'PETAL_LOC', 'FIBER', 'OBJTYPE', 'DESI_TARGET']

    for qframe in qframes:
        fmap = fitsio.read(qframe, columns=keys, ext='FIBERMAP')
        if fibtab is None:
            fibtab = fmap[fmap['TARGETID'] >= 0]
        else:
            fibtab = np.concatenate([fibtab, fmap[fmap['TARGETID'] >= 0]])

    fibtab = np.unique(fibtab)
    fibtab = rfn.append_fields(fibtab, 'OBJNAME', get_spectrum_objname(fibtab['OBJTYPE'], fibtab['DESI_TARGET']))
    keys += 'OBJNAME'

    # Loop through the list of unique object types in this exposure.
    unique_nms = np.unique(fibtab['OBJNAME'])
    gridlist = []

    for nm in unique_nms:
        fig = bk.figure(plot_height=height, plot_width=width)
        fig.yaxis.axis_label = 'counts'
        fig.xaxis.axis_label = 'wavelength [angstroms]'
        fig.x_range = Range1d(3500, 9950)
        fig.add_layout(BoxAnnotation(left=5660, right=5930, fill_color='blue', fill_alpha=0.03, line_alpha=0))
        fig.add_layout(BoxAnnotation(left=7470, right=7720, fill_color='blue', fill_alpha=0.03, line_alpha=0))

        select = fibtab['OBJNAME'] == nm
        nfibs = np.minimum(np.sum(select), num_fibs)
        minflux, maxflux = 1e99, -1e99

        # Randomly select nfibs fibers of this object type.
        fibers = np.random.choice(fibtab['FIBER'][select], size=nfibs, replace=False)
        idx = np.isin(fibtab['FIBER'], fibers)

        for i, (tid, petal, fiber, otype, desitgt, oname) in enumerate(fibtab[idx]):
            for cam in colors:
                camfile = os.path.join(data, expid, f'{frame}-{cam.lower()}{petal}-{expid}.fits')
                if os.path.exists(camfile):

                    # Convert TARGETID to table index in file.
                    fits = fitsio.FITS(camfile)
                    fits_fibers = fits['FIBERMAP']['FIBER'][:]
                    j = np.argwhere(fits_fibers == fiber)
                    if j.shape != (1,1):
                        continue
                    j = j.item()

                    # Extract target information for this fiber.
                    ra, dec = fits['FIBERMAP']['TARGET_RA', 'TARGET_DEC'][j]

                    # Extract wavelength and flux for this fiber.
                    wavelength = fits['WAVELENGTH'][j,:].flatten()
                    flux = fits['FLUX'][j,:].flatten()

                    # Downsample the fluxes.
                    dwavelength = downsample(wavelength, n)
                    dflux = downsample(flux, n)
                    minflux = np.minimum(minflux, np.percentile(dflux, 1))
                    maxflux = np.maximum(maxflux, np.percentile(dflux, 99))
                    length = len(dwavelength)

                    # Create bokeh plotting objects.
                    source = ColumnDataSource(data=dict(
                                fiber = [fiber]*length,
                                cam = [f'{cam}{petal}']*length,
                                objtype = [nm]*length,
                                ra = [ra]*length,
                                dec = [dec]*length,
                                wave = dwavelength,
                                flux = dflux
                            ))
                    fig.line('wave', 'flux', source=source, alpha=0.5, color=colors[cam])

        # Configure plot for spectra of this object type.
        fig.add_layout(Title(text= f'Downsample: {n}', text_font_style='italic'), 'above')
        fig.add_layout(Title(text= f'Fibers: {fibers}', text_font_style='italic'), 'above')
        fig.add_layout(Title(text= f'OBJTYPE: {nm}', text_font_size='16pt'), 'above')

#        # Open link to Legacy Survey when the user left-clicks the spectrum.
#        # NOT WORKING: see https://github.com/desihub/nightwatch/issues/321
#        url = "https://www.legacysurvey.org/viewer-desi?ra=@ra&dec=@dec&layer=ls-dr9&zoom=15&mark=@ra,@dec"
#        taptool = fig.select(type=TapTool)
#        taptool.callback = OpenURL(url=url)

        # Add over tool with spectrum info.
        tooltips = tooltips=[
            ('Fiber', '@fiber'),
            ('Cam', '@cam'),
            ('Objtype', '@objtype'),
            ('Wavelength', '@wave'),
            ('Flux', '@flux')
        ]

        hover = HoverTool(
            tooltips=tooltips
        )

        fig.add_tools(hover)

        maxflux = 1.05*maxflux
        minflux = 1.05*minflux if minflux < 0 else 0.9*minflux
        fig.y_range = Range1d(int(minflux), int(maxflux))

        gridlist += [[fig]]

    return gridplot(gridlist, sizing_mode='fixed')


def lister(string):
    '''
    Produces a list of fibers from translating the string input

    Args:
        string that requests specific fibers (eg "1, 3-5, 501")

    Returns a list of ints corresponding to the fibers specified (eg [1, 3, 5, 501])
    '''
    try:
        str_spl = string.split(',')
        result = []
        for sub in str_spl:
            if '-' in sub:
                between = sub.split('-')
                if len(between) != 2:
                    return None
                lower = int(between[0])
                upper = int(between[1])+1
                result += range(lower, upper, 1)
            else:
                result += [int(sub)]
        return np.array(result)
    except:
        return None


def plot_spectra_input(datadir, expid_num, frame, n, select_string, height=500, width=1000):
    '''
    Produces plot displaying the specific fibers requested.

    Args:
        datadir: night directory that contains the expid we want to process
        expid_num: string or int of the expid we want to process spectra for
        frame: filename header to look for ("qframe" or "qcframe")
        n: int of downsample size
        select_string: string that requests specific fibers ("1, 3-5" corresponds to fibers 1, 3, 5)

    Options:
        height: height of the plot
        width: height of the plot

    Returns bokeh.plotting.figure containing all existing specified fibers
    '''
    fibers = lister(select_string)
    if fibers is None:
        return None

    result_able = []
    result_not = [fiber for fiber in fibers if fiber >=5000]
    flux_total = []

    expid = str(expid_num).zfill(8)
    colors = { 'B':'steelblue', 'R':'crimson', 'Z':'forestgreen' }

    expdir = os.path.join(datadir, expid)
    fibergroups, missingfibers = io.findfibers(expdir, fibers)
    if len(missingfibers) < len(fibers):
        foundfibers = np.concatenate(list(fibergroups.values()))
    else:
        foundfibers = []

    fig = bk.figure(plot_height=height, plot_width=width,
                    tools=['tap', 'reset', 'box_zoom', 'pan'])
    fig.xaxis.axis_label = 'wavelength [angstroms]'
    fig.x_range = Range1d(3200, 10200)
    fig.yaxis.axis_label = 'counts'
    fig.add_layout(BoxAnnotation(left=5660, right=5930, fill_color='blue', fill_alpha=0.03, line_alpha=0))
    fig.add_layout(BoxAnnotation(left=7470, right=7720, fill_color='blue', fill_alpha=0.03, line_alpha=0))

    for spectro in fibergroups.keys():
        for cam in colors:
            framefile = os.path.join(datadir, expid,
                    '{}-{}{}-{}.fits'.format(frame, cam.lower(), spectro, expid))
            if not os.path.isfile(framefile):
                print(f"WARNING: missing {framefile}")
                continue

            fibermap = fitsio.read(framefile, ext='FIBERMAP')

            wavelength = fitsio.read(framefile, ext='WAVELENGTH')
            flux = fitsio.read(framefile, ext='FLUX')
            spectrofibers = fibergroups[spectro]
            indexes = np.where(np.in1d(fibermap['FIBER'], spectrofibers))[0]
            assert len(spectrofibers) == len(indexes)

            for i, ifiber in zip(indexes, spectrofibers):
                # Extract flux and wavelength.
                dwavelength = downsample(wavelength[i], n)
                dflux = downsample(flux[i], n)
                length = len(dwavelength)

                # Extract object type (TGT or SKY) and bitmask info.
                objtype = fibermap['OBJTYPE'][i]
                desitgt = fibermap['DESI_TARGET'][i]
                objtype = get_spectrum_objname(objtype, desitgt)

                # Get sky coordinates of the spectrum.
                ra  = fibermap['TARGET_RA'][i]
                dec = fibermap['TARGET_DEC'][i]

                # Create a column data source used for mouseover info.
                source = ColumnDataSource(data=dict(
                            fiber = [ifiber]*length,
                            cam = [f'{cam}{spectro}']*length,
                            objtype = [objtype]*length,
                            ra = [ra]*length,
                            dec = [dec]*length,
                            wave = dwavelength,
                            flux = dflux
                        ))
                flux_total += dflux
                fig.line("wave", "flux", source=source, alpha=0.5, color=colors[cam])

    # Open a link to the Legacy Survey when the user taps the spectrum.
    url = "https://www.legacysurvey.org/viewer-desi?ra=@ra&dec=@dec&layer=ls-dr9&zoom=15&mark=@ra,@dec"
    taptool = fig.select(type=TapTool)
    taptool.callback = OpenURL(url=url)

    # fig.add_layout(Title(text= "Downsample: {}".format(n), text_font_style="italic"), 'above')
    if len(missingfibers) > 0:
        fig.add_layout(Title(text= "Not Found: {}".format(missingfibers),
            text_font_style="italic"), 'above')

    fig.add_layout(Title(text= "Fibers: {}".format(', '.join(map(str, foundfibers))),
        text_font_size="12pt"), 'above')

    if len(foundfibers) == 0:
        print('ERROR: Unable to find any input spectra in {} for {}'.format(
            datadir, select_string))

    # Add tooltips that allow users to view spectrum information on hover.
    tooltips = tooltips=[
        ("Fiber", "@fiber"),
        ("Cam", "@cam"),
        ("Objtype", "@objtype"),
        ("Wavelength", "@wave"),
        ("Flux", "@flux")
    ]

    hover = HoverTool(
        tooltips=tooltips
    )
    fig.add_tools(hover)

    # Use the help tool to redirect users to the DESI Nightwatch QA wiki Q&A
    if _is_bokeh23:
        fig.add_tools(HelpTool(description='See the DESI wiki for details\non spectra QA',
                                redirect='https://desi.lbl.gov/trac/wiki/DESIOperations/NightWatch/NightWatchDescription#Spectra'))

    else:
        fig.add_tools(HelpTool(help_tooltip='See the DESI wiki for details\non spectra QA',
                                redirect='https://desi.lbl.gov/trac/wiki/DESIOperations/NightWatch/NightWatchDescription#Spectra'))

    # Set axis range.
    if len(flux_total) == 0:
        upper = 1
    else:
        upper = int(np.percentile(flux_total, 99.99))
    fig.y_range = Range1d(int(-0.02*upper), upper)
    fig.yaxis.formatter = NumeralTickFormatter(format='0a')

    return fig


def plot_spectra_qa(data, names, calstandards):
    spectro = data['SPECTRO']
    colors = { 'B':'steelblue', 'R':'firebrick', 'Z':'green' }

    calwaves = calstandards['wavelength']

    figs = []
    for name in names:
        cam = name[0]
        wave = int(name[1:])

        linearea = data[name]
        select = linearea > 0

        # Get the calibration standards from input.
        # Convert data stored vs. spectrograph to a plot 
        camwaves = np.asarray(calwaves[cam])
        iwave = np.argmin(np.abs(camwaves - wave))

        upper_err, upper_warn, nominal, lower_warn, lower_err = [], [], [], [], []
        for sp in spectro:
            cals = calstandards['area']['spectrograph'][f'{sp}'][cam]
            upper_err.append(cals['upper_err'][iwave])
            upper_warn.append(cals['upper'][iwave])
            nominal.append(cals['nominal'][iwave])
            lower_warn.append(cals['lower'][iwave])
            lower_err.append(cals['lower_err'][iwave])

#        cals = calstandards['area']['spectrograph']#[f'{spectro}'][cam]
#        for sp in spectro:
#            print('SPECTRO: ', sp)
#        upper_err = cals['upper_err']
#        upper_warn = cals['upper']
#        nominal = cals['nominal']
#        lower_warn = cals['lower']
#        lower_err = cals['lower_err']

        mcolors = ['black']*len(nominal)
        msizes = [5]*len(nominal)

        source = ColumnDataSource(data=dict(
            data_val=linearea[select],
            locations=spectro[select],
            lower=lower_warn,
            upper=upper_warn,
            colors=mcolors,
            sizes=msizes
        ))

        # Set up figures and labels.
        plotmin = 0.9*np.min(np.minimum(lower_err, linearea[select]))
        plotmax = 1.1*np.max(np.maximum(upper_err, linearea[select]))

        fig = bk.figure(x_range=Range1d(start=-0.1, end=9.1),
                        y_range=Range1d(start=plotmin, end=plotmax),
                        plot_height=200, plot_width=1000)

        fig.xaxis.ticker = [0,1,2,3,4,5,6,7,8,9]
        fig.xaxis.axis_label = 'spectrograph'
        fig.yaxis.minor_tick_line_color = None
        fig.ygrid.grid_line_color = None
        fig.yaxis.axis_label = 'line area'

        # Plot the line areas for all spectrographs.
        fig.circle(x='locations', y='data_val', 
                   fill_color='colors', size='sizes', line_color=None,
                   source=source, name='circles')
        fig.title.text = f'{cam} camera: λ{name[1:]}'
        fig.title.text_color = colors[cam]

        # Add a visual indication of the typical range of variations.
        fig.add_layout(
            Band(base='locations', lower='lower', upper='upper',
                 source=source, level='underlay',
                 fill_alpha=0.1, fill_color=colors[cam],
                 line_width=0.7, line_color='black'))

        figs.append([fig])

    return gridplot(figs, toolbar_location='right')
