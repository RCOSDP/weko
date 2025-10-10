# -*- coding: utf-8 -*-
#
# Copyright (c) 2025 National Institute of Informatics.
# WEKO is free software; you can redistribute it and/or modify it under the
# terms of the MIT License; see LICENSE file for more details.
""" Update weko_link in records_metadata, workflow_activity and Elasticsearch.

Usage:
```
invenio shell tools/update_weko_links.py
```

仕様：
* records_metadata(json), workflow_activity(temp_data) および Elasticsearch(item-v1.0.0) に weko_link を追加する
    * weko_linkは pk_id をキー、WEKOID を値とする辞書型のデータ
        * 改修前（マイグレーション前）は 必ず「pk_id = WEKOID」となる仕様であり、 
          アイテムメタデータ内のauthor_link の配列内にはWEKOIDが登録される仕様となっていた。
          よってマイグレーション時は対象アイテムのメタデータ内のauthor_linkを取得し、
          その各要素をキーおよび値として持つ辞書を作成し、格納すればよい。
        * 例）
            "author_link": ["1", "2", "3", … , "99"]
             ↓
            "weko_link": {"1": "1", "2": "2", "3": "3", ... , "99": "99"}
    * 既に weko_link が存在する場合は追加処理をスキップする
    * 更新処理は invenio(model) を介して行う
    * ES更新処理は実行有無を容易に切り替えられるようにしておく
      他のマイグレーションと併せてリインデックスする場合、当ツールではES更新が不要になる可能性がある
      →現状は `skip_es_update` 変数で切り替え可能としている。実行時引数での切り替えは未実装。
* ツールの実行対象は1機関分のみとする
    * invenio shell でツール起動することを前提とし、
      実行対象機関は当ツールを呼びだすシェル側で選択すること
* エラー発生時
    * アイテム単位で処理できたところまでコミットする
      エラーが発生したアイテムはロールバックし、次のアイテムの処理を行う
      →`db.session.begin_nested()` でネストトランザクションを利用している
* エラー発生後の再実行の際は処理済みのアイテムはスキップされるようにする
    * 前述の通り既に weko_link が存在する場合スキップすることで実現
* ログ出力（標準出力）
    * 開始／終了、処理にかかった時間
    * どこまで処理が進んでいるかが分かるようにする
    * どのアイテムでエラーが発生したかわかるようにする

"""

from datetime import datetime
from operator import or_
import os
import json
import traceback

from elasticsearch import Elasticsearch
from flask import current_app
from invenio_db import db
from invenio_pidstore.models import PersistentIdentifier
from invenio_records.models import RecordMetadata
from sqlalchemy import and_
from weko_deposit.api import WekoIndexer
from weko_workflow.models import Activity

# 後ほどまとめてリインデックスする等でElasticsearchの更新をスキップする場合はTrueに設定
skip_es_update = True

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
            if not isinstance(y, dict) or "nameIdentifiers" not in y:
                continue
            name_identifiers = y["nameIdentifiers"]
            for z in name_identifiers:
                if z.get("nameIdentifierScheme","") == "WEKO" and z.get("nameIdentifier","") not in weko_id_list:
                    weko_id_list.append(z.get("nameIdentifier"))

    weko_link = {}
    for weko_id in weko_id_list:
        weko_link[weko_id] = weko_id
    return weko_link

