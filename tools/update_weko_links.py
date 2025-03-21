# -*- coding: utf-8 -*-
"""
weko_linkを作成するスクリプト
records_metadataのauthor_linkからweko_linkを作成し、records_metadataを更新する。
workflow_activityのtemp_dataからweko_linkを作成し、workflow_activityを更新する。
"""

import csv, json, psycopg2, sys, traceback
from os import getenv


def get_connection(db_name):
    return psycopg2.connect(
        database=db_name,
        user=getenv('INVENIO_POSTGRESQL_DBUSER'),
        password=getenv('INVENIO_POSTGRESQL_DBPASS'),
        host=getenv('INVENIO_POSTGRESQL_HOST'),
        port=5432,
        connect_timeout=10
    )
    
def update_records_metadata(db_list):
    try:
        for db_name in db_list:
            update_logs = []
            with get_connection(db_name) as conn, conn.cursor() as cur:
                # records_metadataを更新する。
                cur.execute("""
                    SELECT id, json 
                    FROM records_metadata 
                    WHERE json::jsonb->>'recid' ~ '^[0-9]+$' 
                    OR json::jsonb->>'recid' ~ '\\.0$';
                """)
                results = cur.fetchall()
                for ret in results:
                    id = ret[0]
                    json_data = ret[1]
                    # author_linkからweko_linkを作成
                    if 'author_link' in json_data:
                        author_link = json_data['author_link']
                        weko_link = {str(item): str(item) for item in author_link}
                        json_data['weko_link'] = weko_link
                        # レコードを更新
                        cur.execute("""
                            UPDATE records_metadata
                            SET json = %s
                            WHERE id = %s;
                        """, (json.dumps(json_data), id))
                        update_logs.append((id, json_data))
                        print(f'Updated record id: {id}')
    except:
        print(f'ERROR: {traceback.print_exc()}')
        
def update_workflow_activity(db_list):
    try:
        for db_name in db_list:
            update_logs = []
            with get_connection(db_name) as conn, conn.cursor() as cur:
                # workflow_activityからデータを取得。
                cur.execute("""
                    SELECT id, item_id ,temp_data 
                    FROM workflow_activity 
                    WHERE temp_data IS NOT NULL;
                """)
                results = cur.fetchall()
            for ret in results:
                id = ret[0]
                item_id = ret[1]
                json_str = ret[2]
                # 編集を開始したが、まだ一度もセーブしていないワークフローについての処理
                # item_idが存在する場合は、item_metadataからmetainfoを取得し、weko_linkを作成する
                if json_str == {} and item_id is not None:
                    with get_connection(db_name) as conn, conn.cursor() as cur:
                        print(item_id)
                        cur.execute("""
                            SELECT id, json
                            FROM item_metadata 
                            WHERE id = %s;
                        """, (item_id,))
                        item_metadata = cur.fetchone()
                        json_data = {}
                        json_data["metainfo"] = item_metadata[1]
                        weko_link = get_weko_link(json_data)
                        json_data['weko_link'] = weko_link
                        # レコードを更新
                        cur.execute("""
                            UPDATE workflow_activity
                            SET temp_data = to_jsonb(CAST(%s AS text))
                            WHERE id = %s;
                        """, (json.dumps(json_data), id))
                        
                        print(f'Updated workflow id: {id}')
                # 編集を開始して、セーブしてあるtemp_dataが存在するワークフローについての処理
                elif isinstance(json_str, str):
                    json_data = json.loads(json_str)
                    weko_link = get_weko_link(json_data)
                    json_data['weko_link'] = weko_link
                    # レコードを更新
                    with get_connection(db_name) as conn, conn.cursor() as cur:
                        cur.execute("""
                            UPDATE workflow_activity
                            SET temp_data = to_jsonb(CAST(%s AS text))
                            WHERE id = %s;
                        """, (json.dumps(json_data, ensure_ascii=False), id))
                    update_logs.append((id, json_data))
                    print(f'Updated workflow id: {id}')
    except:
        print(f'ERROR: {traceback.print_exc()}')

def get_weko_link(metadata):
    """
    メタデータからweko_idを取得し、weko_idを使って
    weko_linkを作成します。
    args
        metadata: dict 
        例：{
                "metainfo": {
                    "item_30002_creator2": [
                        {
                            "nameIdentifiers": [
                                {
                                    "nameIdentifier": "8",
                                    "nameIdentifierScheme": "WEKO",
                                    "nameIdentifierURI": ""
                                }
                            ]
                        }
                    ]
                },
                "files": [],
                "endpoints": {
                    "initialization": "/api/deposits/items"
                }
            }
    return
        weko_link: dict
        例：{"2": "10002"}
    """
    weko_link = {}
    weko_id_list=[]
    for x in metadata["metainfo"].values():
        if not isinstance(x, list):
            continue
        for y in x:
            if not isinstance(y, dict):
                continue
            for key, value in y.items():
                if not key == "nameIdentifiers":
                    continue
                for z in value:
                    if z.get("nameIdentifierScheme","") == "WEKO":
                        if z.get("nameIdentifier","") not in weko_id_list:
                            weko_id_list.append(z.get("nameIdentifier"))
    weko_link = {}
    for weko_id in weko_id_list:
        weko_link[weko_id] = weko_id
    return weko_link

if __name__ == '__main__':
    db_list = [getenv('INVENIO_POSTGRESQL_DBNAME')]
    update_records_metadata(db_list)
    update_workflow_activity(db_list)