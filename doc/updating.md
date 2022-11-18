# How to Update and Restart Nightwatch

## Instructions at KPNO

As of March 2022, Nightwatch runs as a service at KPNO. Details are provided on
the [DESI wiki](https://desi.lbl.gov/trac/wiki/DOS/NightWatchService).

Update instructions are available at
```
/exposures/nightwatch/README
```
in the DESI cluster. The contents of the README are copied below.

### Set up the Environment

In order to update the version of Nightwatch, log into desi-7:
```
ssh datasystems@desi-7.kpno.noao.edu
```

Next, configure the environment using the `gonightwatch` command:
```
gonightwatch
```

### Check Status

Check the Nightwatch monitor and webapp status using the [process
control commands](https://desi.lbl.gov/trac/wiki/DOS/NightWatchService):
```
nwctl status    # Check Nightwatch monitor
nwwactl status  # Check Nightwatch webapp
```

You can also check the Nightwatch log and make sure it's updating every 10 s.
```
cd /exposures/nightwatch
tail -f nightwatch.log
```

### Update the Software

To update the Nightwatch installation, stop Nightwatch with nwctl.
```
nwctl stop
nwctl status # Confirm it has stopped
```

Then run
```
cd $NIGHTWATCH
git pull
cd /exposures/nightwatch
```

### Cleanup and Restart
If you stopped in the middle of processing an exposure, it may not have cleanly
finished processing. Check `nightwatch.log`. You can always delete the relevant
exposure folder before restarting to ensure processing is completed.
```
rm -rf /exposures/nightwatch/YYYYMMDD/00NNNNNN  # with caution!
nwctl start
nwctl status                                    # Confirm it has started
tail -f nightwatch.log                          # Confirm it is processing
```

If the webapp needs to be restarted, use the nwwactl process control:
```
nwwactl start
nwwactl status                                  # Confirm it is running
tail -f nightwatch-webapp.log                   # Confirm it is processing
```

## Instructions at NERSC

### Cori

Cori is being replaced in 2023. As of the end of 2022, the primary Nightwatch instance runs on `cori21`. Instructions for updating Nightwatch on Cori are available in
```
/global/cfs/cdirs/desi/spectro/nightwatch/nersc/README
```

### Perlmutter

Perlmutter will replace Cori in 2023. A test installation is available for updates. Instructions are available at
```
/global/cfs/cdirs/desi/spectro/nightwatch/nersc/perlmutter/README
```
