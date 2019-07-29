# Running A Containerized Nightwatch 
This tutorial will go through the process of setting up a stack to run Nightwatch on Spin, or on a local machine, in addition to documenting the configurations and default images built for Nightwatch.

#### Useful resources:
Spin has some tutorials if you want to go through [building a Docker image](https://docs.nersc.gov/services/spin/getting_started/lesson-1/) or [starting up a basic stack](https://docs.nersc.gov/services/spin/getting_started/lesson-2/).

## Contents
- [General Structure](#general-structure) 
- [Configuring Images](#configuring-images)
  - [uWSGI](#uwsgi)
    - [Image Context](#image-context)
  - [Nginx](#nginx)
- [Running At NERSC (Spin and Rancher)](#running-at-nersc)
  - [Getting Started](#getting-started)
  - [Mounting Volumes](#mounting-volumes)
  - [Setting Permissions](#setting-permissions)
  - [Starting A Stack](#starting-a-stack)
- [Some Useful Tips and Tricks](#some-useful-tips-and-tricks)

## General Structure
Our stack will consist of two separate containers, one running [Nginx](https://nginx.org/en/docs/) to serve as our frontend server, and one running [uWSGI](https://uwsgi-docs.readthedocs.io/en/latest/index.html), which will handle transferring requests between Nginx and our Flask web app. To coordinate these two containers, we have to use Docker-compose, which will allow the two containers to communicate properly. Spin, where we will run the stack at NERSC, handles the actual distribution of nodes and the connection to the internet. 

![nightwatch structure](nightwatch-structure.png)

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
See the [uWSGI documentation](https://uwsgi-docs.readthedocs.io/en/latest/CustomOptions.html) if you want to learn more about the specific options here. The version of the app.ini file in this repo also contains some more details on these configs.

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
user@cori01: $ module load spin
```
Now, test your account:
```
user@cori01: $ spin-keygen.sh
Password for user ?
Success: Spin API Key generated for user.
user@cori01: $
```
Next, we want to define which rancher environment we are going to be using. There are two options: cattle-dev, and cattle-prod, the development and production environments, respectively. In this example, and for non-production state versions, we will choose cattle-dev. The environment variable is helpful, or rancher will ask us every time we try and do something to choose which environment we want to do it in.
```
user@cori01: $ export RANCHER_ENVIRONMENT=cattle-dev
```
Now, we will create the directory structure we need for the application to work smoothly, and to mount our volumes properly. First, create a directory you want to keep the docker-compose files, and nginx configurations in. 
```
user@cori01: $ export SPIN_DIRECTORY=path/to/where/you/want/the/project/
user@cori01: $ mkdir $SPIN_DIRECTORY && cd $SPIN_DIRECTORY
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
user@cori01:SPIN_DIRECTORY $ touch docker-compose.yml && open docker-compose.yml
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
user@cori01:SPIN_DIRECTORY $ mkdir web && cd web
user@cori01:SPIN_DIRECTORY $ touch nginx.conf && open nginx.conf
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

### Mounting Volumes
So far, we have a docker-compose file that will theoretically run- however, we don't have any content for our app! We need to mount the external directories containing these files into our container. Here, we are using docker volumes, although there are other ways to mount external files into a container (see the [docker-compose documentation](https://docs.docker.com/compose/compose-file/compose-file-v2/#volumes)). Mounting our data externally allows us to keep the image light, as well as making it easier to tweak the code or update the data or html files to new versions, without having to build a new image.
The syntax for mounting a volume is as follows:
```
volumes:
    - /external/path:/internal/path:mode
```
The path to the external directory (relative to the docker-compose.yml!), then the mountpoint within the directory, then the mode (here, mostly ro, or read-only). These are the volumes we need:
1. Static html files, mounted to /app/static
2. Processed data files, mounted to /app/data
3. Nightwatch, desimodel, and desiutil code, mounted to respective directories inside the /app directory
4. The nginx.conf file created above, mounted into the nginx container (you can copy and paste what I have below, as it should have the same relative directory structure)

This is what my docker-compose.yml looks like, with an added volumes section to the app and web services:
```
version: '2'
services:
  app:
    image: registry.spin.nersc.gov/alyons18/app-uwsgi-flask:latest
    volumes:
     - ../qqatest/output:/app/static 
     - ../qqa:/app/qqa:ro
     - ../desimodel:/app/desimodel:ro
     - ../desiutil:/app/desiutil:ro
     - ../qqatest/data/output:/app/data:ro
    user: [your UID]:[your GID, probably desi (58102)]
    retain_ip: true            
    cap_drop:                  
    - ALL
  web:
    image: registry.spin.nersc.gov/alyons18/web-nginx:latest
    volumes:
    - ./web/nginx-proxy.conf:/etc/nginx/conf.d/default.conf:ro
    ports:
    - "60000:8080"
    user: [your UID]:[your GID]
    group_add:
    - nginx
    cap_drop:
    - ALL
```
### Setting Permissions
Running at Spin means that our services need to comply with their [security requirements](https://docs.nersc.gov/services/spin/best_practices/#security). In addition, because we mounted directories in the global filesystem at NERSC above, our application needs to match user and group privileges for accessing those files, or we won't be able to use them for our service. This means we need to make sure that all the directories and sub-directories being accessed by our containers have the proper permissions:
```
user@cori01:SPIN_DIRECTORY $ chmod o+x [directories here]
```
Make sure all of your directories, going all the way from the top to the bottom, have the executable bit at the end. In addition to this, we need to be running the container as a non-root user, specifically one with permissions to access these files and make modifications. This also improves security, as we will be removing almost all of the capabilities that a root user would have.
We already mostly took care of the permissions issue by putting our uid and gid into the docker-compose, but there are some specific issues with how uWSGI runs that mean we need to reiterate this. In particular, uWSGI expects to be a root user to start, and to be switched later to a specific user and group. We need to tell it not to expect this, or our application will get stuck in the starting up phase. To do this, we add the following section to the app service in our docker-compose.yml.
```
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
```
This is basically the same command as we saw the the app Dockerfile, but by placing it in the docker-compose, the uWSGI container begins expecting to be a non-root user.

### Starting A Stack
Our docker-compose.yml is now complete, and we can start up our stack on Spin with rancher. First, make sure you are in the right directory- this should be the directory containing your docker-compose.yml, and the directory should be the same name as the stack you want to run. See [Spin naming conventions](https://docs.nersc.gov/services/spin/best_practices/#naming-convention-for-stacks). Validate your docker-compose.yml for any syntax errors:
```
user@cori01:SPIN_DIRECTORY $ rancher up --render
```
If everything seems ok, this should print out the contents of the file. If not, it will point to the error. Once everything is all squared away, we can start the stack:
```
user@cori01:SPIN_DIRECTORY $ rancher up -d
```
The `-d` flag runs everything in the background, so the logs don't get printed to the console, and you can do other stuff without exiting the running process. If you do want to check the logs for a service, you can call:
```
user@cori01:SPIN_DIRECTORY $ rancher logs service-name --follow --tail 100
```
The `--follow` tag will print the logs out realtime to the console, while the `--tail` option will only print out the last, in this case 100, lines of the log. 
If everything is in order, then calling
```rancher ps```
should return that both of our services, app and web, are healthy. In order to visit them, you can check where they are being hosted:
```
rancher inspect your-stack-name/web | jq '.fqdn'
```
Which should return a name like web.stack-name.dev.stable.spin.nersc.org:{your external nginx port}, which you can navigate to in your browser. Or, you can use the IP address (although this changes periodically, the url is more reliable). To check the port or the IP address, you can use:
```
rancher inspect your-stack-name/web | jq '.publicEndpoints'
[
  {
    "hostId": "1h83",
    "instanceId": "1i2601738",
    "ipAddress": "128.55.206.19",
    "port": 60000,
    "serviceId": "1s4783",
    "type": "publicEndpoint"
  }
]
```
If everything went properly, you should see the nightly calendar pop up when you navigate to the address, and voilà!

## Some Useful Tips and Tricks
These are just a mix of things I learned that were useful while trying to get this to work.
