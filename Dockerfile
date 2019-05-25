FROM python:3.7-stretch

RUN mkdir -p /app
WORKDIR /app

ADD Pipfile Pipfile.lock ./
RUN set -e \
 && pip install pipenv \
 && pipenv install --system --deploy --ignore-pipfile

ADD liquidcore ./liquidcore
ADD manage.py ./

ENV PYTHONUNBUFFERED 1
VOLUME /app/var

CMD ./manage.py initialize && waitress-serve --port 8000 liquidcore.site.wsgi:application
