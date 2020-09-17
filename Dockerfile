FROM python:3.8-buster

RUN set -e \
 && apt-get update \
 && apt-get install -y --no-install-recommends sqlite3 \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /app
WORKDIR /app

ADD Pipfile Pipfile.lock ./
RUN set -e \
 && pip install pipenv \
 && pipenv install --system --deploy --ignore-pipfile

ADD liquidcore ./liquidcore
ADD manage.py dockercmd ./

ENV PYTHONUNBUFFERED 1
VOLUME /app/var

RUN SECRET_KEY=x ./manage.py collectstatic

CMD ./dockercmd
