#!/usr/bin/bash

if [ $(hostname) != "desi-8" ] || [ $(whoami) != "datasystems" ]; then
    echo "only run this as datasystems@desi-8 at KPNO; exiting"
    exit 1
fi

#- Delete non-essential FITS files more than a week old
for prefix in preproc qsky qfiberflat psf; do
    find /exposures/nightwatch/20?????? -name ${prefix}\*.fits -mtime +7 -exec rm {} \;
done

#- Delete spectra FITS files more than 2 weeks old
find /exposures/nightwatch/20?????? -name \*frame\*.fits -mtime +14 -exec rm {} \;

#- Delete preproc HTML files and replace with a simple redirect page
clean_preproc() {
    dir=`dirname $1`
    cd $dir
    ppfile=`basename $1`
    preproc=preproc.html
    if [ ! -f ${preproc} ]; then
        # echo "Creating ${preproc}"
cat << EOF > ${preproc}
<html>
  <head>
    <title>Preproc output: not found.</title>
  </head>
  <body>
    <p>Preproc output removed.</p>
    <button onclick="history.back()">Go Back</button>
  </body>
</html>
EOF
    fi

    rm ${ppfile}
    ln -s ${preproc} ${ppfile}
}

export -f clean_preproc
find /exposures/nightwatch/20?????? -name \*preproc-\*.html -mtime +14 -exec bash -c 'clean_preproc "$1"' _ {} \;

#- Delete exposure folders older than 1 year. A "manual" approach is being used because the find command has a tendency to hang without exiting.
for ymd in `\ls /exposures/nightwatch | grep -E "^20[0-9]{6}$"`; do
    let delta=(`date +%s`-`date +%s -d ${ymd}`)/86400
    if [ ${delta} -gt 365 ]; then
        if [ -d /exposures/nightwatch/${ymd} ]; then
            rm -rf /exposures/nightwatch/${ymd}
        fi
    fi
done
