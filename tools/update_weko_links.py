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
        PersistentIdentifier.status == 'R'
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
                                or_(
                                    (PersistentIdentifier.pid_value == str(recid)),
                                    (PersistentIdentifier.pid_value == f"{recid}.0")
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
                            and_(
                                Activity.action_status != 'F',
                                Activity.action_status != 'C'
                            ),
                            and_(
                                Activity.temp_data != None,
                                Activity.temp_data != {}
                            )
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


def get_working_activity_ids():
    """
    登録途中のワークフローのアクティビティIDのリストを取得します。

    Returns:
        list: Activityテーブルのid（アクティビティID）のリスト
    """
    # item_idがNoneかつtemp_dataがNoneでないActivity.idのリストを取得
    query = Activity.query.filter(
        Activity.item_id.is_(None),
        Activity.temp_data != None
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


def main(batch_size=500):
    """Main context.
    Args:
        batch_size: int
            一度に処理するアイテム数
    """
    # アイテムメタデータおよび編集中ワークフローのtemp_dataを更新する
    update_records_metadata(batch_size)

    # 登録途中のワークフローのtemp_dataを更新する
    update_workflow_activities(batch_size)


if __name__ == '__main__':
    starttime = datetime.now()
    current_app.logger.info(f"{starttime.isoformat()} - Starting update_weko_links.py")

    main()

    endtime = datetime.now()
    current_app.logger.info(f"{endtime.isoformat()} - Finished update_weko_links.py")
    current_app.logger.info(f"Duration: {endtime - starttime}")