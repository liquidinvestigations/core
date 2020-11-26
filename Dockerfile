FROM python:3.8-buster

RUN set -e \
 && apt-get update \
 && apt-get install -y --no-install-recommends sqlite3 \
 && apt-get update && apt-get install -y gosu \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

ARG USER_NAME=liquid
ARG UID=666
ARG GID=666
RUN groupadd -g $GID -o $USER_NAME
RUN useradd -m -u $UID -g $GID -o -s /bin/bash $USER_NAME

RUN mkdir -p /app
WORKDIR /app

ADD Pipfile Pipfile.lock ./
RUN set -e \
 && pip install pipenv \
 && pipenv install --system --deploy --ignore-pipfile

ADD liquidcore ./liquidcore
ADD manage.py dockercmd ./
ADD docker-entrypoint.sh ./

ENV PYTHONUNBUFFERED 1

ENV DATA_DIR "/app/var"
ENV USER_NAME $USER_NAME
ENV UID $UID
ENV GID $GID

VOLUME /app/var

RUN SECRET_KEY=x ./manage.py collectstatic

ENTRYPOINT ["/app/docker-entrypoint.sh"]

CMD /app/dockercmd
