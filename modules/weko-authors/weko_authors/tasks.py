# -*- coding: utf-8 -*-
#
# This file is part of WEKO3.
# Copyright (C) 2017 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# WEKO3 is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with WEKO3; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.

"""WEKO3 authors tasks."""
import os
import glob
from datetime import datetime, timezone
from time import sleep

from celery import shared_task, states
from celery.result import GroupResult
from celery.task.control import inspect
from flask import current_app
from weko_workflow.utils import delete_cache_data, get_cache_data

from weko_authors.config import WEKO_AUTHORS_IMPORT_CACHE_KEY

from .utils import export_authors, import_author_to_system, save_export_url, \
    set_export_status


@shared_task
def export_all():
    """Export all creator."""
    try:
        start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        set_export_status(start_time=start_time)
        file_uri = export_authors()
        if file_uri:
            end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_export_url(start_time, end_time, file_uri)

        return file_uri
    except Exception as ex:
        current_app.logger.error(ex)


@shared_task
def import_author(author):
    """Import Author."""
    result = {'start_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    try:
        import_author_to_system(author)
        result['status'] = states.SUCCESS
    except Exception as ex:
        current_app.logger.error(ex)
        result['status'] = states.FAILURE
        if ex.args and len(ex.args) and isinstance(ex.args[0], dict) \
                and ex.args[0].get('error_id'):
            error_msg = ex.args[0].get('error_id')
            result['error_id'] = error_msg

    result['end_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return result

@shared_task
def import_author_over_max(reached_point, item_count, task_ids ,max_part):
    """
    WEKO_AUTHORS_IMPORT_MAX_NUM_OF_DISPLAYSを超えた著者をインポートする場合の処理です。
    先に行っているインポートタスクが終了次第、reached_pointから一時ファイルを用いて
    著者インポートを開始します。
    Args:
        reached_point: 一時ファイルにおいてmax_displayに達した位置 
                part_numberが一時ファイルのpart数で、countが一時ファイルの再開位置
                データ例:{"part_number": 101, "count": 3}
        count: インポートする著者データの数.
        task_ids: 先に行っているmax_diplay分のタスクID.
    """
    from .utils import get_check_base_name
    from invenio_cache import current_cache
    import gc, json
    from weko_workflow.utils import update_cache_data
    max_display = current_app.config.get("WEKO_AUTHORS_IMPORT_MAX_NUM_OF_DISPLAYS")
    
    # 最初はmax_displayの500で割った秒数だけ待つ
    sleep(max_display//500)
    
    # task_idsの全てのtaskが終了するまで待つ
    check_task_end(task_ids)
    del task_ids
    gc.collect()

    # 結果ファイルのDL用に一時ファイルを作成
    temp_folder_path = current_app.config.get("WEKO_AUTHORS_IMPORT_TEMP_FOLDER_PATH")
    result_file_download_name = "{}_{}.{}".format(
        "import_author_result",
        datetime.datetime.now().strftime("%Y%m%d%H%M"),
        "tsv"
    )
    
    result_file_path = os.path.join(temp_folder_path, result_file_download_name)
    check_file_name = get_check_base_name()
    update_cache_data(
        current_app.config["WEKO_AUTHORS_IMPORT_CACHE_RESULT_OVER_MAX_FILE_PATH_KEY"],
        result_file_path,
        current_app.config["WEKO_AUTHORS_IMPORT_TEMP_FILE_RETENTION_PERIOD"]
    )
    current_cache.get(current_app.config["WEKO_AUTHORS_IMPORT_CACHE_RESULT_OVER_MAX_FILE_PATH_KEY"])
    # すべてのtaskが終了したら、max_display以降のtaskを実行
    # part_numberから始めて、max_partまでのpartをインポートする。
    authors = []
    for i in range(reached_point.get("part_number"), max_part+1):
        part_check_file_name = f"{check_file_name}-part{i}"
        check_file_part_path = os.path.join(temp_folder_path, part_check_file_name)

        #一時ファイルからインポートできるファイルを取得
        with open(check_file_part_path, "r", encoding="utf-8-sig") as check_part_file:
            data = json.load(check_part_file)
            for index, item in enumerate(data):
                # max_display以降のところまで飛ばす
                if i == reached_point.get("part_number") and index < reached_point.get("count"):
                    continue
                check_result = False if item.get("errors", []) else True
                if check_result:
                    item.pop("warnings", None)
                    item.pop("is_deleted", None)
                    authors.append(item)
                    
        # authorsが長さWEKO_AUTHORS_IMPORT_BATCH_SIZEを超えた時点でインポート
        if len(authors) >= current_app.config.get("WEKO_AUTHORS_IMPORT_BATCH_SIZE"):
            import_authors_for_over_max(authors)
            authors = []
    # authorsが残っている場合
    if authors:
        import_authors_for_over_max(authors)
        
    # 一時ファイルの削除
    
    
    
    
def import_authors_for_over_max(authors):
    import gc
    from celery import group
    group_tasks = []
    tasks = []
    task_ids = []
    for author in authors:
        group_tasks.append(import_author.s(author))

    # group_tasksを実行
    import_task = group(group_tasks).apply_async()
    import_task.save()
    for idx, task in enumerate(import_task.children):                
        full_name_info =""
        # フルネーム生成
        for author_name_info in authors[idx].get("authorNameInfo", [{}]):
            family_name = author_name_info.get("familyName", "")
            first_name = author_name_info.get("firstName", "")
            full_name = f"{family_name},{first_name}"
            if len(full_name)!=1:
                if len(full_name_info)==0:
                    full_name_info += full_name
                else:
                    full_name_info += f"\n{full_name}"
        tasks.append({
            'task_id': task.task_id,
            'weko_id': authors[idx].get('pk_id'),
            'full_name': full_name_info,
            'status': 'PENDING'
        })
        task_ids.append(task.task_id)
        
    # task_idsの全てのtaskが終了するまで待つ
    check_task_end(task_ids)
    del task_ids
    gc.collect()
    
    count = 0
    result = []
    for _task in tasks:
        task = import_author.AsyncResult(_task['task_id'])
        start_date = ""
        end_date = ""
        if task.result:
            start_date = task.result.get('start_date', '')
            end_date = task.result.get('end_date', '')
        status = states.PENDING
        error_id = None
        if task.result and task.result.get('status'):
            status = task.result.get('status')
            error_id = task.result.get('error_id')
        result.append({
            "start_date": start_date,
            "end_date": end_date,
            "weko_id": _task['weko_id'],
            "full_name": _task['full_name'],
            "status": status,
            "error_id": error_id
        })
        task.forget()
    del tasks
    # TODO インポート結果を一時ファイルに書き込む処理
    # write_temp_file(result)
    # TODO インポート結果をサマリーに追加する処理
    authors = []
    gc.collect()


# 3秒ごとにtask_idsを確認し、全てのtaskが終了したらループを抜ける
def check_task_end(task_ids):
    max_display = current_app.config.get("WEKO_AUTHORS_IMPORT_MAX_NUM_OF_DISPLAYS")
    while True:
        count = 0
        for task_id in task_ids:
            task = import_author.AsyncResult(task_id)
            if task.result:
                end_date = task.result.get('end_date')
            else:
                end_date = None
            if end_date:
                count += 1
        if count == max_display:
            break
        else:
            sleep(3)
    return 0

def check_is_import_available(group_task_id=None):
    """Is import available."""
    result = {
        'is_available': True
    }

    if not inspect(timeout=current_app.config.get("CELERY_GET_STATUS_TIMEOUT", 3.0)).ping():
        result['is_available'] = False
        result['celery_not_run'] = True
    else:
        cache_data = get_cache_data(WEKO_AUTHORS_IMPORT_CACHE_KEY)
        if cache_data:
            task = GroupResult.restore(cache_data.get('group_task_id'))
            if task:
                if task.successful() or task.failed():
                    delete_cache_data(WEKO_AUTHORS_IMPORT_CACHE_KEY)
                else:
                    result['is_available'] = False
                    if group_task_id and group_task_id == task.id:
                        result['continue_data'] = cache_data
            else:
                delete_cache_data(WEKO_AUTHORS_IMPORT_CACHE_KEY)

    return result

@shared_task(ignore_result=True)
def check_tmp_file_time_for_author():
    """Check the storage time of the author temp file."""
    path = '/var/tmp'
    # 1日
    ttl = 24* 60* 60 
    author_export_temp_dirc_path = path + "/authors_export"
    author_import_temp_dirc_path = path + "/authors_import"
    author_export_temp_file_path = path + "/authors_export/**"
    author_import_temp_file_path = path + "/authors_import/**"
    
    now = datetime.now(timezone.utc) 
    # 著者エクスポートの一時ファイルの削除
    for d in glob.glob(author_export_temp_file_path):
        tLog = os.path.getmtime(d)
        if (now - datetime.fromtimestamp(tLog, timezone.utc)).total_seconds() >= ttl:
            try:
                os.remove(d)
            except OSError as e:
                current_app.logger.error(e)
    # ディレクトリが空かどうかを確認し、空の場合はディレクトリを削除
    if os.path.exists(author_export_temp_dirc_path) and \
        not os.listdir(author_export_temp_file_path):
        os.rmdir(author_export_temp_file_path)
                
    # 著者インポートの一時ファイルの削除
    for d in glob.glob(author_import_temp_file_path):
        tLog = os.path.getmtime(d)
        if (now - datetime.fromtimestamp(tLog, timezone.utc)).total_seconds() >= ttl:
            try:
                os.remove(path)
            except OSError as e:
                current_app.logger.error(e)
    # ディレクトリが空かどうかを確認し、空の場合はディレクトリを削除
    if os.path.exists(author_import_temp_dirc_path) and \
        not os.listdir(author_import_temp_file_path):
        os.rmdir(author_import_temp_file_path)