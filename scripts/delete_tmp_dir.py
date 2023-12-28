
import os, sys
import shutil
from datetime import datetime
import traceback
import ast
import glob, re
from celery.task.control import inspect
from weko_redis.redis import RedisConnection
from flask import current_app

glob._ishidden = lambda x: False

def get_tasks():
    """現在実行中、待機中のタスクの取得
    """
    inspector = inspect()
    active_tasks = inspector.active()
    reserved_tasks = inspector.reserved()
    actives= []
    reserveds = []
    tasks = []
    for key in active_tasks:
        actives.extend(active_tasks[key])
        reserveds.extend(reserved_tasks[key])
        tasks.extend(active_tasks[key])
        tasks.extend(reserved_tasks[key])
    
    return tasks, actives, reserveds

def get_temp_dir_info():
    """cache::temp_dir_infoからttlのデータを取得
    """
    key = current_app.config["WEKO_ADMIN_CACHE_TEMP_DIR_INFO_KEY_DEFAULT"]
    redis_connection = RedisConnection()
    sessionstore = redis_connection.connection(db=current_app.config['CACHE_REDIS_DB'])
    result = {}
    for idx, val in sessionstore.hgetall(key).items():
        print("idx:{},val:{}".format(idx,val))
        path = idx.decode("UTF-8")
        result[path] = ast.literal_eval(val.decode("UTF-8") or '{}')
    
    return result


def get_exporting_dir(tasks, dir_list):
    """現在実行中のエクスポートタスクによって生成されたディレクトリを取得
    """
    export_tasks = [task for task in tasks if task["name"] == "weko_search_ui.tasks.export_all_task"]
    export_dir = [dir for dir in dir_list if re.search(r"weko_export_.*", dir.split("/")[-1])]
    exporting_dir = {}
    if export_tasks and export_dir:
        for task in export_tasks:
            start_time = datetime.fromtimestamp(task["time_start"])
            filtered_dirs = [d for d in export_dir if datetime.fromtimestamp(os.path.getctime(d)) > start_time]
            newest_dir = min(filtered_dirs, key=lambda d: datetime.fromtimestamp(os.path.getctime(d)) - start_time)
            exporting_dir[newest_dir] = task["id"]
    return exporting_dir
    
if __name__ == "__main__":
    tempdir = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("TMPDIR")
    dir_list = glob.glob(tempdir+"/**")
    tasks, actives, reserveds = get_tasks()
    tmp_dir_info = get_temp_dir_info()
    exporting_dir = get_exporting_dir(actives, dir_list)
    for dir  in dir_list:
        try:
            # delete weko_export_{uuid}
            if re.search(r"weko_export_.*",dir):
                if dir not in exporting_dir:
                    shutil.rmtree(dir)

            # delete weko_import_{%Y%m%d%H%M%S%h}
            elif re.search(r"weko_import_[0-9]{20}",dir):
                can_delete = True
                for task in tasks:
                    if "weko_search_ui.tasks.check_import_items_task" == task["name"] and dir in task["args"]:
                        can_delete = False
                        break
                if can_delete:
                    shutil.rmtree(dir)

            # delete weko_import_{%Y%m%d%H%M%S}, deposit_activity_{%Y%m%d%H%M%S}
            elif re.search(r"weko_import_[0-9]{14}",dir) or re.search(r"deposit_activity_[0-9]{14}", dir):
                can_delete = True
                if dir in list(tmp_dir_info.keys()) and datetime.strptime(tmp_dir_info[dir]["expire"],"%Y-%m-%d %H:%M:%S") > datetime.now():
                    can_delete = False

                for task in tasks:
                    if "weko_search_ui.tasks.remove_temp_dir_task" == task["name"] and dir in task["args"]:
                        can_delete = False
                if can_delete:
                    shutil.rmtree(dir)

            # delete pymp-{uuid}
            elif re.search(r"/pymp-.{8}",dir):
                _dir = glob.glob(dir+"/**")
                if len(_dir)==0 or (len(_dir)==1 and re.search(r"\.nfs.*",_dir[0].split("/")[-1])):
                    shutil.rmtree(dir)

            # delete comb_pdfs
            elif "comb_pdfs" in dir:
                shutil.rmtree(dir)

            # delete {%Y%m%d%H%M%S}
            elif re.search(r"/[0-9]{14}",dir):
                shutil.rmtree(dir)

            # delete celery.log, celeryd.log, celery.log-{%Y%m%d%}
            elif re.search(r"/celery.*",dir):
                if os.path.isfile(dir):
                    os.remove(dir)
                elif os.path.isdir(dir):
                    shutil.rmtree(dir)
            
            # delete python file
            elif re.search(r".*\.py", dir):
                os.remove(dir)

            # delete other import
            elif re.search(r"weko_import_.*",dir):
                shutil.rmtree(dir)

        except Exception:
            print("failed delete :{}".format(dir))
            traceback.print_exc()
