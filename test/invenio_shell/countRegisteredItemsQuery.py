"""
公開アイテム数
非公開アイテム数
チェック用クエリ生成プログラム

トータルの計算には問題がある。

docker-compose exec web invenio shell code/test/invenio_shell/countRegistereditemsQuery.py

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

        print(u"SELECT COUNT(DISTINCT id) as registered_items FROM records_metadata WHERE id IN (SELECT object_uuid FROM pidstore_pid WHERE pid_type='parent' and status='R');")
        print(u"SELECT COUNT(DISTINCT id) as private_oai_items FROM records_metadata WHERE id IN (SELECT object_uuid FROM pidstore_pid WHERE pid_type='parent' and status='R') AND ((" +
              " OR ".join(unpublish_oai_cond) + ") OR (json->>'publish_status'='1' OR (json->>'publish_date')::date >= now()));")
        print(u"SELECT COUNT(DISTINCT id) as public_oai_items FROM records_metadata WHERE id IN (SELECT object_uuid FROM pidstore_pid WHERE pid_type='parent' and status='R') AND json->>'publish_status'='0'  AND (json->>'publish_date')::date < now() AND ("+" AND ".join(unpublish_oai_cond2) + ");")

        """ select private indices on the GUI"""
        cur.execute(
            u"SELECT id FROM index WHERE (public_state = False OR (public_date>=now()));")
        for row in cur:
            unpublish_index.append(row[0])
            unpublish_cond.append(
                "json->>'path' ~ '.*(\"|/)+"+str(row[0])+"(\"|/)+.*'")
            unpublish_cond2.append(
                "json->>'path' !~ '.*(\"|/)+"+str(row[0])+"(\"|/)+.*'")

        print(u"SELECT COUNT(DISTINCT id) as private_items FROM records_metadata WHERE id IN (SELECT object_uuid FROM pidstore_pid WHERE pid_type='parent' and status='R') AND ((" +
              " OR ".join(unpublish_cond) + ") OR (json->>'publish_status'='1' OR (json->>'publish_date')::date >= now()));")
        print(u"SELECT COUNT(DISTINCT id) as public_items FROM records_metadata WHERE id IN (SELECT object_uuid FROM pidstore_pid WHERE pid_type='parent' and status='R') AND json->>'publish_status'='0'  AND (json->>'publish_date')::date < now() AND ("+" AND ".join(unpublish_cond2) + ");")
