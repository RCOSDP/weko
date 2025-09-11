FROM python:3.9-slim

RUN pip3 install tavern
RUN pip3 install beautifulsoup4
RUN pip3 install psycopg2-binary

RUN apt-get -y update && apt-get -y install curl

WORKDIR /tavern