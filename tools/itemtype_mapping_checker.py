# -*- coding: utf-8 -*-
"""
ログ例
* データベース名,アイテムタイプ名,アイテムタイプID,修正対象のプロパティ名(key)
"""
import csv, json, psycopg2, sys, traceback
from os import getenv
from os.path import dirname, join

def get_connection(db_name):
    return psycopg2.connect(
        database=db_name,
        user=getenv('INVENIO_POSTGRESQL_DBUSER'),
        password=getenv('INVENIO_POSTGRESQL_DBPASS'),
        host=getenv('INVENIO_POSTGRESQL_HOST'),
        port=5432,
        connect_timeout=10
    )

def check_mapping(db_list):
    try:
        for db_name in db_list:
            update_logs = []
            with get_connection(db_name) as conn, conn.cursor() as cur:
                cur.execute("SELECT item_type_id,jsonb_path_query(mapping,'$.*.jpcoar_mapping.**.\@value') FROM item_type_mapping WHERE id IN (SELECT max(id) as id FROM item_type_mapping GROUP BY item_type_id);")
                results = cur.fetchall()
                for ret in results:
                    item_type_id = ret[0]
                    list = str(ret[1]).split(".")
                    cur.execute("SELECT count(id) FROM item_type_property WHERE schema::text like '%{}%'".format(list[-1]))
                    counts = cur.fetchall()
                    count = int(counts[0][0])
                    if count == 0:
                        print("{}:{}:{}:{}".format(db_name,item_type_id,list[-1],count))
                
                cur.execute("SELECT item_type_id,jsonb_path_query(mapping,'$.*.jpcoar_mapping.**.\@attributes.*') FROM item_type_mapping WHERE id IN (SELECT max(id) as id FROM item_type_mapping GROUP BY item_type_id);")
                results = cur.fetchall()
                for ret in results:
                    item_type_id = ret[0]
                    list = str(ret[1]).split(".")
                    cur.execute("SELECT count(id) FROM item_type_property WHERE schema::text like '%{}%'".format(list[-1]))
                    counts = cur.fetchall()
                    count = int(counts[0][0])
                    if count == 0:
                        print("{}:{}:{}:{}".format(db_name,item_type_id,list[-1],count))
                

    except:
        print(f'ERROR: {traceback.print_exc()}')

if __name__ == '__main__':
    db_list = [getenv('INVENIO_POSTGRESQL_DBNAME')]
    check_mapping(db_list)
