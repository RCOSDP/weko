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
FROM python:3.6-slim as stage_1

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
ADD scripts /code/scripts
ADD modules /code/modules
ADD packages.txt /code/packages.txt
ADD packages-invenio.txt /code/packages-invenio.txt
ADD requirements-weko-modules.txt /code/requirements-weko-modules.txt
ADD invenio /code/invenio

FROM stage_3 AS stage_4
# Run container as user `weko` with UID `1000`, which should match
# current host user in most situations:
RUN adduser --uid 1000 --disabled-password --gecos '' invenio && \
    chown -R invenio:invenio /code
USER invenio

FROM stage_4 AS stage_5
# Create Weko instance:
RUN chmod +x /code/scripts/create-instance.sh
RUN /code/scripts/create-instance.sh

FROM stage_5 AS stage_6
# Create Weko instance2:
WORKDIR /code
ADD scripts/instance.cfg /code/scripts/instance.cfg
RUN chmod +x /code/scripts/create-instance2.sh
RUN /code/scripts/create-instance2.sh

FROM stage_6 AS stage_7
# Make given VENV default:
ENV PATH=/home/invenio/.virtualenvs/invenio/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ENV VIRTUALENVWRAPPER_PYTHON=/usr/local/bin/python
RUN echo "source /usr/local/bin/virtualenvwrapper.sh" >> ~/.bashrc
RUN echo "workon invenio" >> ~/.bashrc
#RUN mv /home/invenio/.virtualenvs/invenio/var/instance/static /home/invenio/.virtualenvs/invenio/var/instance/static.org

FROM stage_7 AS stage_8
# Start the Weko application:
CMD ["/bin/bash", "-c", "invenio run -h 0.0.0.0"]
# CMD ["/bin/bash", "-c", "gunicorn invenio_app.wsgi --workers=4 --worker-class=meinheld.gmeinheld.MeinheldWorker -b 0.0.0.0:5000 "]
#CMD ["/bin/bash","-c","uwsgi --ini /code/scripts/uwsgi.ini"]
