import os, sys, re, json
import argparse, jinja2
import bokeh
from bokeh.embed import components
from flask import (Flask, send_from_directory, redirect)

parser = argparse.ArgumentParser(usage = "app.py [options]")
parser.add_argument("-i", "--indir", type=str, required=True, help="input directory with pre-generated nightwatch webpages")
parser.add_argument("-d", "--datadir", type=str, help="directory with qproc output data files (if different than --indir)")
parser.add_argument("--host", type=str, default="0.0.0.0", help="hostname (e.g. localhost or 0.0.0.0")
parser.add_argument("--port", type=int, default=8001, help="port number")
parser.add_argument("--debug", action="store_true", help="enable Flask debug mode")

args = parser.parse_args()

if args.datadir is None and args.indir is not None:
    args.datadir = args.indir

indir = os.path.abspath(args.indir)
datadir = os.path.abspath(args.datadir)

app = Flask('nightwatch', static_folder=indir)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

@app.route('/')
def redict_to_cal():
    global indir
    print('redirecting to nights.html')
    return redirect('nights.html', code=302)

@app.route('/timeseries/')
def test_input():
    global indir
    env = jinja2.Environment(
        loader=jinja2.PackageLoader('nightwatch.webpages', 'templates')
    )
    filename = os.path.join(indir, "static", "timeseries_dropdown.json")

    with open(filename, 'r') as myfile:
        json_data=myfile.read()

    dropdown = json.loads(json_data)

    template = env.get_template('timeseries_input.html')
    return template.render(dropdown_hdu=dropdown)

@app.route('/timeseries/<int:start_date>/<int:end_date>/<string:hdu>/<string:attribute>')
def test_timeseries(start_date, end_date, hdu, attribute):
    global datadir

    verify = [
    not re.match(r"20[0-9]{6}", str(start_date)),
    not re.match(r"20[0-9]{6}", str(end_date)),
    re.match(r"\.\.", hdu) or hdu=="",
    re.match(r"\.\.", attribute) or attribute==""
    ]

    error_string = [
    "start date, ",
    "end date, ",
    "attribute"
    ]

    filename = os.path.join(indir, "static", "timeseries_dropdown.json")

    with open(filename, 'r') as myfile:
        json_data=myfile.read()

    dropdown = json.loads(json_data)

    if any(verify):
        error_message = "Invalid "
        for i in range(len(verify)):
            if verify[i]:
                error_message += error_string[i]
        return error_message
    #html_attr["dropdown_hdu"] = dropdown

    from nightwatch.webpages.timeseries import generate_timeseries_html

    html = generate_timeseries_html(datadir, start_date, end_date, hdu, attribute, dropdown)

    return html

@app.route('/<int:night>/<string:expid>/spectra/')
def redirect_to_spectrograph_spectra(night, expid):
    print('redirecting to spectrograph spectra')
    return redirect('/{}/{}/spectra/spectrograph/qframe/4x/'.format(night, '{:08d}'.format(expid)), code=302)

@app.route('/<int:night>/<int:expid>/spectra/input/', defaults={'frame': None, 'select_string': None, 'downsample': None})
@app.route('/<int:night>/<int:expid>/spectra/input/<string:select_string>/<string:frame>/<string:downsample>/')
def getspectrainput(night, expid, select_string, frame, downsample):
    global datadir
    from nightwatch.webpages import spectra
    return spectra.get_spectra_html(os.path.join(datadir, str(night)), night, expid, "input", frame, downsample, select_string)

@app.route('/<int:night>/<int:expid>/spectra/<string:view>/', defaults={'frame': None, 'downsample': None})
@app.route('/<int:night>/<int:expid>/spectra/<string:view>/<string:frame>/', defaults={'downsample': None})
@app.route('/<int:night>/<int:expid>/spectra/<string:view>/<string:frame>/<string:downsample>/')
def getspectra(night, expid, view, frame, downsample):
    global datadir

    if downsample is None:
        if frame is None:
            return redirect('/{}/{}/spectra/{}/qframe/4x/'.format(night, '{:08d}'.format(expid), view), code=302)
        return redirect('/{}/{}/spectra/{}/{}/4x/'.format(night, '{:08d}'.format(expid), view, frame), code=302)

    from nightwatch.webpages import spectra
    return spectra.get_spectra_html(os.path.join(datadir, str(night)), night, expid, view, frame, downsample)

@app.route('/<int:night>/')
def getnight(night):
    global indir
    explist = os.path.join(str(night), 'exposures.html')
    print(f'returning {explist}', file=sys.stderr)
    return send_from_directory(indir, explist)

@app.route('/<int:night>/<int:expid>/')
def getexp(night, expid):
    global indir
    qaexp = f'{night}/{expid:08d}/qa-summary-{expid:08d}.html'
    print(f'returning QA summary {qaexp}', file=sys.stderr)
    return send_from_directory(indir, qaexp)

@app.route('/<path:filepath>')
def getfile(filepath):
    global indir
    global datadir

    fullpath = os.path.join(indir, filepath)
    if os.path.isfile(fullpath):
        print(f"found {fullpath}", file=sys.stderr)
        return send_from_directory(indir, filepath)

    # Try YEARMMDD/EXPID06/preproc-CAM-EXPID-Nx.html that isn't generated yet
    m = re.match('^(20\d{6})/(\d{8})/preproc-([brz]{1}\d{1})-(\d{8})-(\d*)x.html$', filepath)
    if m:
        night, expid, camera, expid2, downsample = m.groups()
        if expid != expid2:
            return f"expid mismatch in directory ({expid}) vs. filename ({expid2})"

        fitsfilepath = f'{datadir}/{night}/{expid}/preproc-{camera}-{expid}.fits'
        if os.path.isfile(fitsfilepath):
            print("found " + fitsfilepath, file=sys.stderr)
            downsample = int(downsample)
            if downsample <= 0:
                return 'invalid downsample'

            from nightwatch.webpages import plotimage
            plotimage.write_image_html(fitsfilepath, os.path.join(indir, filepath), downsample, night)
            return send_from_directory(indir, filepath)

    print("could NOT find " + fullpath, file=sys.stderr)
    return 'ERROR: no data found for input URL'

if __name__ == "__main__":
    app.run(debug=args.debug, host=args.host, port=args.port)

