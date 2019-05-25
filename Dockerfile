FROM python:3.7-stretch

RUN mkdir -p /app
WORKDIR /app

ADD Pipfile Pipfile.lock ./
RUN set -e \
 && pip install pipenv \
 && pipenv install --system --deploy --ignore-pipfile

COPY liquidcore manage.py ./

ENV PYTHONUNBUFFERED 1
VOLUME /app/var

CMD ./manage.py initialize && ./manage.py runserver 0.0.0.0:8000
