FROM python:3.7-stretch

RUN mkdir -p /app
WORKDIR /app

ADD requirements.txt ./
RUN pip install -r requirements.txt

COPY . .
COPY liquidcore/site/settings/docker_local.py liquidcore/site/settings/local.py

VOLUME /app/var
ENV PYTHONUNBUFFERED 1
CMD ./manage.py initialize && ./manage.py runserver 0.0.0.0:8000
