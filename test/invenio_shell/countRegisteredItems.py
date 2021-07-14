"""

公開アイテム数
非公開アイテム数
チェックプログラム

トータルの計算には問題がある。

docker-compose exec web invenio shell code/test/invenio_shell/countRegistereditems.py

"""
import os
import warnings

import psycopg2
import psycopg2.extras

warnings.simplefilter('ignore', DeprecationWarning)
warnings.simplefilter('ignore', UserWarning)

unpublish_oai_index = []
unpublish_oai_cond = []
unpublish_oai_cond2 = []
total_items = []
private_oai_items = []
public_oai_items = []

unpublish_index = []
unpublish_cond = []
unpublish_cond2 = []
private_items = []
public_items = []

HOST = os.environ['INVENIO_POSTGRESQL_HOST']
PORT = 5432
DATABASE = os.environ['INVENIO_POSTGRESQL_DBNAME']
USER = os.environ['INVENIO_POSTGRESQL_DBUSER']
PASSWORD = os.environ['INVENIO_POSTGRESQL_DBPASS']

with psycopg2.connect(host=HOST, port=PORT, database=DATABASE, user=USER, password=PASSWORD) as conn:
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        """ select private indices on the OAI-PMH protocol"""
        cur.execute(
            u"SELECT id FROM index WHERE (harvest_public_state = False OR public_state = False OR (public_date>=now()));")
        for row in cur:
            unpublish_oai_index.append(row[0])
            unpublish_oai_cond.append(
                "json->>'path' ~ '.*(\"|/)+"+str(row[0])+"(\"|/)+.*'")
            unpublish_oai_cond2.append(
                "json->>'path' !~ '.*(\"|/)+"+str(row[0])+"(\"|/)+.*'")

        """ select registered items on the repository"""
        cur.execute(
            u"SELECT DISTINCT id FROM records_metadata WHERE id IN (SELECT object_uuid FROM pidstore_pid WHERE pid_type='parent' and status='R');")
        for row in cur:
            total_items.append(row[0])

        """ select private items on the OAI-PMH protocol"""
        cur.execute(
            u"SELECT DISTINCT id FROM records_metadata WHERE id IN (SELECT object_uuid FROM pidstore_pid WHERE pid_type='parent' and status='R') AND (("+" OR ".join(unpublish_oai_cond) + ") OR (json->>'publish_status'='1' OR (json->>'publish_date')::date >= now()));")
        for row in cur:
            private_oai_items.append(row[0])

        """ select public items on the OAI-PMH protocol"""
        cur.execute(
            u"SELECT DISTINCT id FROM records_metadata WHERE id IN (SELECT object_uuid FROM pidstore_pid WHERE pid_type='parent' and status='R') AND json->>'publish_status'='0'  AND (json->>'publish_date')::date < now() AND ("+" AND ".join(unpublish_oai_cond2) + ");")
        for row in cur:
            public_oai_items.append(row[0])

        """ select private indices on the GUI"""
        cur.execute(
            u"SELECT id FROM index WHERE (public_state = False OR (public_date>=now()));")
        for row in cur:
            unpublish_index.append(row[0])
            unpublish_cond.append(
                "json->>'path' ~ '.*(\"|/)+"+str(row[0])+"%'")
            unpublish_cond2.append(
                "json->>'path' !~ '.*(\"|/)+"+str(row[0])+"(\"|/)+.*'")

        """ select private items on the GUI"""
        cur.execute(
            u"SELECT DISTINCT id FROM records_metadata WHERE id IN (SELECT object_uuid FROM pidstore_pid WHERE pid_type='parent' and status='R') AND (("+" OR ".join(unpublish_cond) + ") OR (json->>'publish_status'='1' OR (json->>'publish_date')::date >= now()));")
        for row in cur:
            private_items.append(row[0])

        """ select public items on the GUI"""
        cur.execute(
            u"SELECT DISTINCT id FROM records_metadata WHERE id IN (SELECT object_uuid FROM pidstore_pid WHERE pid_type='parent' and status='R') AND json->>'publish_status'='0'  AND (json->>'publish_date')::date < now() AND ("+" AND ".join(unpublish_cond2) + ");")
        for row in cur:
            public_items.append(row[0])


print("total: {0}".format(len(total_items)))
print("total2: {0}".format(len(public_items)+len(private_items)))
print("public(oaipmh): {0}".format(len(public_oai_items)))
print("private(oaipmh): {0}".format(len(private_oai_items)))
print("public: {0}".format(len(public_items)))
print("private: {0}".format(len(private_items)))