def update_records_metadata(batch_size=500):
    """
    アイテムメタデータおよび編集中ワークフローのtemp_dataを更新する
    """
    current_app.logger.info(f"  {datetime.now().isoformat()} - Updating records_metadata and workflow_activity...")
    es = Elasticsearch(
            'http://' + os.environ.get('INVENIO_ELASTICSEARCH_HOST', 'localhost') + ':9200')

    # 対象アイテムのrecidのリストを取得

    query = PersistentIdentifier.query.filter(
        PersistentIdentifier.pid_type == 'recid',
        PersistentIdentifier.status == 'R',
        PersistentIdentifier.pid_value.notlike('%.%')
    ).with_entities(PersistentIdentifier.pid_value).statement
    results = db.engine.execution_options(stream_results=True).execute(query)
    recids = [r[0] for r in results]

    current_app.logger.info(f"  {datetime.now().isoformat()} - Found {len(recids)} recids to process.")

    pages = [recids[i:i + batch_size] for i in range(0, len(recids), batch_size)]

    for page in pages:
        current_app.logger.info(f"  Processing page {pages.index(page) + 1}/{len(pages)}...")
        for recid in page:
            try:
                current_app.logger.info(f"  Processing recid: {recid}")

                # ==ネストトランザクション開始：アイテム毎にコミットする==
                with db.session.begin_nested():
                    # 最新バージョンおよび x.0 の　records_metadata を更新する
                    # recid または recid.0 のレコードを取得
                    record_metadata_records = RecordMetadata.query.filter(
                        RecordMetadata.id.in_(
                            db.session.query(PersistentIdentifier.object_uuid).filter(
                                PersistentIdentifier.pid_type == 'recid',
                                PersistentIdentifier.pid_value.in_(
                                    [str(recid), f"{recid}.0"]
                                )
                            )
                        )
                    ).all()
                    current_app.logger.info(f"    Found {len(record_metadata_records)} records_metadata entries to process.")

                    for record in record_metadata_records:
                        # records_metadata の weko_link を更新する
                        json_data = {**record.json}
                        item_id = record.id
                        weko_link = {}
                        if 'weko_link' in json_data:
                            # すでにweko_linkが存在するrecords_metadataはスキップ
                            weko_link = json_data['weko_link']
                            current_app.logger.info(f'    weko_link already exists, skipping update records_metadata item_id: {item_id}')
                            pass
                        else:
                            if 'author_link' in json_data:
                                # author_linkからweko_linkを作成
                                """
                                weko_linkは pk_id をキー、WEKOID を値とする辞書型のデータ
                                    例：{"2": "10002"}

                                改修前（マイグレーション前）は 必ず「pk_id = WEKOID」となる仕様であり、
                                アイテムメタデータ内のauthor_link の配列内にはWEKOIDが登録される仕様となっていた。
                                よってマイグレーション時は対象アイテムのメタデータ内のauthor_linkを取得し、
                                その各要素をキーおよび値として持つ辞書を作成し、格納すればよい。
                                    例：author_link = [ "2", "3" ]
                                        → weko_link = { "2": "2", "3": "3" }
                                """
                                author_link = json_data['author_link']
                                weko_link = {str(item): str(item) for item in author_link}
                                json_data['weko_link'] = weko_link
                                record.json = json_data
                            else:
                                # author_linkが存在しない場合はweko_linkを空で作成
                                json_data['weko_link'] = weko_link
                                record.json = json_data

                            db.session.merge(record)
                            current_app.logger.info(f'    Updated records_metadata item_id: {item_id}')

                        # 編集中の workflow_activity の temp_data を更新する
                        activities = Activity.query.filter(
                            Activity.item_id == item_id,
                            Activity.action_status.notin_(['F', 'C']),
                            Activity.temp_data.isnot(None),
                            Activity.temp_data != {}
                        ).all()
                        # results = db.engine.execution_options(stream_results=True).execute(query)
                        # activitiy_ids = [r[0] for r in results]
                        current_app.logger.info(f"    Found {len(activities)} workflow_activity entries to process.")
                        for activity in activities:
                            json_str = activity.temp_data
                            if json_str:
                                json_data = json.loads(json_str)
                                if 'weko_link' in json_data:
                                    # すでにweko_linkが存在する場合はスキップ
                                    continue

                                # weko_linkを追加
                                activity_weko_link = get_weko_link(json_data)
                                json_data['weko_link'] = activity_weko_link
                                activity.temp_data = json.dumps(json_data, ensure_ascii=False)

                                db.session.merge(activity)
                                current_app.logger.info(f'    Updated workflow_activity id: {activity.id}')

                        # Elasticsearchにweko_linkを追加する
                        if not skip_es_update:
                            indexer = WekoIndexer()
                            es_metadata = indexer.get_metadata_by_item_id(item_id)
                            if es_metadata and '_source' in es_metadata and 'weko_link' in es_metadata["_source"]:
                                # すでにweko_linkが存在する場合はスキップ
                                pass
                            else:
                                es_version = es_metadata["_version"]
                                es_metadata["_source"]["weko_link"] = weko_link
                                body = {
                                    "doc": {
                                        "_item_metadata": es_metadata["_source"]["_item_metadata"],
                                        "weko_link": es_metadata["_source"]["weko_link"]
                                    }
                                }

                                es.update(
                                    index=es_metadata["_index"], # [prefix]-weko-item-v1.0.0
                                    id=item_id,
                                    doc_type="_doc",
                                    body=body,
                                    version=es_version
                                )
                            current_app.logger.info(f'    Updated Elasticsearch item_id: {item_id}')
                # ==ネストトランザクション終了：アイテム毎にコミットする==

                current_app.logger.info(f'  Finished processing recid: {recid}')

            except Exception as e:
                # エラーが起きたアイテムはロールバックして次に進む
                current_app.logger.error(f'  Error occurred while processing recid: {recid}')
                traceback.print_exc()
                continue

    # 変更をデータベースに保存
    db.session.commit()

    current_app.logger.info(f"  {datetime.now().isoformat()} - Finished updating records_metadata and workflow_activity.")


