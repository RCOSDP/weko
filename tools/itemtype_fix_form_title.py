# -*- coding: utf-8 -*-
"""
ログ例
* データベース名,アイテムタイプ名,アイテムタイプID,修正対象のプロパティ名(key)
"""
import csv, json, psycopg2, sys, traceback
from os import getenv
from os.path import dirname, join

TARGET_LIST_FILENAME = 'db_list.tsv'

def get_db_list(filename):
    db_list = []
    with open(filename, "r") as f:
        reader = csv.reader(f, delimiter='\t')
        l = [row for row in reader]
        for ll in l:
            db_list.append(ll[0])
    return db_list

def get_connection(db_name):
    return psycopg2.connect(
        database=db_name,
        user=getenv('INVENIO_POSTGRESQL_DBUSER'),
        password=getenv('INVENIO_POSTGRESQL_DBPASS'),
        host=getenv('INVENIO_POSTGRESQL_HOST'),
        port=5432,
        connect_timeout=10
    )

def fix_form_title(db_list):
    try:
        for db_name in db_list:
            update_logs = []
            with get_connection(db_name) as conn, conn.cursor() as cur:
                cur.execute('SELECT it.id, itn.name, form, render FROM item_type AS it INNER JOIN item_type_name AS itn ON it.name_id = itn.id')
                itemtypes = cur.fetchall()

                for itemtype in itemtypes:
                    is_form_changed = False
                    itemtype_id = itemtype[0]
                    itemtype_name = itemtype[1]
                    form = itemtype[2]
                    render = itemtype[3]
                    
                    if isinstance(form, str):
                        form = json.loads(form)
                    if isinstance(render, str):
                        render = json.loads(render)

                    render_meta_list = render.get('meta_list')

                    for i, f in enumerate(form):
                        form_key = f['key']
                        render_title = render_meta_list.get(form_key, {}).get('title_i18n')
                        # pubdateやsystem_fileなど、meta_list内に存在しないものは無視
                        if not render_title:
                            continue

                        # 管理画面はrenderのmeta_listを参照している。renderに沿った状態に修正する。
                        if form[i].get('title_i18n') != render_title:
                            is_form_changed = True
                            form[i]['title_i18n'] = render_title
                            update_logs.append(f"{db_name},{itemtype_name},{itemtype_id},{form_key}")
                    
                    # formが変更されていたら更新
                    if is_form_changed:
                        render['table_row_map']['form']=form
                        cur.execute('UPDATE item_type SET updated = CURRENT_TIMESTAMP, form = %s, render= %s WHERE id = %s', (json.dumps(form),json.dumps(render), itemtype_id))

                for log in update_logs:
                    print(log)

    except:
        print(f'ERROR: {traceback.print_exc()}')
        for log in update_logs:
            print("rollback: "+log)

if __name__ == '__main__':
    #args = sys.argv

    #input_file_path = args[1] if len(args) == 2 else join(dirname(__file__), TARGET_LIST_FILENAME)
    #db_list = get_db_list(input_file_path)

    db_list = [getenv('INVENIO_POSTGRESQL_DBNAME')]

    fix_form_title(db_list)
