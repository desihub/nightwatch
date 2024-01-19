#!/bin/bash

if [ $(whoami) != "desi" ]; then
    echo "only run this as desi@perlmutter on NERSC; exiting"
    exit 1
fi

if [[ ! -v CFS ]]; then
    echo "CFS environment variable not set; exiting"
    exit 1
fi

NIGHTWATCH=${CFS}/desi/spectro/nightwatch/nersc

usage() { echo "Usage: $0 [-h] [-d YYYYMMDD] [-x]" 1>&2; exit 1; }

while getopts ":h:d:x" o; do
    case "${o}" in
        h)
            # Print help message.
            usage
            ;;
        d)
            # Use a specific date.
            date=${OPTARG}
            ;;
        x)
            # Must specify -x to delete old files
            # (supports testing and prevents unfortunate mistakes)
            delete_files=True
            ;;
        *)
            usage
            ;;
    esac
done
shift $((OPTIND-1))

if [ -z "${date}" ]; then
    date="20??????"
fi

# Delete nonessential FITS files >1 week old. Keep spectra FITS files.
for prefix in preproc qsky qfiberflat psf; do
    if [ -z "${delete_files}" ]; then
        find ${NIGHTWATCH}/${date} -name ${prefix}\*.fits -mtime +7 -exec ls {} \;
    else
        find ${NIGHTWATCH}/${date} -name ${prefix}\*.fits -mtime +7 -exec rm {} \;
    fi
done
