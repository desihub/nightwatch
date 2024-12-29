#!/bin/bash
################################################################################
# Synchronize darks and bias files from DESI_SPECTRO_DARK at NERSC.
# Since rsync over ssh does not work on the DESI cluster, use wget.
#
# Required files: a configuration file with the format
#   user=user
#   passwd=password
# is required for this script to function.
################################################################################

#- Only run on desi-8.
if [ "$HOSTNAME" != "desi-8" ]; then
    echo "Synchronization only works on desi-8."
    exit 0
fi

#- Default settings
URL="https://data.desi.lbl.gov/desi/spectro/desi_spectro_dark/latest"
DESI_SPECTRO_DARK="/software/datasystems/desi_spectro_dark"
VERSION="latest"

#- Load user access info from config file
. ${DESI_SPECTRO_DARK}/sync_desi_spectro_dark.conf

echo `date --utc`

#- Download bias and dark frames
for folder in dark_frames bias_frames; do
    echo "Downloading ${folder} from ${URL}"

    mkdir -p ${DESI_SPECTRO_DARK}/${VERSION}/${folder}
    cd ${DESI_SPECTRO_DARK}/${VERSION}/${folder}

    wget -e robots=off -nd -np --mirror --retr-symlinks=no --user=${user} --password=${passwd} --no-check-certificate ${URL}/${folder}/
    echo `date --utc`
done

#- Get top-level CSV records
for csv in bias_table dark_table exp_daily_dark exp_dark_zero; do
    csvfile=${csv}.csv
    cd ${DESI_SPECTRO_DARK}/${VERSION}

    wget --user=${user} --password=${passwd} --no-check-certificate ${URL}/${csvfile} -O ${csvfile}
done

echo `date --utc`