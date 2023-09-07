FROM python:3.11-bullseye

RUN set -e \
 && apt-get update \
 && apt-get install -y --no-install-recommends sqlite3 git wget \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN wget https://raw.githubusercontent.com/first20hours/google-10000-english/d0736d492489198e4f9d650c7ab4143bc14c1e9e/google-10000-english-no-swears.txt -O /google-10000-english-no-swears.txt

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
