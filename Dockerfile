FROM python:3.7-stretch

RUN mkdir -p /app
WORKDIR /app

ADD Pipfile Pipfile.lock ./
RUN set -e \
 && apt-get update \
 && apt-get install -y --no-install-recommends qrencode \
 && apt-get clean && rm -rf /var/lib/apt/lists/* \
 && pip install pipenv \
 && pipenv install --system --deploy --ignore-pipfile

ADD liquidcore ./liquidcore
ADD manage.py dockercmd ./

ENV PYTHONUNBUFFERED 1
VOLUME /app/var

RUN LIQUID_TITLE=x LIQUID_DOMAIN=x SECRET_KEY=x ./manage.py collectstatic

CMD ./dockercmd
