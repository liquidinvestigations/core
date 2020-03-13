FROM python:3.8-buster

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

RUN LIQUID_TITLE=x LIQUID_DOMAIN=x SECRET_KEY=x ./manage.py collectstatic

CMD ./dockercmd
