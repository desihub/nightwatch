import os, sys, re, json
import argparse, jinja2
import bokeh
from bokeh.embed import components
from flask import (Flask, send_from_directory, redirect)

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
stat = ""
data = ""

parser = argparse.ArgumentParser(usage = "{prog} [options]")
parser.add_argument("-s", "--static", type=str, required=True, help="static file directory")
parser.add_argument("-d", "--data", type=str, help="data/fits file directory")
parser.add_argument("--host", type=str, default="localhost", help="hostname (e.g. localhost or 0.0.0.0")
parser.add_argument("--port", type=int, default=8001, help="port number")
args = parser.parse_args()

stat = args.static
data = args.data

@app.route('/')
def redict_to_cal():
    print('redirecting to nights.html')
    return redirect('nights.html', code=302)


@app.route('/timeseries/')
def test_input():
    env = jinja2.Environment(
        loader=jinja2.PackageLoader('qqa.webpages', 'templates')
    )
    filename = os.path.join(stat, "cal_files", "timeseries_dropdown.json")

    with open(filename, 'r') as myfile:
        json_data=myfile.read()

    dropdown = json.loads(json_data)

    template = env.get_template('timeseries_input.html')
    return template.render(dropdown_hdu=dropdown)

@app.route('/timeseries/<int:start_date>/<int:end_date>/<string:hdu>/<string:attribute>')
def test_timeseries(start_date, end_date, hdu, attribute):

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

    filename = os.path.join(stat, "cal_files", "timeseries_dropdown.json")

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

    from qqa.webpages.timeseries import generate_timeseries_html

    html = generate_timeseries_html(data, start_date, end_date, hdu, attribute, dropdown)

    return html

@app.route('/<int:night>/<string:expid>/spectra/')
def redirect_to_spectrograph_stectra(night, expid):
    print('redirecting to spectrograph stectra')
    return redirect('{}/{}/spectra/spectrograph/qframe/4x/'.format(night, expid), code=302)

@app.route('/<int:night>/<int:expid>/spectra/input/', defaults={'frame': None, 'select_string': None, 'downsample': None})
@app.route('/<int:night>/<int:expid>/spectra/input/<string:select_string>/<string:frame>/<string:downsample>/')
def getspectrainput(night, expid, select_string, frame, downsample):
    global data
    data = os.path.abspath(data)
    from qqa.webpages import spectra
    return spectra.get_spectra_html(os.path.join(data, str(night)), expid, "input", frame, downsample, select_string)

@app.route('/<int:night>/<int:expid>/spectra/<string:view>/', defaults={'frame': None, 'downsample': None})
@app.route('/<int:night>/<int:expid>/spectra/<string:view>/<string:frame>/', defaults={'downsample': None})
@app.route('/<int:night>/<int:expid>/spectra/<string:view>/<string:frame>/<string:downsample>/')
def getspectra(night, expid, view, frame, downsample):
    global data
    data = os.path.abspath(data)

    if downsample is None:
        return redirect('{}/{}/spectra/{}/{}/4x/'.format(night, expid, view, frame), code=302)

    from qqa.webpages import spectra
    return spectra.get_spectra_html(os.path.join(data, str(night)), expid, view, frame, downsample)

@app.route('/<path:filepath>')
def getfile(filepath):
    global stat
    global data
    stat = os.path.abspath(stat)
    data = os.path.abspath(data)

    exists_html = os.path.isfile(os.path.join(stat, filepath))
    if exists_html:
        print("found " + os.path.join(stat, filepath), file=sys.stderr)
        print("retrieving " + os.path.join(stat, filepath), file=sys.stderr)
        return send_from_directory(stat, filepath)

    print("could NOT find " + os.path.join(stat, filepath), file=sys.stderr)

    # splits the url contents by '/'
    filedir, filename = os.path.split(filepath)

    filebasename, fileext = os.path.splitext(filename)

    splitname = filebasename.split('-')
    down = splitname.pop()
    if down[len(down)-1] != 'x':
        return 'no data for ' + os.path.join(stat, filepath)

    filebasename = '-'.join(splitname)
    fitsfilename = '{filebasename}.fits'.format(filebasename=filebasename)
    fitsfilepath = os.path.join(data, filedir, fitsfilename)
    exists_fits = os.path.isfile(fitsfilepath)

    exists_fits = os.path.isfile(fitsfilepath)
    if exists_fits:
        print("found " + fitsfilepath, file=sys.stderr)
        downsample = int(down[:len(down)-1])
        if downsample <= 0:
            return 'invalid downsample'

        # assume qqa/py is in PYTHONPATH
        # sys.path.append(os.path.abspath(os.path.join('..', 'py', 'qqa')))
        from qqa.webpages import plotimage

        plotimage.write_image_html(fitsfilepath, os.path.join(stat, filepath), downsample)
        return send_from_directory(stat, filepath)

    print("could NOT find " + fitsfilepath, file=sys.stderr)
    return 'no data for ' + os.path.join(stat, filepath)

if __name__ == "__main__":
    app.run(debug=True, host=args.host, port=args.port)
