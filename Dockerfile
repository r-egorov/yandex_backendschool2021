FROM python:3.9-slim-buster

MAINTAINER Ruslan Egorov 'ch-isis@ya.ru'

COPY . /srv/flask_app

WORKDIR /srv/flask_app
RUN apt-get clean \
    && apt-get -y update

RUN apt-get -y install nginx \
    && apt-get -y install python3-dev \
    && apt-get -y install build-essential

RUN pip install -r requirements.txt

COPY configs/nginx.conf /etc/nginx
RUN chmod +x ./start.sh

EXPOSE 8000

CMD ["./start.sh"]
