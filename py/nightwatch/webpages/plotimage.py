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

    current = os.path.basename(input).split("-")[1]
    expid = os.path.basename(input).split("-")[2].split(".")[0]

    if re.match(r'pp-bcomposite*', os.path.basename(output)):
        plot_script, plot_div = main(input, None, downsample, label="B", roll=-(int(expid)%10))
    elif re.match(r'pp-rcomposite*', os.path.basename(output)):
        plot_script, plot_div = main(input, None, downsample, label="R", roll=-(int(expid)%10))
    elif re.match(r'pp-zcomposite*', os.path.basename(output)):
        plot_script, plot_div = main(input, None, downsample, label="Z", roll=-(int(expid)%10))
    else:
        plot_script, plot_div = main(input, None, downsample)

    input_dir = os.path.dirname(input)
    available = []
    preproc_files = [i for i in os.listdir(input_dir) if re.match(r'preproc.*', i)]
    preproc_files = [i for i in os.listdir(input_dir) if (re.match(r'preproc.*', i) or re.match(r'pp.*', i))]

    for file in preproc_files:
        available += [file.split("-")[1]]

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

    make_composites(input_dir, night, expid)
    preproc_composites = [i for i in os.listdir(input_dir) if re.match(r'pp.*composite.*fits', i)]
    print(preproc_composites)

    compositepath = os.path.join(input_dir, preproc_composites[0])
    print(compositepath)
    plot_script, plot_div = main(compositepath, None, downsample)

    html_components = dict(
        version=bokeh.__version__, downsample=str(downsample),
        preproc=True, night=night, available=available,
        current=None, expid=int(expid), zexpid='{:08d}'.format(expid),
        num_dirs=2, qatype='amp', plot_script = plot_script, plot_div = plot_div,
    )
    
    # make_composites(input_dir, night, expid)
    # preproc_composites = [i for i in os.listdir(input_dir) if re.match(r'pp.*composite.*fits', i)]
    # print(preproc_composites)

    # cams = ["Bcomposite", "Rcomposite", "Zcomposite"]
    # for cam, composite in zip(cams, preproc_composites):
    #     compositepath = os.path.join(input_dir, composite)
    #     print(compositepath)
    #     script, div = main(compositepath, None, downsample)
    #     html_components[cam] = dict(script=script, div=div)

    html = template.render(**html_components)

    #- Write HTML text to the output file
    with open(output, 'w') as fx:
        fx.write(html)

    print('Wrote {}'.format(output))

def write_composites_html(input_dir, night, expid, downsample, output):
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
    
    template = env.get_template('composites.html')

    html_components = dict(
        version=bokeh.__version__, downsample=str(downsample),
        night=night, expid=int(expid), zexpid='{:08d}'.format(expid),
        num_dirs=2, qatype='amp',
    )

    make_composites(input_dir, night, expid)
    preproc_composites = [i for i in os.listdir(input_dir) if re.match(r'pp.*composite.*fits', i)]
    print(preproc_composites)

    bcompositepath = os.path.join(input_dir, preproc_composites[0])
    print(bcompositepath)
    script, div = main(bcompositepath, None, downsample, label="B", roll=-(expid%10))
    html_components['BCOMPOSITE'] = dict(script=script, div=div, text="test")

    rcompositepath = os.path.join(input_dir, preproc_composites[1])
    print(rcompositepath)
    script, div = main(rcompositepath, None, downsample, label="R", roll=-(expid%10))
    html_components['RCOMPOSITE'] = dict(script=script, div=div)

    zcompositepath = os.path.join(input_dir, preproc_composites[2])
    print(zcompositepath)
    script, div = main(zcompositepath, None, downsample, label="Z", roll=-(expid%10))
    html_components['ZCOMPOSITE'] = dict(script=script, div=div)

    html = template.render(**html_components)

    #- Write HTML text to the output file
    with open(output, 'w') as fx:
        fx.write(html)

    print('Wrote {}'.format(output))

    

def write_composite_html(inputs, output, downsample, night):
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

    input = inputs[0]
    expid = os.path.basename(input).split("-")[2].split(".")[0]

    bscript, bdiv = main(inputs[0], None, downsample, label="B", roll=-(int(expid)%10))
    rscript, rdiv = main(inputs[1], None, downsample, label="R", roll=-(int(expid)%10))
    zscript, zdiv = main(inputs[2], None, downsample, label="Z", roll=-(int(expid)%10))

    input_dir = os.path.dirname(input)
    available = []
    preproc_files = [i for i in os.listdir(input_dir) if re.match(r'preproc.*', i)]
    preproc_files = [i for i in os.listdir(input_dir) if (re.match(r'preproc.*', i) or re.match(r'pp.*', i))]

    for file in preproc_files:
        available += [file.split("-")[1]]

    html_components = dict(
        bokeh_version=bokeh.__version__, downsample=str(downsample), preproc=True,
        basename=os.path.splitext(os.path.basename(input))[0], night=night,
        available=available, current=None, expid=int(str(expid)), zexpid=expid,
        num_dirs=2, qatype='amp', composite=True, bscript=bscript, bdiv=bdiv,
        rscript=rscript, rdiv=rdiv, zscript=zscript, zdiv=zdiv, 
    )

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
    slot = (slot//2 + (slot%2)*len(images)/2).astype(int)
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
        
    hdu = fits.PrimaryHDU(sqrt_stretch(b_image[0]))
    outfile =  os.path.join(preprocdir, "pp-{}-{:08d}.fits").format("b" + "compositesqrtstretch", expid)
    hdu.writeto(outfile, overwrite=True)
    print("b composite done")
    
    hdu = fits.PrimaryHDU(sqrt_stretch(r_image[0]))
    outfile =  os.path.join(preprocdir, "pp-{}-{:08d}.fits").format("r" + "compositesqrtstretch", expid)
    hdu.writeto(outfile, overwrite=True)
    print("r composite done")

    hdu = fits.PrimaryHDU(sqrt_stretch(z_image[0]))
    outfile =  os.path.join(preprocdir, "pp-{}-{:08d}.fits").format("z" + "compositesqrtstretch", expid)
    hdu.writeto(outfile, overwrite=True)
    print("z composite done")

def sqrt_stretch(x):
    return x/np.sqrt(np.abs(x+1e-10))

