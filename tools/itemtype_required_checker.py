# -*- coding: utf-8 -*-
"""
ログ例
* データベース名,アイテムタイプ名,アイテムタイプID,修正対象のプロパティ名(key)
"""
import csv, json, psycopg2, sys, traceback
from os import getenv
from os.path import dirname, join
from copy import deepcopy

def get_connection(db_name):
    return psycopg2.connect(
        database=db_name,
        user=getenv('INVENIO_POSTGRESQL_DBUSER'),
        password=getenv('INVENIO_POSTGRESQL_DBPASS'),
        host=getenv('INVENIO_POSTGRESQL_HOST'),
        port=5432,
        connect_timeout=10
    )

def check_itemtype_data(db_list):
    try:
        for db_name in db_list:
            print('=== Check {} start.'.format(db_name))
            with get_connection(db_name) as conn, conn.cursor() as cur:
                cur.execute("SELECT a.id, a.render, b.name FROM item_type a JOIN item_type_name b ON a.name_id = b.id;")
                results = cur.fetchall()
                for ret in results:
                    item_type_id = ret[0]
                    render = ret[1]
                    item_type_name = ret[2]

                    if isinstance(render, str):
                        render = json.loads(render)

                    meta_list = render.get('meta_list', {})
                    item_required_list = render.get('table_row_map', {}).get('schema', {}).get('required', [])

                    # check item required
                    fail_list = check_item_required(deepcopy(item_required_list), meta_list)
                    if fail_list:
                        print('{} - item type name: {}({}), issue list of item: {}'.format(db_name, item_type_name, item_type_id, fail_list))

                    fail_list = []
                    schemaeditor_schema = deepcopy(render.get('schemaeditor', {}).get('schema', {}))
                    tableRowMap_schema = deepcopy(render.get('table_row_map', {}).get('schema', {}))
                    tableRowMap_schema.pop('required', None)
                    tableRowMap_form = render.get('table_row_map', {}).get('form', [])
                    # check sub item required
                    check_sub_item_required(fail_list, schemaeditor_schema, tableRowMap_schema, tableRowMap_form)
                    if fail_list:
                        print('{} - item type name: {}({}), issue list of sub item: {}'.format(db_name, item_type_name, item_type_id, fail_list))
        print('=== Check {} end.'.format(db_list))
    except:
        print(f'ERROR: {traceback.print_exc()}')


def check_item_required(required_list, meta_list):
    fail_list = []
    if 'pubdate' in required_list:
        required_list.remove('pubdate')
    else:
        fail_list.append('pubdate')
    if isinstance(meta_list, dict):
        for item_key, item_data in meta_list.items():
            required_flag = item_data.get('option', {}).get('required', False)
            if required_flag:
                if item_key in required_list:
                    required_list.remove(item_key)
                else:
                    fail_list.append(item_key)
    if required_list:
        fail_list += required_list
    return fail_list


def check_sub_item_required(fail_list, schemaeditor_schema, tableRowMap_schema, tableRowMap_form):
    # check
    if 'required' in schemaeditor_schema:
        schemaeditor_required_list = deepcopy(schemaeditor_schema.get('required', []))
    else:
        schemaeditor_required_list = []
    if 'required' in tableRowMap_schema:
        tableRowMap_required_list = deepcopy(tableRowMap_schema.get('required', []))
    else:
        tableRowMap_required_list = []
    title = tableRowMap_schema.get('title', '')
    for form in tableRowMap_form:
        key = form.get('key', '').split('.')[-1]
        # skip for system item
        if key in ['pubdate', 'system_identifier_doi', 'system_identifier_hdl', 'system_identifier_uri', 'system_file']:
            continue

        append_flag = False
        required_flag = form.get('required', False)
        if required_flag:
            if key in schemaeditor_required_list:
                schemaeditor_required_list.remove(key)
            else:
                append_flag = True
            if key in tableRowMap_required_list:
                tableRowMap_required_list.remove(key)
            else:
                append_flag = True
            if append_flag:
                fail_list.append('{}({})'.format(title, form.get('key', '')))
        items = form.get('items', [])
        if items and key:
            # get schema of schemaeditor
            if 'properties' in schemaeditor_schema:
                schemaeditor_prop = schemaeditor_schema.get('properties', {}).get(key, {})
            elif 'items' in schemaeditor_schema:
                schemaeditor_prop = schemaeditor_schema.get('items', {}).get('properties', {}).get(key, {})
            else:
                schemaeditor_prop = schemaeditor_schema.get(key, {})
            # get schema of table_row_map
            if 'properties' in tableRowMap_schema:
                tableRowMap_prop = tableRowMap_schema.get('properties', {}).get(key, {})
            elif 'items' in tableRowMap_schema:
                tableRowMap_prop = tableRowMap_schema.get('items', {}).get('properties', {}).get(key, {})
            else:
                tableRowMap_prop = tableRowMap_schema.get(key, {})
            check_sub_item_required(fail_list, schemaeditor_prop, tableRowMap_prop, items)
    if schemaeditor_required_list:
        fail_list += ['{}({})'.format(title, a) for a in schemaeditor_required_list]
    if tableRowMap_required_list:
        fail_list +=  ['{}({})'.format(title, a) for a in tableRowMap_required_list]


if __name__ == '__main__':
    db_list = [getenv('INVENIO_POSTGRESQL_DBNAME')]
    check_itemtype_data(db_list)
