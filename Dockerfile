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

# Use Python-3.6:
FROM python:3.6-slim-buster as stage_1

# Configure Weko instance:
ENV INVENIO_WEB_HOST=127.0.0.1
ENV INVENIO_WEB_INSTANCE=invenio
ENV INVENIO_WEB_VENV=invenio
ENV INVENIO_WEB_HOST_NAME=invenio
ENV INVENIO_USER_EMAIL=wekosoftware@nii.ac.jp
ENV INVENIO_USER_PASS=uspass123
ENV INVENIO_POSTGRESQL_HOST=postgresql
ENV INVENIO_POSTGRESQL_DBNAME=invenio
ENV INVENIO_POSTGRESQL_DBUSER=invenio
ENV INVENIO_POSTGRESQL_DBPASS=dbpass123
ENV INVENIO_REDIS_HOST=redis
ENV INVENIO_ELASTICSEARCH_HOST=elasticsearch
ENV INVENIO_RABBITMQ_HOST=rabbitmq
ENV INVENIO_RABBITMQ_USER=guest
ENV INVENIO_RABBITMQ_PASS=guest
ENV INVENIO_RABBITMQ_VHOST=/
ENV INVENIO_WORKER_HOST=127.0.0.1
ENV SEARCH_INDEX_PREFIX=tenant1
ENV INVENIO_WEB_PROTOCOL=https
ENV CACHE_REDIS_DB=0
ENV ACCOUNTS_SESSION_REDIS_DB_NO=1
ENV CELERY_RESULT_BACKEND_DB_NO=2
ENV WEKO_AGGREGATE_EVENT_HOUR=0
ENV WEKO_AGGREGATE_EVENT_MINUTE=0

# Configure SQLAlchemy connection pool
# see: https://docs.sqlalchemy.org/en/12/core/pooling.html#api-documentation-available-pool-implementations
ENV INVENIO_DB_POOL_CLASS=QueuePool

FROM stage_1 AS stage_2
# Install Weko web node pre-requisites:
COPY scripts/provision-web.sh /tmp/
RUN /tmp/provision-web.sh

FROM stage_2 AS stage_3
# Add Weko sources to `code` and work there:
WORKDIR /code
RUN adduser --uid 1000 --disabled-password --gecos '' invenio
USER invenio
COPY --chown=invenio:invenio scripts /code/scripts
COPY --chown=invenio:invenio tools /code/tools
COPY --chown=invenio:invenio modules /code/modules
COPY --chown=invenio:invenio packages.txt /code/packages.txt
COPY --chown=invenio:invenio packages-invenio.txt /code/packages-invenio.txt
COPY --chown=invenio:invenio requirements-weko-modules.txt /code/requirements-weko-modules.txt
COPY --chown=invenio:invenio invenio /code/invenio
COPY --chown=invenio:invenio postgresql /code/postgresql

FROM stage_3 AS stage_4
# Create Weko instance:
RUN chmod +x /code/scripts/create-instance.sh;/code/scripts/create-instance.sh



FROM stage_4 AS stage_5
# Create Weko instance2:
USER invenio
WORKDIR /code
COPY --chown=invenio:invenio scripts/instance.cfg /code/scripts/instance.cfg
RUN chmod +x /code/scripts/create-instance2.sh;/code/scripts/create-instance2.sh

FROM stage_5 AS build-env
# Make given VENV default:
ENV PATH=/home/invenio/.virtualenvs/invenio/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
#ENV VIRTUALENVWRAPPER_PYTHON=/usr/local/bin/python
ENV VIRTUALENVWRAPPER_PYTHON=/home/invenio/.virtualenvs/invenio/bin/python
#RUN echo "source /usr/local/bin/virtualenvwrapper.sh" >> ~/.bashrc ; echo "workon invenio" >> ~/.bashrc
RUN pip install virtualenvwrapper
RUN echo "source /home/invenio/.virtualenvs/invenio/bin/virtualenvwrapper.sh" >> ~/.bashrc ; echo "workon invenio" >> ~/.bashrc

RUN mv /home/invenio/.virtualenvs/invenio/var/instance/static /home/invenio/.virtualenvs/invenio/var/instance/static.org

