# -*- coding: utf-8 -*-
# Copyright (c) 2017 National Institute of Informatics.
#
# Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this list of conditions
#  and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions
#  and the following disclaimer in the documentation and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products
#  derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
# INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
# EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


# Use Python-3.6:
FROM python:3.6-slim-buster AS stage_1

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
COPY --chown=invenio:invenio tika /code/tika

FROM stage_3 AS stage_4
# Create Weko instance:
RUN chmod +x /code/scripts/create-instance.sh && /code/scripts/create-instance.sh

FROM stage_4 AS stage_5
# Create Weko instance2:
USER invenio
WORKDIR /code
COPY --chown=invenio:invenio scripts/instance.cfg /code/scripts/instance.cfg
RUN chmod +x /code/scripts/create-instance2.sh && /code/scripts/create-instance2.sh

FROM stage_5 AS build-env
# Make given VENV default:
ENV PATH=/home/invenio/.virtualenvs/invenio/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ENV VIRTUALENVWRAPPER_PYTHON=/home/invenio/.virtualenvs/invenio/bin/python
RUN pip install virtualenvwrapper
RUN echo "source /home/invenio/.virtualenvs/invenio/bin/virtualenvwrapper.sh" >> ~/.bashrc ; echo "workon invenio" >> ~/.bashrc
#RUN mv /home/invenio/.virtualenvs/invenio/var/instance/static /home/invenio/.virtualenvs/invenio/var/instance/static.org
USER root
RUN chown -R invenio:invenio /code
USER invenio

RUN rm -rf /home/invenio/.cache/pip /home/invenio/.cache/npm /home/invenio/.npm || true
RUN find /home/invenio/.virtualenvs/invenio -type d -name __pycache__ -prune -exec rm -rf {} + \
    && find /home/invenio/.virtualenvs/invenio -type f -name "*.pyc" -delete

# Runtime image with only required libs and prebuilt venv/code
FROM python:3.6-slim-buster AS runtime

# Configure Weko instance (keep in sync with build stages)
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
ENV INVENIO_DB_POOL_CLASS=QueuePool

# Optional runtime features (set to 0 to skip)
ARG WITH_LIBREOFFICE=1
ARG WITH_JRE=1
ARG WITH_JA_FONTS=1

# Install runtime libraries only (no build tools)
# buster is archived; update apt sources to archive mirrors
RUN sed -i 's/deb.debian.org/archive.debian.org/g' /etc/apt/sources.list && \
    sed -i 's/security.debian.org/archive.debian.org/g' /etc/apt/sources.list && \
    apt-get -y update --allow-releaseinfo-change && \
    apt-get -y install --no-install-recommends \
        libpq5 \
        libxml2 \
        libxslt1.1 \
        libffi6 \
        libssl1.1 \
        libjpeg62-turbo \
        libfreetype6 \
        libtiff5 \
        libzip4 \
        libpcre3 \
        supervisor \
        ca-certificates \
    && apt-get -y autoremove && apt-get -y clean \
    && rm -rf /var/lib/apt/lists/*

# Optional packages (kept separate to allow build-time toggles)
RUN set -eux; \
    apt-get -y update --allow-releaseinfo-change; \
    if [ "${WITH_JRE}" = "1" ]; then \
        apt-get -y install --no-install-recommends default-jre; \
    fi; \
    if [ "${WITH_LIBREOFFICE}" = "1" ]; then \
        apt-get -y install --no-install-recommends libreoffice-java-common libreoffice; \
    fi; \
    if [ "${WITH_JA_FONTS}" = "1" ]; then \
        apt-get -y install --no-install-recommends fonts-ipafont fonts-ipaexfont; \
    fi; \
    apt-get -y autoremove && apt-get -y clean; \
    rm -rf /var/lib/apt/lists/*

# Optional Node.js + webassets filters (set to 0 to skip in worker)
ARG WITH_NODE=1
RUN set -eux; \
    if [ "${WITH_NODE}" = "1" ]; then \
        apt-get -y update --allow-releaseinfo-change; \
        apt-get -y install --no-install-recommends curl; \
        curl -fsSL https://deb.nodesource.com/setup_16.x | bash -; \
        apt-get -y update --allow-releaseinfo-change; \
        apt-get -y install --no-install-recommends nodejs; \
        npm install -g node-sass@9.0.0 clean-css@3.4.12 requirejs uglify-js; \
        npm cache clean --force; \
        rm -rf /root/.npm; \
        apt-get -y purge --auto-remove curl; \
        apt-get -y autoremove && apt-get -y clean; \
        rm -rf /var/lib/apt/lists/*; \
    fi

RUN adduser --uid 1000 --disabled-password --gecos '' invenio
COPY --from=build-env /home/invenio/.virtualenvs/invenio /home/invenio/.virtualenvs/invenio
COPY --from=build-env /code /code
RUN chown -R invenio:invenio /code /home/invenio/.virtualenvs/invenio

# Make given VENV default:
ENV PATH=/home/invenio/.virtualenvs/invenio/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ENV VIRTUALENVWRAPPER_PYTHON=/home/invenio/.virtualenvs/invenio/bin/python
WORKDIR /code
USER invenio

# CMD ["/bin/bash", "-c", "gunicorn invenio_app.wsgi --workers=4 --worker-class=meinheld.gmeinheld.MeinheldWorker -b 0.0.0.0:5000 "]
#CMD ["/bin/bash","-c","uwsgi --ini /code/scripts/uwsgi.ini"]
CMD ["/bin/bash", "-c", "invenio run -h 0.0.0.0"]
