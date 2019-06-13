import os, sys, re, json
import argparse, jinja2
import bokeh
from bokeh.embed import components
from flask import (Flask, send_from_directory, redirect)

app = Flask(__name__)
stat = ""
data = ""

parser = argparse.ArgumentParser(usage = "{prog} [options]")
parser.add_argument("-s", "--static", type=str, required=True, help="static file directory")
parser.add_argument("-d", "--data", type=str, help="data/fits file directory")
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

    from qqa.plots.timeseries import generate_timeseries

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
    app.run(debug=True)
