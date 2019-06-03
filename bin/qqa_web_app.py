import os, sys
import argparse
from flask import (Flask, send_from_directory)

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
        from qqa.plots import plotimage

        plotimage.main(fitsfilepath, os.path.join(stat, filepath), downsample)
        return send_from_directory(stat, filepath)

    print("could NOT find " + fitsfilepath, file=sys.stderr)
    return 'no data for ' + os.path.join(stat, filepath)

if __name__ == "__main__":
    app.run(debug=True)
