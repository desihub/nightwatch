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

@app.route('/<path:filepath>')
def getfile(filepath):
    global stat
    global data
    exists_html = os.path.isfile(os.path.join(stat, filepath))
    if exists_html:
        return send_from_directory(stat, filepath)

    while (len(filepath) != 0 and filepath[len(filepath)-1] == '/'):
        filepath = filepath[:len(filepath)-1]
    # splits the url contents by '/'
    filename_split = filepath.split('/')
    if len(filename_split) < 3:
        return 'no data for ' + os.path.join(stat, filepath)

    cam = filename_split[2].split('-')[0]
    down = filename_split[2].split('-')[1].split('.')[0]

    fitsfilename = 'preproc' + '-' + cam + '-' + filename_split[1] + '.fits'
    fitsfilepath = os.path.join(data, filename_split[0], filename_split[1], fitsfilename)

    exists_fits = os.path.isfile(fitsfilepath)
    if exists_fits:
        downsample = int(down[:len(down)-1])
        if downsample <= 0:
            return 'invalid downsample'

        sys.path.append(os.path.abspath(os.path.join('..', 'py', 'qqa')))
        import plots.plotimage

        plots.plotimage.main(fitsfilepath, os.path.join(stat, filepath), downsample)
        return send_from_directory(stat, filepath)
    return 'no data for ' + os.path.join(stat, filepath)

if __name__ == "__main__":
    app.run(debug=True)
