FROM python:2.7

RUN mkdir -p /usr/src/app && mkdir -p /mnt/logs
WORKDIR /usr/src/app

ADD requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

VOLUME /usr/src/app

CMD python manage.py db upgrade && /usr/local/bin/gunicorn -w 2 -b :8000 app:app --reload --access-logfile /tmp/access.log --error-logfile  /tmp/error.log