def bulk_update_records_metadata(batch_size=500):
    """
    bulk update records_metadata and workflow_activity
    Note: This function skipped elasticsearch update.
    
    """
    current_app.logger.info(f"  {datetime.now().isoformat()} - Updating records_metadata and workflow_activity...")

    # get recids which status is 'R' and pid_type is 'recid' and pid_value is base recid (not like %.%)
    query = PersistentIdentifier.query.filter(
        PersistentIdentifier.pid_type == 'recid',
        PersistentIdentifier.status == 'R',
        or_(
            PersistentIdentifier.pid_value.notlike('%.%'),
            PersistentIdentifier.pid_value.like('%.0')
        )
    ).with_entities(PersistentIdentifier.pid_value, PersistentIdentifier.object_uuid).statement
    results = db.engine.execution_options(stream_results=True).execute(query)
    recids = [{
        "pid_value": r[0],
        "object_uuid": r[1]
    } for r in results]

    current_app.logger.info(f"  {datetime.now().isoformat()} - Found {len(recids)} recids to process.")

    bulk_batch_size = batch_size // 3 * 2  # considering recid and recid.0
    recid_chunks = [recids[i:i + bulk_batch_size] for i in range(0, len(recids), bulk_batch_size)]

    for i, recid_chunk in enumerate(recid_chunks):
        current_app.logger.info(f"  Processing page {i + 1}/{len(recid_chunks)}...")
        object_uuids = [item['object_uuid'] for item in recid_chunk]
        # get recid and recid.0
        records_metadata_query = RecordMetadata.query.filter(
            RecordMetadata.id.in_(object_uuids)
        ).with_entities(RecordMetadata.id, RecordMetadata.json, RecordMetadata.version_id).statement
        results = db.engine.execution_options(stream_results=True).execute(records_metadata_query)
        records_metadata_info = {r[0]: (r[1], r[2]) for r in results}

        skipped_record_metadata_ids = []
        bulk_records_metadata_data = []
        for item_id, (json_data, version_id) in records_metadata_info.items():
            current_app.logger.info(f"  Creating new records_metadata id: {item_id}")
            new_record_json = json_data
            if 'weko_link' in json_data:
                # すでにweko_linkが存在するrecords_metadataはスキップ
                skipped_record_metadata_ids.append(item_id)
                current_app.logger.info(f'    weko_link already exists, skipping update records_metadata item_id: {item_id}')
                continue

            if 'author_link' in json_data:
                # author_linkからweko_linkを作成
                """
                weko_linkは pk_id をキー、WEKOID を値とする辞書型のデータ
                    例：{"2": "10002"}

                改修前（マイグレーション前）は 必ず「pk_id = WEKOID」となる仕様であり、
                アイテムメタデータ内のauthor_link の配列内にはWEKOIDが登録される仕様となっていた。
                よってマイグレーション時は対象アイテムのメタデータ内のauthor_linkを取得し、
                その各要素をキーおよび値として持つ辞書を作成し、格納すればよい。
                    例：author_link = [ "2", "3" ]
                        → weko_link = { "2": "2", "3": "3" }
                """
                author_link = json_data["author_link"]
                weko_link = {str(item): str(item) for item in author_link}
                new_record_json["weko_link"] = weko_link
            else:
                # create empty weko_link when author_link not exists
                new_record_json["weko_link"] = {}

            bulk_records_metadata_data.append({
                "id": item_id,
                "json": new_record_json,
                "version_id": version_id
            })

        # check if bulk update data length equal to records length
        if (len(bulk_records_metadata_data) + len(skipped_record_metadata_ids)) != len(records_metadata_info):
            current_app.logger.error("Bulk update data length not equal to records length")
            current_app.logger.error(f"  records length: {len(records_metadata_info)}")
            current_app.logger.error(f"  bulk update data length: {len(bulk_records_metadata_data)}")
            current_app.logger.error(f"  skipped records length: {len(skipped_record_metadata_ids)}")
            raise Exception("Bulk update data length not equal to records length")
        
        # bulk update activities
        activity_query = Activity.query.filter(
            Activity.item_id.in_(list(records_metadata_info.keys())),
            Activity.action_status.notin_(['F', 'C']),
            Activity.temp_data.isnot(None),
            Activity.temp_data != {}
        ).with_entities(Activity.id, Activity.temp_data).statement
        results = db.engine.execution_options(stream_results=True).execute(activity_query)
        activities = {r[0]: r[1] for r in results}

        skipped_activity_ids = []
        new_activities = []
        for activity_id, temp_data in activities.items():
            json_str = temp_data
            if not json_str:
                current_app.logger.info(f'    temp_data is empty, skipping activity id: {activity_id}')
                skipped_activity_ids.append(activity_id)
                continue

            json_data = json.loads(json_str)
            if 'weko_link' in json_data:
                # skip if weko_link already exists
                skipped_activity_ids.append(activity_id)
                current_app.logger.info(f'    weko_link already exists, skipping activity id: {activity_id}')
                continue

            # weko_linkを追加
            activity_weko_link = get_weko_link(json_data)
            json_data['weko_link'] = activity_weko_link
            new_activities.append({
                'id': activity_id,
                'temp_data': json.dumps(json_data, ensure_ascii=False, default=str)
            })
                
        # check if bulk update data length equal to activities length
        if (len(new_activities) + len(skipped_activity_ids)) != len(activities):
            current_app.logger.error("Bulk update data length not equal to activities length")
            current_app.logger.error(f"  activities length: {len(activities)}")
            current_app.logger.error(f"  bulk update data length: {len(new_activities)}")
            current_app.logger.error(f"  skipped activities length: {len(skipped_activity_ids)}")
            raise Exception("Bulk update data length not equal to activities length")

        # transaction start
        with db.session.begin_nested():
            try:
                # bulk update records_metadata
                if bulk_records_metadata_data:
                    db.session.bulk_update_mappings(RecordMetadata, bulk_records_metadata_data)
                    # show bulk update records_metadata ids
                    updated_ids = [r['id'] for r in bulk_records_metadata_data]
                    current_app.logger.info(f'    Updated records_metadata item_ids: {updated_ids}')
                    for i in updated_ids:
                        print(f"[FIX][update_weko_links.py]records_metadata:{i}")
                
                # bulk update activities
                if new_activities:
                    db.session.bulk_update_mappings(Activity, new_activities)
                    # show bulk update activity ids
                    updated_ids = [r['id'] for r in new_activities]
                    current_app.logger.info(f'    Updated workflow_activity ids: {updated_ids}')
                    for i in updated_ids:
                        print(f"[FIX][update_weko_links.py]workflow_activity:{i}")

                current_app.logger.info(f'  Finished processing recids: {recid_chunk}')

            except Exception as e:
                # エラーが起きたアイテムはロールバックして次に進む
                current_app.logger.error(e)
                traceback.print_exc()
                continue

    # 変更をデータベースに保存
    db.session.commit()

    current_app.logger.info(f"  {datetime.now().isoformat()} - Finished updating records_metadata and workflow_activity.")


