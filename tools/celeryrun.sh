#!/usr/bin/env bash

#celery worker -A invenio_app.celery --loglevel=DEBUG -B -D -f /code/celeryd.log
celery worker -A invenio_app.celery --loglevel=DEBUG -B -D -f /code/celeryd.log --concurrency=5
