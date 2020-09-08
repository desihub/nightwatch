FROM python:3

WORKDIR /app
ENV PYTHONPATH ${PYTHONPATH}:./nightwatch/py
ENV PYTHONPATH ${PYTHONPATH}:./desimodel/py
ENV PYTHONPATH ${PYTHONPATH}:./desiutil/py
ADD . /app
RUN pip3 install -r requirements.txt
EXPOSE 5000

ENTRYPOINT [ "uwsgi" ]
CMD [ "--ini", "app.ini"]