def get_working_activity_ids():
    """
    登録途中のワークフローのアクティビティIDのリストを取得します。

    Returns:
        list: Activityテーブルのid（アクティビティID）のリスト
    """
    # item_idがNoneかつtemp_dataがNoneでないActivity.idのリストを取得
    query = Activity.query.filter(
        Activity.item_id.is_(None),
        Activity.temp_data.isnot(None)
    ).with_entities(Activity.id).statement
    results = db.engine.execution_options(stream_results=True).execute(query)
    return [r[0] for r in results]

def update_workflow_activities(batch_size=500):
    """
    登録途中のワークフローのtemp_dataを更新する
    """
    current_app.logger.info(f"  {datetime.now().isoformat()} - Updating workflow_activity for in-progress workflows...")
    # 対象アクティビティIDリストを取得
    working_activity_ids = get_working_activity_ids()
    current_app.logger.info(f"  {datetime.now().isoformat()} - Found {len(working_activity_ids)} workflow activities to process.")

    pages = [working_activity_ids[i:i + batch_size] for i in range(0, len(working_activity_ids), batch_size)]

    for page in pages:
        current_app.logger.info(f"  Processing page {pages.index(page) + 1}/{len(pages)}...")
        activities = Activity.query.filter(Activity.id.in_(page)).all()
        for activity in activities:
            try:
                current_app.logger.info(f"  Processing workflow activity id: {activity.id}")
                with db.session.begin_nested():
                    # workflow_activity の temp_data を更新する
                    json_str = activity.temp_data
                    if json_str:
                        json_data = json.loads(json_str)
                        if 'weko_link' in json_data:
                            # すでにweko_linkが存在する場合はスキップ
                            current_app.logger.info(f'    weko_link already exists, skipping activity id: {id}')
                            continue

                        # # weko_linkを追加してコミット
                        weko_link = get_weko_link(json_data)
                        json_data['weko_link'] = weko_link
                        # del json_data['weko_link']  # テスト用にweko_linkを削除
                        activity.temp_data = json.dumps(json_data, ensure_ascii=False)

                        db.session.merge(activity)

                current_app.logger.info(f'    Updated workflow id: {id}')
            except Exception as e:
                # このレコードはロールバックして次に進む
                current_app.logger.error(f'    Error occurred while processing activity id: {id}')
                traceback.print_exc()
                continue

    # 変更をデータベースに保存
    db.session.commit()

    current_app.logger.info(f"  {datetime.now().isoformat()} - Finished updating workflow_activity.")

