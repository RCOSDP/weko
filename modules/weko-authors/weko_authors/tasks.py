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
import gc, json, csv
import sys
import tempfile
import traceback
from datetime import datetime, timezone
from time import sleep

from celery import shared_task, states, group
from celery.result import GroupResult
from celery.task.control import inspect
from flask import current_app
from flask_babelex import lazy_gettext as _
from invenio_cache import current_cache
from weko_logging.activity_logger import UserActivityLogger
from weko_workflow.utils import delete_cache_data, get_cache_data

from sqlalchemy.exc import SQLAlchemyError
from elasticsearch import ElasticsearchException

from weko_authors.config import WEKO_AUTHORS_IMPORT_CACHE_KEY

from .utils import (
    export_authors, import_author_to_system, save_export_url, set_export_status,
    export_prefix, import_id_prefix_to_system, import_affiliation_id_to_system,
    get_check_base_name, handle_exception, update_cache_data
)

@shared_task
def export_all(export_target, user_id):
    """Export all creator."""
    try:
        start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        set_export_status(user_id, start_time=start_time)
        file_uri = None
        if export_target == "author_db":
            file_uri = export_authors(user_id)
        elif export_target == "id_prefix" or export_target == "affiliation_id":
            file_uri = export_prefix(export_target, user_id)
        if file_uri:
            end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_export_url(start_time, end_time, file_uri, user_id)

        return file_uri
    except Exception as ex:
        current_app.logger.error(ex)
        traceback.print_exc(file=sys.stdout)


