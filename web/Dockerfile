FROM python:2.7

RUN mkdir -p /usr/src/app && mkdir -p /mnt/logs
WORKDIR /usr/src/app

ADD requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

VOLUME /usr/src/app
