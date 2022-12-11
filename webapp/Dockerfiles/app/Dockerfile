FROM python:3.9

WORKDIR /app
ENV PYTHONPATH ${PYTHONPATH}:./nightwatch/py
ENV PYTHONPATH ${PYTHONPATH}:./desimodel/py
ENV PYTHONPATH ${PYTHONPATH}:./desiutil/py
ADD ./webapp/Dockerfiles/app /app
COPY ./py/nightwatch /app/nightwatch
RUN apt update && apt install -y python3-pandas
RUN cat requirements.txt  | xargs -n 1 pip install
EXPOSE 5000

ENTRYPOINT [ "uwsgi" ]
CMD [ "--ini", "app.ini"]
