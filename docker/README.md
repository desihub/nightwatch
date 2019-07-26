# Running A Containerized Nightwatch 
This tutorial will go through the process of setting up a stack to run Nightwatch on Spin, or on a local machine, in addition to documenting the configurations and default images built for Nightwatch. 

## Contents
- [General Structure](#general-structure) 
- [Configuring Images](#configuring-images)
  - [uWSGI](#uwsgi)
    - [Image Context](#image-context)
  - [Nginx](#nginx)
- [Docker-compose](#docker-compose)
- [Running At NERSC (Spin and Rancher)](#running-at-nersc)

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

uid = 80355 #TO DO: change to environment variable
gid = 58102

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

## Docker-compose
```
insert docker-compose code here
```


## Running at NERSC
