import jinja2
from jinja2 import select_autoescape
import bokeh, os, re, sys

from ..plots.plotimage import main

def write_image_html(input, output, downsample, night):
    '''
    Writes a downsampled image to a given output file.
    Inputs:
        input: image fits file to be plotted
        output: the filepath to write html file to 
        downsample: downsample image NxN
        night: the night YYYYMMDD the image belongs to
    '''

    env = jinja2.Environment(
        loader=jinja2.PackageLoader('nightwatch.webpages', 'templates'),
        autoescape=select_autoescape(disabled_extensions=('txt',),
                                     default_for_string=True, 
                                     default=True)
    )
    
    template = env.get_template('preproc.html')

    plot_script, plot_div = main(input, None, downsample)

    input_dir = os.path.dirname(input)
    available = []
    preproc_files = [i for i in os.listdir(input_dir) if re.match(r'preproc.*', i)]
    for file in preproc_files:
        available += [file.split("-")[1]]

    current = os.path.basename(input).split("-")[1]
    expid = os.path.basename(input).split("-")[2].split(".")[0]

    html_components = dict(
        plot_script = plot_script, plot_div = plot_div,
        bokeh_version=bokeh.__version__, downsample=str(downsample), preproc=True,
        basename=os.path.splitext(os.path.basename(input))[0], night=night,
        available=available, current=current, expid=int(str(expid)), zexpid=expid,
        num_dirs=2, qatype='amp',
    )

    html = template.render(**html_components)

    #- Write HTML text to the output file
    with open(output, 'w') as fx:
        fx.write(html)

    print('Wrote {}'.format(output))


def write_preproc_table_html(input_dir, night, expid, downsample, output):
    '''
    Writes html file with preproc navigation table
    Inputs:
        input_dir: directory containing subdirectories with preproc images
        night: YYYYMMDD
        expid: exposure preproc images belong to
        downsample: downsample image NxN
        output: write html file here
    '''
    env = jinja2.Environment(
        loader=jinja2.PackageLoader('nightwatch.webpages', 'templates'),
        autoescape=select_autoescape(disabled_extensions=('txt',),
                                     default_for_string=True, 
                                     default=True)
    )
    
    template = env.get_template('preproc.html')

    available = []
    preproc_files = [i for i in os.listdir(input_dir) if re.match(r'preproc.*', i)]
    for file in preproc_files:
        available += [file.split("-")[1]]

    html_components = dict(
        version=bokeh.__version__, downsample=str(downsample),
        preproc=True, night=night, available=available,
        current=None, expid=int(expid), zexpid='{:08d}'.format(expid),
        num_dirs=2, qatype='amp',
    )
    
    make_composites(input_dir, night, expid)
    preproc_composites = [i for i in os.listdir(input_dir) if re.match(r'preproc.*composite*', i)]

    cams = ["Bcomposite", "Rcomposite", "Zcomposite"]
    for cam, composite in zip(cams, preproc_composites):
        compositepath = os.join(input_dir, composite)
        script, div = main(compositepath, None, downsample)
        html_components[cam] = dict(script=script, div=div)

    html = template.render(**html_components)

    #- Write HTML text to the output file
    with open(output, 'w') as fx:
        fx.write(html)

    print('Wrote {}'.format(output))



import numpy as np
from glob import glob
import fitsio
from astropy.io import fits

def load_preproc_portion(preproc):
    '''
    Splices together 20 vertical strips, 2 from each preproc files
    Inputs:
        preproc: list of ordered preproc files for a given camera

    '''
    size = 200
    xmin = 0
    xmax = 4000
    #xmin = 1000
    #xmax = 3000
    images = []
    restart = 2048
    start = restart-len(preproc)*size
    for n, ppfile in enumerate(preproc):
        file = fitsio.FITS(ppfile) ## fix this?
        images.append(file["IMAGE"][xmin:xmax,start+n*size:start+(n+1)*size])
        images.append(file["IMAGE"][xmin:xmax,restart+n*size:restart+(n+1)*size])
        #print(ppfile, np.shape(images[-1]))
    
    full = np.empty([np.shape(images[0])[0], size*len(images)], dtype=np.float32)
    #print(np.shape(full))
    slot = np.arange(len(images))
    slot = (slot//2 + (slot%2)*len(images)/2).astype(int32)
    for n, im in enumerate(images):
        full[:,slot[n]*size:(slot[n]+1)*size] = images[n]
    extent = [start, start+size*20, xmin, xmax]
    return full, extent

def make_composites(preprocdir, night, expid):
    '''
    Compiles composite preproc images for each camera and writes .fits file to preprocdir
    Inputs:
        preprocdir: directory containing subdirectories with preproc images
        night: YYYYMMDD
        expid: exposure preproc images belong to

    '''
    preprocfiles = sorted(glob(preprocdir+'/preproc*.fits'))
    if len(preprocfiles)<30: 
        print("Couldn't find the preproc spectroscopy files in", directory)
        return
    roll = -(expid%10)
    b_image = load_preproc_portion(np.roll(preprocfiles[0:10],roll))
    r_image = load_preproc_portion(np.roll(preprocfiles[10:20],roll))
    z_image = load_preproc_portion(np.roll(preprocfiles[20:30],roll))
    print("preprocs loaded")
        
    hdu = fits.PrimaryHDU(b_image[0])
    outfile =  os.path.join(preprocdir, "preproc-{}-{:08d}.fits").format("b" + "composite", expid)
    hdu.writeto(outfile, overwrite=True)
    print("b composite done")
    
    hdu = fits.PrimaryHDU(r_image[0])
    outfile =  os.path.join(preprocdir, "preproc-{}-{:08d}.fits").format("r" + "composite", expid)
    hdu.writeto(outfile, overwrite=True)
    print("r composite done")

    hdu = fits.PrimaryHDU(z_image[0])
    outfile =  os.path.join(preprocdir, "preproc-{}-{:08d}.fits").format("z" + "composite", expid)
    hdu.writeto(outfile, overwrite=True)
    print("z composite done")

def sqrt_stretch(x):
    return x/np.sqrt(np.abs(x+1e-10))

