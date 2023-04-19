import numpy as np
import matplotlib.pyplot as plt
from astropy.io import fits
import os

nw_path='/global/cfs/cdirs/desi/spectro/nightwatch/nersc/'

exposures=[]

#select program and dates to take into account

program='CALIB long Arcs Cd+Xe'
caltype='longarcs'
cam='B3612'
petal=0

february=np.arange(1,28+1).astype(str)
march=np.arange(1,31+1).astype(str)
april=np.arange(1,9+1).astype(str)

months=[february,march,april]
monthids=['02','03','04']




mean_flux=np.zeros(sum([len(i) for i in months]))
std_flux=np.zeros(sum([len(i) for i in months]))

mean_temp=np.zeros(sum([len(i) for i in months]))
std_temp=np.zeros(sum([len(i) for i in months]))

mean_humidity=np.zeros(sum([len(i) for i in months]))
std_humidity=np.zeros(sum([len(i) for i in months]))

mean_flux[:],std_flux[:]=np.nan,np.nan
mean_temp[:],std_temp[:]=np.nan,np.nan
mean_humidity[:],std_humidity[:]=np.nan,np.nan


nightlabel=[]
i=0
m=0
for month in months:
    monthid=monthids[m]
    for night in month:
        if len(night)==1:
            nightid='2023'+monthid+'0'+night
        elif len(night)==2:
            nightid='2023'+monthid+night
        nightlabel.append(nightid[4:6]+'/'+nightid[6:])
        night_path=nw_path+nightid
        flux=[]
        tairtemp=[]
        humidity=[]
        
        try:
            expids=[f.name for f in os.scandir(night_path) if f.is_dir()]
        except:
            i+=1
            continue

        for expid in expids:
            try:
                F=fits.open(nw_path+nightid+'/'+expid+'/qa-'+expid+'.fits')
                T=F['PER_SPECTRO'].data
                if program in T['PROGRAM']:
                    flux.append(T[cam][petal])
                    tairtemp.append(F['PER_SPECTRO'].header['TAIRTEMP'])
                    humidity.append(F['PER_SPECTRO'].header['TPR1HUM'])
            except:
                continue

        mean_flux[i]=np.mean(flux)
        std_flux[i]=np.std(flux)
        mean_temp[i]=np.mean(tairtemp)
        std_temp[i]=np.mean(tairtemp)
        mean_humidity[i]=np.mean(humidity)
        std_humidity[i]=np.mean(humidity)
        i+=1
    m+=1

plt.figure(figsize=(20,5))
plt.errorbar(nightlabel,mean_flux,yerr=std_flux,fmt='bo')
plt.xlabel('Day')
plt.ylabel('Flux')
plt.xticks(rotation=90)
plt.grid()
plt.title('From 02/01 to 04/09 / '+program+' / '+cam+' / petal 0')
plt.savefig('time_series_'+caltype+'.png')


plt.figure(figsize=(8,6))
plt.errorbar(mean_temp,mean_flux,yerr=std_flux,fmt='bo')
plt.xlabel('TAIRTEMP')
plt.ylabel('Flux')
plt.grid()
plt.title('From 02/01 to 04/09 / '+program+' / '+cam+' / petal 0')
plt.savefig('temp_vs_flux_'+caltype+'.png')



plt.figure(figsize=(8,6))
plt.errorbar(mean_humidity,mean_flux,yerr=std_flux,fmt='bo')
plt.xlabel('TPR1HUM')
plt.ylabel('Flux')
plt.grid()
plt.title('From 02/01 to 04/09 / '+program+' / '+cam+' / petal 0')
plt.savefig('humidity_vs_flux_'+caltype+'.png')