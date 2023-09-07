FROM python:3.11-bullseye

RUN set -e \
 && apt-get update \
 && apt-get install -y --no-install-recommends sqlite3 git wbritish-small \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /app
WORKDIR /app

ADD Pipfile Pipfile.lock ./
RUN set -e \
 && pip install pipenv \
 && pipenv install --system --deploy --ignore-pipfile

ADD liquidcore ./liquidcore
ADD manage.py dockercmd .git/ ./

ENV PYTHONUNBUFFERED 1
ENV OTEL_TRACES_EXPORTER=none OTEL_METRICS_EXPORTER=none OTEL_LOGS_EXPORTER=none
VOLUME /app/var

RUN SECRET_KEY=x ./manage.py collectstatic

CMD ./dockercmd
