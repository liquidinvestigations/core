FROM python:3.7-stretch

RUN mkdir -p /app
WORKDIR /app

ADD requirements.txt ./
RUN pip install -r requirements.txt

ENV DJANGO_SETTINGS_MODULE liquidcore.site.settings.docker_local
COPY . .

VOLUME /app/var
ENV PYTHONUNBUFFERED 1
CMD ./manage.py initialize && ./manage.py runserver 0.0.0.0:8000