@shared_task
def import_author(author, force_change_mode, request_info):
    """Import Author.

    Args:
        author (dict): Author data to import.
        force_change_mode (bool): Whether to force change mode.
        request_info (dict): Request information for logging.

    Returns:
        dict: Result of the import operation.

    """
    result = {'start_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    retrys = current_app.config["WEKO_AUTHORS_BULK_EXPORT_MAX_RETRY"]
    interval = current_app.config["WEKO_AUTHORS_BULK_EXPORT_RETRY_INTERVAL"]
    status = author['status']
    weko_id = author['weko_id']
    del author['status']
    del author["weko_id"]
    del author["current_weko_id"]
    try:
        # Retry processing in case of connection error
        for attempt in range(retrys):
            try:
                import_author_to_system(
                    author, status, weko_id, force_change_mode,
                    request_info=request_info
                )
                result['status'] = states.SUCCESS
                break
            except SQLAlchemyError as ex:
                traceback.print_exc(file=sys.stdout)
                handle_exception(ex, attempt, retrys, interval)
            except ElasticsearchException as ex:
                traceback.print_exc(file=sys.stdout)
                handle_exception(ex, attempt, retrys, interval)
            except TimeoutError as ex:
                traceback.print_exc(file=sys.stdout)
                handle_exception(ex, attempt, retrys, interval)
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
def import_id_prefix(prefix):
    """Import ID Prefix.

    Args:
        prefix (dict): id_prefix metadata from tsv/csv.

    Returns:
        dict: Result of the import operation.
    """
    result = {'start_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    try:
        import_id_prefix_to_system(prefix)
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
def import_affiliation_id(affiliation_id):
    """Import Affiliation ID.

    Args:
        affiliation_id (dict): affiliation_id metadata from tsv/csv.

    Returns:
        dict: Result of the import operation.
    """
    result = {'start_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    try:
        import_affiliation_id_to_system(affiliation_id)
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
def import_author_over_max(reached_point, task_ids, max_part, request_info=None):
    """
    Processing for importing authors when exceeding max display.
    After the preceding import tasks are completed, author import will start
    from reached_point using temporary files.

    Args:
        reached_point (dict[str, int]):
            The position in the temporary file where max_display was reached.
                - part_number: the number of parts in the temporary file,
                - count: the restart position in the temporary file.

            Example data: {"part_number": 101, "count": 3}
        task_ids (list): List of task IDs that have been executed before max_display.
        max_part (int): Maximum number of parts.
        request_info (dict): Request information for logging.

    Returns:
        dict: Result of the import operation.
    """

    # Wait until all tasks in task_ids are finished
    check_task_end(task_ids)
    del task_ids
    gc.collect()

    current_app.logger.info('import_author_over_max is start')
    result = {'start_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    try:
        import_authors_from_temp_files(reached_point, max_part, request_info=request_info)
        result['status'] = states.SUCCESS
    except Exception as ex:
        current_app.logger.error(ex)
        traceback.print_exc(file=sys.stdout)
        result['status'] = states.FAILURE
        if ex.args and len(ex.args) and isinstance(ex.args[0], dict) \
                and ex.args[0].get('error_id'):
            error_msg = ex.args[0].get('error_id')
            result['error_id'] = error_msg

    result['end_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    current_app.logger.info('import_author_over_max is end')
    return result


def import_authors_from_temp_files(reached_point, max_part, request_info=None):
    """
    Reads author data from temporary files and imports them.
    Args:
        reached_point (dict[str, int]):
            The position in the temporary file where max_display was reached.
                - part_number: the number of parts in the temporary file,
                - count: the restart position in the temporary file.

            Example data: {"part_number": 101, "count": 3}
        max_part (int): Maximum number of parts.
        request_info (dict): Request information for logging.
    """

    # Create a temporary file for downloading the result file
    temp_folder_path = os.path.join(
        tempfile.gettempdir(),
        current_app.config.get("WEKO_AUTHORS_IMPORT_TMP_DIR")
    )
    result_file_download_name = "{}_{}.{}".format(
        "import_author_result_for_over_max",
        datetime.now().strftime("%Y%m%d%H%M"),
        "tsv"
    )

    result_file_path = os.path.join(temp_folder_path, result_file_download_name)
    check_file_name = get_check_base_name()
    update_cache_data(
        current_app.config["WEKO_AUTHORS_IMPORT_CACHE_RESULT_OVER_MAX_FILE_PATH_KEY"],
        result_file_path,
        current_app.config["WEKO_AUTHORS_CACHE_TTL"]
    )

    # After all tasks are finished, execute tasks after max_display.
    # Start from part_number and import up to max_part.
    authors = []
    for i in range(1, max_part+1):
        part_check_file_name = f"{check_file_name}-part{i}"
        check_file_part_path = os.path.join(temp_folder_path, part_check_file_name)
        # Add authors when i is greater than or equal to reached_point's part_number
        if i >= reached_point.get("part_number"):
            # Get importable files from temporary files
            with open(check_file_part_path, "r", encoding="utf-8-sig") as check_part_file:
                data = json.load(check_part_file)
                for index, item in enumerate(data):
                    # Skip up to the position after max_display
                    if i == reached_point.get("part_number") and index < reached_point.get("count"):
                        continue
                    check_result = False if item.get("errors", []) else True
                    if check_result:
                        item.pop("warnings", None)
                        authors.append(item)
        # Import when authors exceeds WEKO_AUTHORS_IMPORT_BATCH_SIZE
        if len(authors) >= current_app.config.get("WEKO_AUTHORS_IMPORT_BATCH_SIZE"):
            import_authors_for_over_max(authors, request_info=request_info)
            authors = []

        # Delete temporary file
        try:
            os.remove(check_file_part_path)
            current_app.logger.debug(f"Deleted: {check_file_part_path}")
        except Exception as e:
            traceback.print_exc(file=sys.stdout)
            current_app.logger.error(f"Error deleting {check_file_part_path}: {e}")
    # If authors remain
    if authors:
        import_authors_for_over_max(authors, request_info=request_info)
        authors = []
        gc.collect()

def import_authors_for_over_max(authors, request_info=None):
    group_tasks = []
    tasks = []
    task_ids = []
    force_change_mode = current_cache.get(\
        current_app.config.get("WEKO_AUTHORS_IMPORT_CACHE_FORCE_CHANGE_MODE_KEY", False)
        )
    _request_info = request_info or UserActivityLogger.get_summary_from_request()
    if not UserActivityLogger.get_log_group_id(request_info):
        UserActivityLogger.issue_log_group_id(None)
    _request_info["log_group_id"] = UserActivityLogger.get_log_group_id(request_info)

    for author in authors:
        group_tasks.append(import_author.s(author, force_change_mode, _request_info))

    # Execute group_tasks
    import_task = group(group_tasks).apply_async()
    import_task.save()
    for idx, task in enumerate(import_task.children):
        full_name_info =""
        # Generate full name
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
            'record_id': authors[idx].get('pk_id'),
            'previous_weko_id': authors[idx].get('current_weko_id'),
            'new_weko_id': authors[idx].get('weko_id'),
            'full_name': full_name_info,
            'type': authors[idx].get('status'),
            'status': 'PENDING'
        })
        task_ids.append(task.task_id)

    # Wait until all tasks in task_ids are finished
    check_task_end(task_ids)
    del task_ids
    gc.collect()

    success_count = 0
    failure_count = 0
    result = []
    for _task in tasks:
        task = import_author.AsyncResult(_task['task_id'])
        start_date = ""
        end_date = ""
        if task.result:
            start_date = task.result.get('start_date', '')
            end_date = task.result.get('end_date', '')
        error_id = None
        if task.result and task.result.get('status'):
            status = task.result.get('status')
            error_id = task.result.get('error_id')
            if status == states.SUCCESS:
                success_count += 1
            elif status == states.FAILURE:
                failure_count += 1
        # _task here is for tasks that took too long or had some problem.
        else:
            start_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            end_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            status = states.FAILURE
            failure_count += 1
            error_id = _('TimeOut')
        result.append({
            "start_date": start_date,
            "end_date": end_date,
            'previous_weko_id': _task.get('previous_weko_id'),
            'new_weko_id': _task.get('new_weko_id'),
            "full_name": _task['full_name'],
            "type": _task['type'],
            "status": status,
            "error_id": error_id
        })
        # Delete task after completion
        task.forget()
    del tasks
    write_result_temp_file(result)
    # Add import results to summary
    update_summary(success_count, failure_count)

    del authors
    del result
    gc.collect()

def write_result_temp_file(result):
    """Write the result of the task to a temporary file.

    Get the result of the task from the argument result and write it to a temporary file.

    Args:
        result: Contains the result of the task, weko_id, and full_name.

    Example:
        >>> result =  [{
        ...    "start_date": start_date,
                "end_date": end_date,
                "weko_id": 1,
                "full_name": "kimura,shinji",
                "type": "new",
                "status": SUCCESS,
                "error_id": "delete_author_link"
            }, ...]
        >>> write_result_temp_file(result)

    """
    result_file_path = current_cache.get(current_app.config["WEKO_AUTHORS_IMPORT_CACHE_RESULT_OVER_MAX_FILE_PATH_KEY"])
    try:
        with open(result_file_path, "a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file, delimiter='\t')
            for res in result:
                start_date = res.get("start_date", "")
                end_date = res.get("end_date", "")
                prev_weko_id= res.get('previous_weko_id', "")
                new_weko_id= res.get('new_weko_id', "")
                full_name = res.get("full_name", "")
                type = res.get("type", "")
                status = res.get("status", "")
                error_id = res.get("error_id", "")

                msg = prepare_display_status(status, type, error_id)
                writer.writerow(["", start_date, end_date, prev_weko_id, new_weko_id, full_name, msg])


    except Exception as e:
        current_app.logger.error(e)
        traceback.print_exc(file=sys.stdout)
        raise e

def update_summary(success_count, failure_count):
    """Add import results to summary.

    Args:
        success_count: Number of successful imports.
        failure_count: Number of failed imports.
    """
    summary = get_cache_data(current_app.config["WEKO_AUTHORS_IMPORT_CACHE_RESULT_SUMMARY_KEY"])
    if summary:
        summary["success_count"] += success_count
        summary["failure_count"] += failure_count
        update_cache_data(
            current_app.config["WEKO_AUTHORS_IMPORT_CACHE_RESULT_SUMMARY_KEY"],
            summary,
            current_app.config["WEKO_AUTHORS_CACHE_TTL"]
        )
    else:
        summary = {
            "success_count": success_count,
            "failure_count": failure_count
        }
        update_cache_data(
            current_app.config["WEKO_AUTHORS_IMPORT_CACHE_RESULT_SUMMARY_KEY"],
            summary,
            current_app.config["WEKO_AUTHORS_CACHE_TTL"]
        )
    return 0

def prepare_display_status(status, type, error_id):
    msg = ""
    if status == states.SUCCESS:
        msg = prepare_success_msg(type)
    elif status == states.FAILURE:
        msg = _('Error') + ": " + \
            (_('The author is linked to items and cannot be deleted.') \
            if error_id == "delete_author_link" else _('Failed to import.'))
    return msg

def prepare_success_msg(type):
    """Prepare success message based on type.

    Args:
        type (str): Type of success message ('new', 'update', 'deleted').

    Returns:
        str: Success message with translation.
    """
    switcher = {
        'new': _('Register Success'),
        'update': _('Update Success'),
        'deleted': _('Delete Success')
    }
    return switcher.get(type, '')

# Check task_ids every 3 seconds, and exit the loop when all tasks are finished
def check_task_end(task_ids):
    length = len(task_ids)
    sleep_time = current_app.config.get("WEKO_AUTHORS_BULK_IMPORT_RETRY_INTERVAL")
    for i in range(length+10):
        count = 0
        for task_id in task_ids:
            task = import_author.AsyncResult(task_id)
            if task.result:
                end_date = task.result.get('end_date')
            else:
                end_date = None
            if end_date:
                count += 1
        if count == length:
            break
        else:
            sleep(sleep_time)
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
    # 1日
    ttl = current_app.config.get("WEKO_AUTHORS_IMPORT_TEMP_FILE_RETENTION_PERIOD")
    export_temp_dir = os.path.join(
        tempfile.gettempdir(),
        current_app.config.get("WEKO_AUTHORS_EXPORT_TMP_DIR")
    )
    import_temp_dir = os.path.join(
        tempfile.gettempdir(),
        current_app.config.get("WEKO_AUTHORS_IMPORT_TMP_DIR")
    )
    export_temp_file = os.path.join(export_temp_dir, "**")
    import_temp_file = os.path.join(import_temp_dir, "**")

    now = datetime.now(timezone.utc)
    # Delete temporary files for author export
    for d in glob.glob(export_temp_file):
        tLog = os.path.getmtime(d)
        if (now - datetime.fromtimestamp(tLog, timezone.utc)).total_seconds() >= ttl:
            try:
                os.remove(d)
            except OSError as e:
                current_app.logger.error(e)
    # Check if the directory is empty, and if it is, remove the directory
    if (
        os.path.exists(export_temp_dir)
        and not os.listdir(export_temp_file)
    ):
        os.rmdir(export_temp_file)

    # Delete temporary files for author import
    for d in glob.glob(import_temp_file):
        tLog = os.path.getmtime(d)
        if (now - datetime.fromtimestamp(tLog, timezone.utc)).total_seconds() >= ttl:
            try:
                os.remove(d)
            except OSError as e:
                current_app.logger.error(e)
    # Check if the directory is empty, and if it is, remove the directory
    if (
        os.path.exists(import_temp_dir)
        and not os.listdir(import_temp_file)
    ):
        os.rmdir(import_temp_file)