# CMD ["/bin/bash", "-c", "gunicorn invenio_app.wsgi --workers=4 --worker-class=meinheld.gmeinheld.MeinheldWorker -b 0.0.0.0:5000 "]
#CMD ["/bin/bash","-c","uwsgi --ini /code/scripts/uwsgi.ini"]
CMD ["/bin/bash", "-c", "invenio run -h 0.0.0.0"]

# FROM python:3.6-slim-buster as product-base
# RUN apt-get -y update --allow-releaseinfo-change;apt-get -y --no-install-recommends install curl rlwrap screen vim gnupg libpcre3 libffi6 libfreetype6 libmsgpackc2 libssl1.1 libtiff5 libxml2 libxslt1.1 libzip4 nodejs libpq5 default-jre libreoffice-java-common libreoffice fonts-ipafont fonts-ipaexfont git
# COPY --from=build-env /usr/bin /usr/bin
# COPY --from=build-env /usr/lib/node_modules /usr/lib/node_modules
# RUN adduser --uid 1000 --disabled-password --gecos '' invenio
# USER invenio
# WORKDIR /code
# COPY --from=build-env --chown=invenio:invenio /code /code
# COPY --from=build-env --chown=invenio:invenio /home/invenio/.virtualenvs /home/invenio/.virtualenvs
#RUN mv /home/invenio/.virtualenvs/invenio/var/instance/static /home/invenio/.virtualenvs/invenio/var/instance/static.org
# CMD ["/bin/bash"]
# CMD ["/bin/bash", "-c", "invenio run -h 0.0.0.0"]

# FROM python:3.6-slim-buster as product-env
# # Configure Weko instance:
# ENV INVENIO_WEB_HOST=127.0.0.1
# ENV INVENIO_WEB_INSTANCE=invenio
# ENV INVENIO_WEB_VENV=invenio
# ENV INVENIO_WEB_HOST_NAME=invenio
# ENV INVENIO_USER_EMAIL=wekosoftware@nii.ac.jp
# ENV INVENIO_USER_PASS=uspass123
# ENV INVENIO_POSTGRESQL_HOST=postgresql
# ENV INVENIO_POSTGRESQL_DBNAME=invenio
# ENV INVENIO_POSTGRESQL_DBUSER=invenio
# ENV INVENIO_POSTGRESQL_DBPASS=dbpass123
# ENV INVENIO_REDIS_HOST=redis
# ENV INVENIO_ELASTICSEARCH_HOST=elasticsearch
# ENV INVENIO_RABBITMQ_HOST=rabbitmq
# ENV INVENIO_RABBITMQ_USER=guest
# ENV INVENIO_RABBITMQ_PASS=guest
# ENV INVENIO_RABBITMQ_VHOST=/
# ENV INVENIO_WORKER_HOST=127.0.0.1
# ENV SEARCH_INDEX_PREFIX=tenant1
# # Configure SQLAlchemy connection pool
# # see: https://docs.sqlalchemy.org/en/12/core/pooling.html#api-documentation-available-pool-implementations
# ENV INVENIO_DB_POOL_CLASS=QueuePool

# RUN apt-get -y update && apt-get -y install curl nano default-jre libreoffice libreoffice-java-common fonts-ipafont fonts-ipaexfont --no-install-recommends && apt-get -y clean && pip install -U setuptools pip virtualenvwrapper && adduser --uid 1000 --disabled-password --gecos '' invenio
# USER invenio
# COPY --from=build-env --chown=invenio:invenio /home/invenio/.virtualenvs /home/invenio/.virtualenvs
# COPY --from=build-env --chown=invenio:invenio /code /code
# COPY --from=build-env /usr/bin /usr/bin

# ENV PATH=/home/invenio/.virtualenvs/invenio/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
# ENV VIRTUALENVWRAPPER_PYTHON=/usr/local/bin/python
# RUN echo "source /usr/local/bin/virtualenvwrapper.sh" >> ~/.bashrc && echo "workon invenio" >> ~/.bashrc
# WORKDIR /code

# CMD ["/bin/bash", "-c", "invenio run -h 0.0.0.0"]


