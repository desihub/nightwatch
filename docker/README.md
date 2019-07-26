# Running A Containerized Nightwatch 
This tutorial will go through the process of setting up a stack to run Nightwatch on Spin, or on a local machine, in addition to documenting the configurations and default images built for Nightwatch. 

## Contents
- [General Structure](#general-structure) 
- [Configuring Images](#configuring-images)
  - [uWSGI](#uwsgi)
    - [Image Context](#image-context)
  - [Nginx](#nginx)
- [Running At NERSC (Spin and Rancher)](#running-at-nersc)
  - [Getting Started](#getting-started)

## General Structure
Our stack will consist of two separate containers, one running [Nginx](https://nginx.org/en/docs/) to serve as our frontend server, and one running [uWSGI](https://uwsgi-docs.readthedocs.io/en/latest/index.html), which will handle transferring requests between Nginx and our Flask web app. To coordinate these two containers, we have to use Docker-compose, which will allow the two containers to communicate properly. Spin, where we will run the stack at NERSC, handles the actual distribution of nodes and the connection to the internet. 

## Configuring Images
Generally, it shouldn't be necessary to modify the base Docker images, but this section will document the Dockerfiles and specific configurations in case modifications need to be made. 

### uWSGI

```
FROM python:3

WORKDIR /app
ENV PYTHONPATH ${PYTHONPATH}:./qqa/py
ENV PYTHONPATH ${PYTHONPATH}:./desimodel/py
ENV PYTHONPATH ${PYTHONPATH}:./desiutil/py
ADD . /app
RUN pip install -r requirements.txt
EXPOSE 5000

ENTRYPOINT [ "uwsgi" ]
CMD [ "--ini", "app.ini", "--pyargv", "-s ./static -d ./data"]
```

#### Image context
The uWSGI image also contains an app.ini file with uWSGI specific configurations:
```
[uwsgi]
protocol = http
module = app
callable = app
master = true

processes = 5
single-interpreter = true

http-socket = :5000
vacuum = true

die-on-term = true
```

### Nginx

```
FROM nginx:latest

RUN chgrp nginx /var/cache/nginx/
RUN chmod g+w /var/cache/nginx/

RUN sed --regexp-extended --in-place=.bak 's%(^\s+listen\s+)80(;)%\18080\2%' /etc/nginx/conf.d/default.conf
EXPOSE 80

RUN sed --regexp-extended --in-place=.bak 's%^pid\s+/var/run/nginx.pid;%pid /var/tmp/nginx.pid;%' /etc/nginx/nginx.conf
```

## Running at NERSC
## Getting Started
First step is accessing Spin, through Cori.
```
yourlocalmachine$ ssh [your username]@cori.nersc.gov
@cori$ module load spin
```
Next, we want to define which rancher environment we are going to be using. There are two options: cattle-dev, and cattle-prod, the development and production environments, respectively. In this example, and for non-production state versions, we will choose cattle-dev. The environment variable is helpful, or rancher will ask us every time we try and do something to choose which environment we want to do it in.
```
@cori$ export RANCHER_ENVIRONMENT=cattle-dev
```
Now, we will create the directory structure we need for the application to work smoothly, and to mount our volumes properly. First, create a directory you want to keep the docker-compose files, and nginx configurations in. 
```
@cori$ export SPIN_DIRECTORY=path/to/where/you/want/the/project/
@cori$ mkdir $SPIN_DIRECTORY && cd $SPIN_DIRECTORY
```
This should probably be somewhere near to the static html files and data that we will use to populate the app, or somewhere from which you can easily gain access to those files (as we will be mounting those other directories into our containers). For example, this is my own directory structure that I use, all within my own global project filesystem directory:
```bash
├── nightwatch-stack (contains docker files)
│   ├── docker-compose.yml
│   ├── web (contains specific nginx stuff)
│   │   ├── nginx.conf
├── qqatest
│   ├── output (static html files)
│   ├── data (data for dynamic stuff)
│   │   ├── output
├── qqa
├── desimodel
└── desiutil
```
After choosing a good place for the project files, make a new yaml file called docker-compose:
```
SPIN_DIRECTORY$ touch docker-compose.yml $$ open docker-compose.yml
```
And copy and paste the following text, with your data replaced in the brackets: 
```
version: '2'
services:
  app:
    image: registry.spin.nersc.gov/alyons18/app-uwsgi-flask:latest
    user: [your UID]:[your GID, probably desi (58102)]
    retain_ip: true            
    cap_drop:                  
    - ALL
  web:
    image: registry.spin.nersc.gov/alyons18/web-nginx:latest
    ports:
    - "60000:8080"
    user: [your UID]:[your GID]
    group_add:
    - nginx
    cap_drop:
    - ALL
```
Note: you can replace the port above with any port you would like [(look at the Spin port guide)](https://docs.nersc.gov/services/spin/best_practices/#networking). 
Next, we will make a directory specific to the web service:
```
SPIN_DIRECTORY$ mkdir web && cd web
SPIN_DIRECTORY$ touch nginx.conf && open nginx.conf
```
This file will contain our specific nginx configurations, which will allow it to act correctly as a reverse proxy for our flask app. In here, paste the below code:
```
server {
    listen 8080;
    location / {
      proxy_pass http://app:5000;
      proxy_redirect http://$host:8080 http://$host:60000;
      proxy_set_header Host $host:60000;
      proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
      proxy_set_header X-Forwarded-Host $server_name;
      proxy_set_header X-Real-IP $remote_addr;
    }
}
```
Note: again, if you chose a port other than 60000, replace 60000 with your port in the file above. This file tells nginx to pass all requests it receives to the proxy http://app:5000, which is where uWSGI is listening (see the app.ini file). On the way back, we need to tell nginx to direct traffic from the internal port it listens on (8080), to the external port the user is accessing (60000, in this case), hence the proxy_redirect statement. The other lines set the header on the requests going to uWSGI, and can be further configured to adjust security.

### Mounting Volumes and Setting Permissions
So far, we have a docker-compose file that will theoretically run- however, we don't have any content for our app! We need to mount the external directories containing these files into our container. Here, we are using docker volumes, although there 
volumes:
     - ../qqatest/output:/app/static 
     - ../qqa:/app/qqa:ro
     - ../desimodel:/app/desimodel:ro
     - ../desiutil:/app/desiutil:ro
     - ../qqatest/data/output:/app/data:ro
    user: 80355:58102
    entrypoint: uwsgi
    command:
     - --ini
     - app.ini
     - --pyargv
     - '-s ./static -d ./data' 
     - --uid                   
     - '80355'
     - --gid
     - '58102'
volumes:
    - ./web/nginx-proxy.conf:/etc/nginx/conf.d/default.conf:ro
    user: 80355:58102          
