FROM python:3.7-stretch

RUN mkdir -p /app
WORKDIR /app

ADD Pipfile Pipfile.lock ./
RUN set -e \
 && pip install pipenv \
 && pipenv install --system --deploy --ignore-pipfile

COPY . .

ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE liquidcore.site.settings.docker_local

VOLUME /app/var

CMD ./manage.py initialize && ./manage.py runserver 0.0.0.0:8000
