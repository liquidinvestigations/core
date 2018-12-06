FROM python:3.7-stretch

RUN mkdir -p /app
WORKDIR /app

ADD requirements.txt ./
RUN pip install -r requirements.txt

COPY . .
COPY liquidcore/site/settings/docker_local.py liquidcore/site/settings/local.py

ENV PYTHONUNBUFFERED 1

#ADD https://github.com/ufoscout/docker-compose-wait/releases/download/2.3.0/wait /wait
# RUN ./manage.py collectstatic --noinput

VOLUME /app/var

CMD ./manage.py initialize && ./manage.py runserver 0.0.0.0:8000
