# -*- coding: utf-8 -*-
#
# This file is part of WEKO3.
# Copyright (C) 2017 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# WEKO3 is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with WEKO3; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.

# Use Python-3.5:
#FROM ubuntu:18.04
FROM python:3.5 as web_base



# Install Weko web node pre-requisites:
# OPY scripts/provision-web.sh /tmp/
# RUN /tmp/provision-web.sh

RUN apt-get -y update --allow-releaseinfo-change && apt-get -y upgrade && apt-get -y install \
         curl \
         git \
         rlwrap \
         screen \
         vim \
         gnupg \
         gcc \
         g++ \
         make \
         libffi-dev \
         libfreetype6-dev \
         libjpeg-dev \
         libmsgpack-dev \
         libssl-dev \
         libtiff-dev \
         libxml2-dev \
         libxslt-dev \
         libzip-dev \
         libjpeg-dev \
         libtiff-dev \
         imagemagick \
         libopenjp2-7-dev \
         libimagequant-dev \
         libmagickwand-dev \
         libwebp-dev \
         libraqm-dev \
         zlib1g-dev \
         libpng-dev \
         python3-dev \
         python3-pip \
         libpq-dev \
         fonts-ipafont \
         fonts-ipaexfont \
         openjdk-11-jre-headless
RUN apt-get -y update --allow-releaseinfo-change && apt-get -y upgrade && apt-get -y install libreoffice-core --no-install-recommends

RUN bash -c "if [[ ! -f /etc/apt/sources.list.d/nodesource.list ]]; then curl -sL https://deb.nodesource.com/setup_4.x |bash -;fi"
#RUN bash -c "if [[ ! -f /etc/apt/sources.list.d/nodesource.list ]]; then curl -sL https://deb.nodesource.com/setup_12.x |bash -;fi"
RUN apt-get -y update && apt-get -y install nodejs npm
RUN printf "\nPackage: *\nPin: origin deb.nodesource.com\nPin-Priority: 600" >> /etc/apt/preferences.d/nodesource
RUN npm config set user 0
RUN npm config set unsafe-perm true
RUN npm install -g node-sass@3.8.0 clean-css@3.4.12 requirejs uglify-js
RUN pip install -U setuptools pip
RUN pip install -U virtualenvwrapper
RUN if ! grep -q virtualenvwrapper ~/.bashrc; then mkdir -p "$HOME/.virtualenvs" & echo "export WORKON_HOME=$HOME/.virtualenvs" >> "$HOME/.bashrc" & echo "source $(which virtualenvwrapper.sh)" >> "$HOME/.bashrc" ;fi
RUN export WORKON_HOME=$HOME/.virtualenvs
RUN bash -c "source \"$(which virtualenvwrapper.sh)\""
RUN apt-get -y autoremove && $sudo apt-get -y clean


#FROM python:3.5-slim
#COPY --from=web_base /usr/ /usr/
#COPY --from=web_base /lib/ /lib/
#COPY --from=web_base /lib/ /lib/

#COPY --from=web_base /usr/bin /usr/bin
#COPY --from=web_base /usr/lib /usr/lib
#COPY --from=web_base /usr/share /usr/share
#COPY --from=web_base /usr/include /usr/include
#COPY --from=web_base /usr/local/bin /usr/local/bin
#COPY --from=web_base /usr/local/lib /usr/local/lib

# Configure Weko instance:
ENV INVENIO_WEB_HOST=127.0.0.1
ENV INVENIO_WEB_INSTANCE=invenio
ENV INVENIO_WEB_VENV=invenio
ENV INVENIO_USER_EMAIL=wekosoftware@nii.ac.jp
ENV INVENIO_USER_PASS=uspass123
ENV INVENIO_POSTGRESQL_HOST=postgresql
ENV INVENIO_POSTGRESQL_DBNAME=invenio
ENV INVENIO_POSTGRESQL_DBUSER=invenio
ENV INVENIO_POSTGRESQL_DBPASS=dbpass123
ENV INVENIO_REDIS_HOST=redis
ENV INVENIO_ELASTICSEARCH_HOST=elasticsearch
ENV INVENIO_RABBITMQ_HOST=rabbitmq
ENV INVENIO_WORKER_HOST=127.0.0.1
ENV SEARCH_INDEX_PREFIX=tenant1

# Add Weko sources to `code` and work there:
WORKDIR /code
ADD . /code

# Run container as user `weko` with UID `1000`, which should match
# current host user in most situations:
RUN adduser --uid 1000 --disabled-password --gecos '' invenio && \
    chown -R invenio:invenio /code
USER invenio

# Create Weko instance:
RUN /code/scripts/create-instance.sh

# Make given VENV default:
ENV PATH=/home/invenio/.virtualenvs/invenio/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ENV VIRTUALENVWRAPPER_PYTHON=/usr/local/bin/python
RUN echo "source /usr/local/bin/virtualenvwrapper.sh" >> ~/.bashrc
RUN echo "workon invenio" >> ~/.bashrc


#WORKDIR /code
#ADD . /code

# Start the Weko application:
CMD ["/bin/bash", "-c", "invenio run -h 0.0.0.0"]
# CMD ["/bin/bash", "-c", "gunicorn invenio_app.wsgi --workers=4 --worker-class=meinheld.gmeinheld.MeinheldWorker -b 0.0.0.0:5000 "]
#CMD ["/bin/bash","-c","uwsgi --ini /code/scripts/uwsgi.ini"]
