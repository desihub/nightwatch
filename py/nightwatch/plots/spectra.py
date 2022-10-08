from astropy.io import fits
import bokeh.plotting as bk
from bokeh.layouts import gridplot
from bokeh.models import ColumnDataSource, Range1d, Title, HoverTool, NumeralTickFormatter

import numpy as np
import random, os, sys, re

from .. import io

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
#     for j in range(0, length, n):
#         if (j+n <= length):
#             samplex = data[j:(j+n)]
#             resultx += [agg(samplex)]
#         else:
#             samplex = data[j:length]
#             resultx += [agg(samplex)]
    return resultx

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
        try:
            fib += [list(fits.getdata(os.path.join(data, expid, '{}-b{}-{}.fits'.format(frame, spectro, expid)), 5)["FIBER"])]
            colors["B"] = "steelblue"
        except:
            print("could not find {}".format(os.path.join(data, expid, '{}-b{}-{}.fits'.format(frame, spectro, expid))), file=sys.stderr)

        try:
            fib += [list(fits.getdata(os.path.join(data, expid, '{}-r{}-{}.fits'.format(frame, spectro, expid)), 5)["FIBER"])]
            colors["R"] = "red"
        except:
            print("could not find {}".format(os.path.join(data, expid, '{}-r{}-{}.fits'.format(frame, spectro, expid))), file=sys.stderr)

        try:
            fib += [list(fits.getdata(os.path.join(data, expid, '{}-z{}-{}.fits'.format(frame, spectro, expid)), 5)["FIBER"])]
            colors["Z"] = "sienna"
        except:
            print("could not find {}".format(os.path.join(data, expid, '{}-b{}-{}.fits'.format(frame, spectro, expid))), file=sys.stderr)

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
        title = "sp{} fibers {}".format(spectro, ", ".join(map(str, common)))
        fig.add_layout(Title(text=title, text_font_style="italic"), 'above')
        tooltips = tooltips=[
            ("Fiber", "@fiber"),
            ("Cam", "@cam"),
            ("Wavelength", "@wave"),
            ("Flux", "@flux")
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
            wavelength = fits.getdata(os.path.join(data, expid, '{}-{}{}-{}.fits'.format(frame, cam.lower(), spectro, expid)), "WAVELENGTH")
            flux = fits.getdata(os.path.join(data, expid, '{}-{}{}-{}.fits'.format(frame, cam.lower(), spectro, expid)), "FLUX")
            for i in indexes:
                dwavelength = downsample(wavelength[i], n)
                dflux = downsample(flux[i], n)
                if first is None:
                    flux_total += dflux
                length = len(dwavelength)
                source = ColumnDataSource(data=dict(
                            fiber = [fib[0][i]]*length,
                            cam = [cam]*length,
                            wave = dwavelength,
                            flux = dflux,
                        ))
                fig.line("wave", "flux", source=source, alpha=0.5, color=colors[cam])

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

    grid = gridplot([p1, p2], sizing_mode="fixed")
    return grid

def plot_spectra_objtype(data, expid_num, frame, n, num_fibs=5, height=500, width=1000):
    '''
    Produces a gridplot of different spectra plots, each displaying a number of randomly
    selected fibers that correspond to each unique OBJTYPE.

    Args:
        data: night directory that contains the expid we want to process spectra for
        expid_num: string or int of the expid we want to process spectra for
        frame: filename header to look for ("qframe" or "qcframe")
        n: int of downsample size

    Options:
        num_fibs: number of fibers per objtype spectra plot
        height: height of each plot
        width: height of each plot

    Returns bokeh.layouts.gridplot object containing the objtype plots
    '''
    colors = { 'B':'steelblue', 'R':'red', 'Z':'sienna' }
    expid = str(expid_num).zfill(8)

    onlyfiles = [f for f in os.listdir(os.path.join(data, expid)) if os.path.isfile(os.path.join(data, expid, f))]
    qframes = [i for i in onlyfiles if re.match(r'{}.*'.format(frame), i)]
    if len(qframes) == 0:
        print("no supported {}-*.fits files".format(frame))
        return None
    spectr = [int(i.split("-")[1][1]) for i in qframes]
    spectros = random.choices(list(set(spectr)), k=num_fibs)

    gridlist = []
    unique_objs = list(set(fits.getdata(os.path.join(data, expid, qframes[0]), 5)["OBJTYPE"]))
    unique_objs.sort()
    for obj in unique_objs:
        fig=bk.figure(plot_height = height, plot_width = width)
        com = []
        first = True
        for spectro in spectros:
            r_fib = fits.getdata(os.path.join(data, expid, '{}-r{}-{}.fits'.format(frame, spectro, expid)), 5)
            bool_array = r_fib["OBJTYPE"] == obj
            r_fib = r_fib["FIBER"]
            r_fib = [r_fib[i] if bool_array[i] else None for i in range(len(r_fib))]

            b_fib = fits.getdata(os.path.join(data, expid, '{}-b{}-{}.fits'.format(frame, spectro, expid)), 5)
            b_fib = b_fib[b_fib["OBJTYPE"] == obj]["FIBER"]

            z_fib = fits.getdata(os.path.join(data, expid, '{}-z{}-{}.fits'.format(frame, spectro, expid)), 5)
            z_fib = z_fib[z_fib["OBJTYPE"] == obj]["FIBER"]

            common = list(set(r_fib).intersection(b_fib).intersection(z_fib))
            if len(common) > 1:
                common = random.sample(common, k=1)
            com += common
            indexes = [r_fib.index(i) for i in common]
            if first:
                flux_total = []
            for cam in colors:
                if indexes == []:
                    continue
                wavelength = fits.getdata(os.path.join(data, expid, '{}-{}{}-{}.fits'.format(frame, cam.lower(), spectro, expid)), "WAVELENGTH")
                flux = fits.getdata(os.path.join(data, expid, '{}-{}{}-{}.fits'.format(frame, cam.lower(), spectro, expid)), "FLUX")
                for i in indexes:
                    dwavelength = downsample(wavelength[i], n)
                    dflux = downsample(flux[i], n)
                    if first:
                        flux_total += dflux
                    length = len(dwavelength)
                    source = ColumnDataSource(data=dict(
                                fiber = [r_fib[i]]*length,
                                cam = [cam]*length,
                                wave = dwavelength,
                                flux = dflux
                            ))
                    fig.line("wave", "flux", source=source, alpha=0.5, color=colors[cam])
            first = False

        #grid = gridplot(p1, p2)
        fig.add_layout(Title(text= "Downsample: {}".format(n), text_font_style="italic"), 'above')
        fig.add_layout(Title(text= "Fibers: {}".format(com), text_font_style="italic"), 'above')
        fig.add_layout(Title(text= "OBJTYPE: {}".format(obj), text_font_size="16pt"), 'above')

        tooltips = tooltips=[
            ("Fiber", "@fiber"),
            ("Cam", "@cam"),
            ("Wavelength", "@wave"),
            ("Flux", "@flux")
        ]

        hover = HoverTool(
            tooltips=tooltips
        )

        fig.add_tools(hover)

        upper = int(np.percentile(flux_total, 99.99))
        fig.y_range = Range1d(int(-0.02*upper), upper)
        gridlist += [[fig]]
    return gridplot(gridlist, sizing_mode="fixed")

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
        datadir: night directory that contains the expid we want to process spectra for
        expid_num: string or int of the expid we want to process spectra for
        frame: filename header to look for ("qframe" or "qcframe")
        n: int of downsample size
        select_string: string that requests specific fibers ("1, 3-5" corresponds
            to fibers 1, 3, 5)

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
    colors = { 'B':'steelblue', 'R':'red', 'Z':'sienna' }

    expdir = os.path.join(datadir, expid)
    fibergroups, missingfibers = io.findfibers(expdir, fibers)
    if len(missingfibers) < len(fibers):
        foundfibers = np.concatenate(list(fibergroups.values()))
    else:
        foundfibers = []

    fig=bk.figure(plot_height = height, plot_width = width)

    for spectro in fibergroups.keys():
        for cam in colors:
            framefile = os.path.join(datadir, expid,
                    '{}-{}{}-{}.fits'.format(frame, cam.lower(), spectro, expid))
            if not os.path.isfile(framefile):
                print(f"WARNING: missing {framefile}")
                continue

            fibermap = fits.getdata(framefile, 'FIBERMAP')

            wavelength = fits.getdata(framefile, "WAVELENGTH")
            flux = fits.getdata(framefile, "FLUX")
            spectrofibers = fibergroups[spectro]
            indexes = np.where(np.in1d(fibermap['FIBER'], spectrofibers))[0]
            assert len(spectrofibers) == len(indexes)

            for i, ifiber in zip(indexes, spectrofibers):
                dwavelength = downsample(wavelength[i], n)
                dflux = downsample(flux[i], n)
                length = len(dwavelength)
                source = ColumnDataSource(data=dict(
                            fiber = [ifiber]*length,
                            cam = [cam]*length,
                            wave = dwavelength,
                            flux = dflux
                        ))
                flux_total += dflux
                #print(str(i), file=sys.stderr)
                fig.line("wave", "flux", source=source, alpha=0.5, color=colors[cam])

    # fig.add_layout(Title(text= "Downsample: {}".format(n), text_font_style="italic"), 'above')
    if len(missingfibers) > 0:
        fig.add_layout(Title(text= "Not Found: {}".format(missingfibers),
            text_font_style="italic"), 'above')

    fig.add_layout(Title(text= "Fibers: {}".format(', '.join(map(str, foundfibers))),
        text_font_size="12pt"), 'above')

    if len(foundfibers) == 0:
        print('ERROR: Unable to find any input spectra in {} for {}'.format(
            datadir, select_string))

    tooltips = tooltips=[
        ("Fiber", "@fiber"),
        ("Wavelength", "@wave"),
        ("Flux", "@flux")
    ]

    hover = HoverTool(
        tooltips=tooltips
    )

    fig.add_tools(hover)

    if len(flux_total) == 0:
        upper = 1
    else:
        upper = int(np.percentile(flux_total, 99.99))
    fig.y_range = Range1d(int(-0.02*upper), upper)
    fig.yaxis.formatter = NumeralTickFormatter(format='0a')

    return fig
