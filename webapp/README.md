# Running A Containerized Nightwatch 
This tutorial will go through the process of running Nightwatch with Rancher2 on Spin, in addition to documenting the configurations and default images built for Nightwatch.

#### Useful resources:
- Spin has some tutorials if you want to go through [building a Docker image](https://docs.nersc.gov/services/spin/getting_started/lesson-1/). As of 08/20, there aren't any tutorials I could find going through how to use Kubernetes or Rancher2 (besides the training for Spin users).

- [Rancher2 documentation](https://rancher.com/docs/rancher/v2.x/en/).

- [Kubernetes documentation](https://kubernetes.io/docs/home/).

- [Docker documentation](https://docs.docker.com/).

- [uWSGI documentation](https://uwsgi-docs.readthedocs.io/en/latest/index.html).

- [Flask documentation](https://flask.palletsprojects.com/en/1.1.x/).

## Contents
- [General Structure](#general-structure) 
- [Configuring the base image](#configuring-the-base-image)
- [Building and Shipping Images to NERSC](#building-and-shipping-images-to-nersc)
  - [Building new images](#building-new-images)
  - [Ship images to NERSC registry](#ship-images-to-spin)
- [Running At NERSC (Spin and Rancher)](#running-at-nersc)
- [Rancher2 + Kubernetes Troubleshooting](#rancher2--kubernetes-troubleshooting)

## General Structure
Rancher2 uses Kubernetes instead of Docker, so the structure of the web app is slightly different than previously (see documentation in /docker-rancher1 folder); instead of writing a docker-compose.yml file to specify the interaction between a uWSGI-flask container (the app) and a nginx container (server interfacing with internet), we will write a kubernetes deployment yaml file that configures one container/workload, and a separate yaml file to configure a load-balancer/ingress, which will act in the same way our nginx docker container did. We can do much of this “writing” through the rancher2 GUI. 

## Configuring Images
Generally, it shouldn't be necessary to modify the base Docker image, but this section will document the Dockerfile and specific configurations in case modifications need to be made, or you want to build one of your own. However, because we are mounting the nightwatch webapp code, it will be necessary to rebuild the image in the case a new page is added, or new interactive functions are added to Nightwatch. It will also be necessary to re-build the image if we need to update any of the dependencies to a new version, or add new ones (as we want to build all dependencies into the image itself).

### uWSGI
The full dockerfile for the uWSGI/Flask app image:
```
FROM python:3

WORKDIR /app
ENV PYTHONPATH ${PYTHONPATH}:./nightwatch/py
ENV PYTHONPATH ${PYTHONPATH}:./desimodel/py
ENV PYTHONPATH ${PYTHONPATH}:./desiutil/py
ADD . /app
RUN pip install -r requirements.txt
EXPOSE 5000

ENTRYPOINT [ "uwsgi" ]
CMD [ "--ini", "app.ini"]
```
The first line tells Docker which image the new image is based off of- in general, this should be a standardized, well-maintained image, to ensure greatest stability. The next line creates a directory *inside* the container, in which we will mount all of our external files. The `ENV` lines add our desi models to the pythonpath inside the container, and the `ADD` line copies the files in the same directory as the docker file to the container. In this case, that was the requirements.txt file, the app.py code, and the uWSGI config file app.ini. Requirements.txt contains all of the dependencies we need to run the app. These requirements get installed in the next `RUN` line. All the needed files are contained in the /Dockerfiles folder. `EXPOSE` tells the container to expose port 5000, on which the app will listen for requests from the user. The final two lines tell the container how to start up the application, with the entrypoint `uwsgi` and the arguments `"--ini app.ini --pyargv -s ./static -d ./data`. These tell uWSGI to look for the app.ini file for configurations, as well as to pass the `pygarv` arguments into the Flask app.

#### uWSGI Configuration
The uWSGI image also contains an app.ini file with uWSGI specific configurations:
```
[uwsgi]
protocol = http
module = app
callable = app
master = true
pyargv = "webapp -i ./static -d ./data"

processes = 5
single-interpreter = true

http-socket = :5000
vacuum = true

die-on-term = true
```
See the [uWSGI documentation](https://uwsgi-docs.readthedocs.io/en/latest/CustomOptions.html) if you want to learn more about the specific options here. The version of the app.ini file in this repo also contains some more details on these configs.

## Building and Shipping Images to NERSC
### Building New Images
First, you need to set up a working directory to store all the files needed for the build, and create the Dockerfile that will provide the instructions for the image. You can just use the /Dockerfile subdirectory located in the same directory as this README, as it already contains all the files needed to build a copy of the uwsgi-flask Nightwatch image. Note, if you are re-building this image to include an update to the webapp code, make sure that the version of app.py you are building into the image is also updated. Now you can run this command from inside the /Dockerfiles directory:

```
user@localmachine:Dockerfiles $ docker image build --tag [image-name-here] .
```
The `--tag` flag allows you to give a name to your image, and the last argument defines which directory Docker should look for the Dockerfile and other files it needs to build the image (here, it is set to the directory we are already in). Now, if you run `docker image list [image-name]` you should see the new container listed. 

### Ship Images to Spin
Once you're happy with the image, you need to publish it to the NERSC registry to be able to use it at Spin (rancher1 or rancher2). First, we need to tag the image properly on our local machine:
```
user@laptop: $ docker image list [image-name]
REPOSITORY              TAG     IMAGE ID      CREATED            SIZE
my-first-container-app  latest  c4f1cd0eb01c  About an hour ago  165MB
user@laptop: $ docker image tag [image-name] registry.nersc.gov/desi/[namespace]/[image-name]:[version]
```
The namespace should be nightwatch, but you can also create a new one. You can name the version whatever you want, but if this is an update to the nightwatch webapp image, you should tag it latest. Now, if you list the images again, you should see an additional image with the same ID, but with a different name. Now, login to the Spin registry with your NERSC username and password:
```
user@laptop: $ docker login https://registry.nersc.gov/
Username:
Password:
Login Succeeded
user@laptop: $
```
Then, push your image to the registry, but with the relevant info replaced in the brackets.
```
user@laptop: $ docker image push registry.spin.nersc.gov/desi/[namespace]/[image-name]:[version]
```
If the version is "latest", DON'T include it in the push. Otherwise, do include the version name. Now, the images are available to be pulled in the rancher environment, and we can start up an application stack at NERSC.

## Running at NERSC
See the Rancher2Docs.pdf document for a step-by-step walkthrough of using Rancher2 to set up a Nightwatch web service.

## Rancher2 + Kubernetes Troubleshooting
These are a couple of the things I noticed were most likely to have gone wrong when I was trying to get Nightwatch up and running.

 1. **NERSC security requirements:** Make sure that you have the correct security configurations: all capabilities dropped except for "NET_BIND_SERVICE". Otherwise the pod will not be able to run.
 2. **User permissions:** Make sure that you didn't specify the group or user id in the command, but instead in the specified boxes. Often this is an issue if you have uWSGI problems; when uWSGI starts up it will say "running as root" or "unable to set GID as current user".
 3. **uWSGI loading app correctly:** If the app.py code isn't configured correctly, uWSGI won't be able to load it properly. You might see an error that says uWSGI was unable to find a mountpoint, or no module was found. Make sure that the app.py code isn't wrapped in a function (as it needs to be for running it as a plain Flask webapp, not a containerized service), and make sure that the uWSGI app.ini config file module:callable argument references the same name as the Flask app code itself.
 4. **Read Only permissions:** If you are unable to access the live interactive features, like the image downsampling or the spectra plotting, you might have specified the static directory to be read only; this is the only volume we DON'T want to be read only, as the app needs to be able to write new files to that directory.
