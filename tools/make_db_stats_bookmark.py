import os
import sys
import json
from datetime import datetime
import requests
from requests.auth import HTTPBasicAuth
import psycopg2
import psycopg2.extras
from uuid import uuid4
import hashlib

args = sys.argv
args = sys.argv
if len(args) == 4:
    http_method = "https" if args[1] == "https" else "http"
    user = args[2]
    password = args[3]
    auth = HTTPBasicAuth(user,password)
elif len(args) == 2:
    http_method = "https" if args[1] == "https" else "http"
    auth = None
else:
    print("Usage: python reindex_all_index.py [http_method] [user] [password]")
    sys.exit(1)

ES_HOST = os.environ.get('INVENIO_ELASTICSEARCH_HOST','localhost')
ES_PORT = 9200
ES_VERIFY = False

DB_HOST = os.environ['INVENIO_POSTGRESQL_HOST']
DB_PORT = 5432
DB_DATABASE = os.environ['INVENIO_POSTGRESQL_DBNAME']
DB_USER = os.environ['INVENIO_POSTGRESQL_DBUSER']
DB_PASSWORD = os.environ['INVENIO_POSTGRESQL_DBPASS']

search_query = {"query": {"match_all": {}}}
stats_bookmark_index = os.environ.get('SEARCH_INDEX_PREFIX')+"-stats-bookmarks"
search_url = f"{http_method}://{ES_HOST}:9200/{stats_bookmark_index}/_search"
req_args = {"headers":{"Content-Type":"application/json"},"verify":ES_VERIFY}
if auth:
    req_args["auth"] = auth

result = requests.get(search_url,json=search_query,**req_args)
if result.status_code == 200:
    result = result.json()
else:
    print("# Elasticsearch search failed.: {}".format(result.text))
    sys.exit(1)

stats_bookmark_documents = result["hits"]["hits"]

def _generate_id():
    """Generate identifier.
    :return:
    """
    current_time = datetime.utcnow().isoformat()
    return str(str(uuid4()) + \
        hashlib.sha1(current_time.encode("utf-8")).hexdigest())

num_trans=0
with psycopg2.connect(host=DB_HOST, port=DB_PORT, database=DB_DATABASE, user=DB_USER, password=DB_PASSWORD) as conn:
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        try:
            for doc in stats_bookmark_documents:
                source_id =doc["_id"]
                index = doc["_index"]
                type = doc["_type"]
                source = doc["_source"]
                if "timestamp" in source:
                    date = source["timestamp"]
                elif "date" in source:
                    date = source["date"]

                query = u"INSERT INTO stats_bookmark (id, source_id, index, type, source, date, created, updated) "\
                    "VALUES ('{id}', '{source_id}', '{index}', '{type}', '{source}', '{date}', '{created}', '{updated}') "\
                    "ON CONFLICT ON CONSTRAINT uq_stats_key_stats_bookmark "\
                    "DO UPDATE SET "\
                    "source = EXCLUDED.source;".format(
                        id=_generate_id(),
                        source_id=source_id,
                        index=index,
                        type=type,
                        source=json.dumps(source),
                        date=date,
                        created=date, # 完全な代替項目が存在しないため、source["date"]で代用
                        updated=date # 完全な代替項目が存在しないため、source["date"]で代用
                    )
                cur.execute(
                    query
                )
                num_trans+=1
            conn.commit()
            print("# success transfer {} records".format(num_trans))
        except Exception as e:
            print("# raise error")
            import traceback
            print(traceback.format_exc())
            conn.rollback()