def bulk_update_workflow_activities(batch_size=500):
    """
    bulk update workflow_activity for in-progress workflows
    Note: This function skipped elasticsearch update.
    
    """
    current_app.logger.info(f"  {datetime.now().isoformat()} - Updating workflow_activity for in-progress workflows...")

    # get working activity ids
    query = Activity.query.filter(
        Activity.item_id.is_(None),
        Activity.temp_data.isnot(None)
    ).with_entities(Activity.id, Activity.temp_data).statement
    results = db.engine.execution_options(stream_results=True).execute(query)
    all_activities = [(r[0], r[1]) for r in results]

    current_app.logger.info(f"  {datetime.now().isoformat()} - Found {len(all_activities)} workflow activities to process.")

    activity_chunks = [all_activities[i:i + batch_size] for i in range(0, len(all_activities), batch_size)]

    for i, activities in enumerate(activity_chunks):
        current_app.logger.info(f"  Processing page {i + 1}/{len(activity_chunks)}...")

        skipped_activity_ids = []
        new_activities = []
        for activity_id, temp_data in activities:
            json_str = temp_data
            if not json_str:
                current_app.logger.info(f'    temp_data is empty, skipping activity id: {activity_id}')
                skipped_activity_ids.append(activity_id)
                continue

            json_data = json.loads(json_str)
            if 'weko_link' in json_data:
                # skip if weko_link already exists
                skipped_activity_ids.append(activity_id)
                current_app.logger.info(f'    weko_link already exists, skipping activity id: {activity_id}')
                continue

            # weko_linkを追加
            activity_weko_link = get_weko_link(json_data)
            json_data['weko_link'] = activity_weko_link
            new_activities.append({
                'id': activity_id,
                'temp_data': json.dumps(json_data, ensure_ascii=False, default=str)
            })
                
        # check if bulk update data length equal to activities length
        if (len(new_activities) + len(skipped_activity_ids)) != len(activities):
            current_app.logger.error("Bulk update data length not equal to activities length")
            current_app.logger.error(f"  activities length: {len(activities)}")
            current_app.logger.error(f"  bulk update data length: {len(new_activities)}")
            current_app.logger.error(f"  skipped activities length: {len(skipped_activity_ids)}")
            raise Exception("Bulk update data length not equal to activities length")
        
        # transaction start
        with db.session.begin_nested():
            try:
                # bulk update activities
                if new_activities:
                    db.session.bulk_update_mappings(Activity, new_activities)
                    # show bulk update activity ids
                    updated_ids = [r['id'] for r in new_activities]
                    current_app.logger.info(f'    Updated workflow_activity ids: {updated_ids}')
                    for i in updated_ids:
                        print(f"[FIX][update_weko_links.py]workflow_activity:{i}")

                current_app.logger.info(f'  Finished processing activities: {[r["id"] for r in activities]}')

            except Exception as e:
                # エラーが起きたアイテムはロールバックして次に進む
                current_app.logger.error(e)
                traceback.print_exc()
                continue

    # commit changes to database
    db.session.commit()

    current_app.logger.info(f"  {datetime.now().isoformat()} - Finished updating workflow_activity.")


def main(batch_size=500):
    """Main context.
    Args:
        batch_size: int
            一度に処理するアイテム数
    """
    # アイテムメタデータおよび編集中ワークフローのtemp_dataを更新する
    # update_records_metadata(batch_size)
    bulk_update_records_metadata(batch_size)

    # 登録途中のワークフローのtemp_dataを更新する
    bulk_update_workflow_activities(batch_size)


if __name__ == '__main__':
    starttime = datetime.now()
    current_app.logger.info(f"{starttime.isoformat()} - Starting update_weko_links.py")

    main()

    endtime = datetime.now()
    current_app.logger.info(f"{endtime.isoformat()} - Finished update_weko_links.py")
    current_app.logger.info(f"Duration: {endtime - starttime}")