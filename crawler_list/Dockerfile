
FROM python:3.7

WORKDIR /usr/src/app/

COPY . .

RUN pip3 install redis

RUN pip3 install sqlalchemy

RUN pip3 install requests

RUN pip3 install psycopg2

ENV INVENIO_POSTGRESQL_HOST=postgresql

ENV INVENIO_POSTGRESQL_DBNAME=invenio

ENV INVENIO_POSTGRESQL_DBPASS=dbpass123

ENV INVENIO_POSTGRESQL_DBUSER=invenio

CMD ["python", "app.py"]