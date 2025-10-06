import os
import logging
import gc
import time
import json
import sys
import traceback
import requests
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.attributes import flag_modified

from flask import current_app
from invenio_db import db
from invenio_indexer.api import RecordIndexer
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_records.models import RecordMetadata

from weko_records.models import ItemMetadata, ItemType, ItemTypeProperty
import weko_schema_ui
from weko_admin.models import AdminSettings

def main(restricted_item_type_id, batch_size=500, run_es_reindex=False):
    """Main context."""

    try:
        current_app.logger.info('restricted records update start')
        with db.session.begin_nested():
            update_item_type_property(restricted_item_type_id)
            update_item_type(batch_size=batch_size)
            # item_metadata and records_metadata update are skipped because of running by sql script.
            # update_item_metadata()
            # update_records_metadata()
        update_admin_settings()
        db.session.commit()
        current_app.logger.info('restricted records update end')
        if run_es_reindex:
            current_app.logger.info('ElasticSearch data update start')
            elasticsearch_reindex(True)
            current_app.logger.info('ElasticSearch data update end')
    except SQLAlchemyError as ex:
        db.session.rollback()
        current_app.logger.error(str(ex))
        current_app.logger.error("records rollback")
        current_app.logger.error(traceback.format_exc())


def update_item_type_property(restricted_item_type_id):
    """update item_type_property record (specified id only)"""

    target_obj = ItemTypeProperty.query.filter_by(id=restricted_item_type_id).one_or_none()
    if target_obj:
        with open('tools/restricted_jsons/item_type_property/schema.json', 'r') as schema_file:
            target_obj.schema = json.load(schema_file)
        with open('tools/restricted_jsons/item_type_property/form.json', 'r') as form_file:
            target_obj.form = json.load(form_file)
        with open('tools/restricted_jsons/item_type_property/forms.json', 'r') as forms_file:
            target_obj.forms = json.load(forms_file)
    else:
        current_app.logger.warning('id: ' + str(restricted_item_type_id) + ' not found')

    current_app.logger.info('update item_type_property records success')


def update_item_type(batch_size=500):
    """update item_type records"""

    def _check_restricted_item_type(item_type):
        """check if item_type record is restricted item type."""
        target_nested_props = ['filename', 'provide', 'terms', 'termsDescription']
        props = item_type.schema['properties']
        for _, value in props.items():
            if value.get('type') != 'array' or value['items'].get('type') != 'object':
                continue
            nested_props = value['items'].get('properties', {})
            if all([prop in nested_props.keys() for prop in target_nested_props]):
                return True
        return False

    def _get_restricted_item_type_key(item_type):
        """get restricted item type key"""
        target_nested_props = ['filename', 'provide', 'terms', 'termsDescription']
        props = item_type.schema['properties']
        for key, value in props.items():
            if value.get('type') != 'array' or value['items'].get('type') != 'object':
                continue
            nested_props = value['items'].get('properties', {})
            if all([prop in nested_props.keys() for prop in target_nested_props]):
                return key
        return None

    def _format_new_schema(target_schema, key, schema_roles):
        """format new schema
        get new format of schema (add 'roles', del 'groups', 'dataType')
        
        Args:
            target_schema (dict): original schema
            key (str): target property key
            schema_roles (dict): roles to be added
        Returns:
            dict: formatted schema
        """
        properties = target_schema['properties'][key]['items']['properties']
        filtered_properties = {
            k: v for k, v in properties.items()
            if k not in ['groups', 'dataType']
        }
        if 'roles' not in filtered_properties.keys():
            filtered_properties['roles'] = schema_roles
        target_schema['properties'][key]['items']['properties'] = filtered_properties
        return dict(target_schema)

    def _format_new_form(target_form, key, form_roles):
        """format new form
            get new format of form (add 'roles', del 'groups', 'dataType')
        Args:
            target_form (list): original form
            key (str): target property key
            form_roles (dict): roles to be added
        Returns:
            list: formatted form
        """
        new_form = []
        for element in target_form:
            if isinstance(element, dict) and element.get('key') == key:
                remove_elements_key = [key + '[].groups', key + '[].dataType']
                filterd_items = [
                    item for item in element['items']
                    if item['key'] not in remove_elements_key
                ]
                if (key + '[].roles') not in [item['key'] for item in filterd_items]:
                    filterd_items.append(form_roles)
                element['items'] = filterd_items
            new_form.append(element)
        return new_form

    def _format_new_render(target_render, key, schema_roles, form_roles, render_roles):
        """get new format of render (add 'roles', del 'groups', 'dataType')"""
        # schemaeditor schema
        schemaeditor_schema = target_render['schemaeditor']['schema']['properties'][key]
        new_schemaeditor_schema = {k: v for k, v in schemaeditor_schema.items() if k not in ['groups', 'dataType']}
        new_schemaeditor_schema['roles'] = render_roles
        target_render['schemaeditor']['schema']['properties'][key] = new_schemaeditor_schema
        # table row map form
        table_row_map_form = target_render['table_row_map']['form']
        target_render['table_row_map']['form'] = _format_new_form(table_row_map_form, key, form_roles)
        # table row map schema
        table_row_map_schema = target_render['table_row_map']['schema']
        target_render['table_row_map']['schema'] = _format_new_schema(table_row_map_schema, key, schema_roles)
        return target_render

    current_app.logger.info('update item_type records start')

    # load json data
    schema = None
    with open('tools/restricted_jsons/item_type/roles_schema.json', 'r') as schema_file:
        schema = json.load(schema_file)
    form = None
    with open('tools/restricted_jsons/item_type/roles_form.json', 'r') as form_file:
        form = json.load(form_file)
    render = None
    with open('tools/restricted_jsons/item_type/roles_render.json', 'r') as render_file:
        render = json.load(render_file)

    # update item_type records
    query =  db.session.query(ItemType.id).filter(
        ItemType.is_deleted.is_(False)
    ).order_by(ItemType.name_id, ItemType.tag).statement
    results = db.engine.execution_options(stream_results=True).execute(query)
    item_type_ids = [r[0] for r in results]
    current_app.logger.info('target item_type count: ' + str(len(item_type_ids)))
    
    for item_type_id in item_type_ids:
        item_type = ItemType.query.get(item_type_id)
        if not _check_restricted_item_type(item_type):
            continue

        # update item type
        key = _get_restricted_item_type_key(item_type)
        # schema
        item_type.schema = _format_new_schema(dict(item_type.schema), key, schema)
        flag_modified(item_type, "schema")
        # form
        form_roles = json.loads(json.dumps(form).replace('<key>', key))
        item_type.form = _format_new_form(list(item_type.form), key, form_roles)
        flag_modified(item_type, "form")
        # render
        item_type.render = _format_new_render(dict(item_type.render), key, schema, form_roles, render)
        flag_modified(item_type, "render")
        
        current_app.logger.info(f'    Updated item_type id: {item_type.id}')

    current_app.logger.info('update item_type records success')


def update_item_metadata(bach_size=100):
    """update item_metadata records"""

    def _format_json(record_json):
        """get new format of json"""
        owner_id = int(record_json.pop('owner', -1))
        shared_user_id = int(record_json.pop('shared_user_id', -1))

        if owner_id:
            record_json['owner'] = owner_id
            
        shared_user_ids = [shared_user_id] if shared_user_id and shared_user_id > 0 else []

        record_json['shared_user_ids'] = shared_user_ids
        record_json['weko_shared_ids'] = shared_user_ids

        return record_json

    current_app.logger.info('update item_metadata records start')

    # update item_metadata records
    query = """
        SELECT id FROM item_metadata
        WHERE NOT (json ? 'shared_user_ids')
        AND json ? 'shared_user_id'
    """
    results = db.engine.execution_options(stream_results=True).execute(query)
    item_metadata_ids = [r[0] for r in results]
    current_app.logger.info('target item_metadata count: ' + str(len(item_metadata_ids)))

    pages = [item_metadata_ids[i:i + bach_size] for i in range(0, len(item_metadata_ids), bach_size)]
    for item_metadata_id_batch in pages:
        item_metadata_list = ItemMetadata.query.filter(
            ItemMetadata.id.in_(item_metadata_id_batch)
        ).all()
        for item_metadata in item_metadata_list:
            item_metadata.json = _format_json(dict(item_metadata.json))
            flag_modified(item_metadata, "json")
            current_app.logger.info(f'    Updated item_metadata id: {item_metadata.id}')
            gc.collect()

    current_app.logger.info('update item_metadata records success')


def update_records_metadata(bach_size=100):
    """update records_metadata records"""

    def _format_json(record_json):
        """get new format of json"""
        owner_id = int(record_json.pop('owner', -1))
        shared_user_id = int(record_json.pop('weko_shared_id', -1))

        if owner_id > 0:
            record_json['owner'] = owner_id
            record_json['owners'] = [owner_id]
            record_json['_deposit']['owner'] = owner_id
            record_json['_deposit']['owners'] = [owner_id]

        shared_user_ids = [shared_user_id] if shared_user_id and shared_user_id > 0 else []

        record_json['weko_shared_ids'] = shared_user_ids
        record_json['_deposit']['weko_shared_ids'] = shared_user_ids
        return record_json

    current_app.logger.info('update record_metadata records start')

    # update records_metadata records
    query = """
        SELECT id FROM records_metadata
        WHERE NOT (json ? 'weko_shared_ids')
        AND json ? 'weko_shared_id'
    """
    results = db.engine.execution_options(stream_results=True).execute(query)
    record_metadata_ids = [r[0] for r in results]
    current_app.logger.info('target record_metadata count: ' + str(len(record_metadata_ids)))

    current_app.logger.info(f'record_metadata_ids: {record_metadata_ids}')
    pages = [record_metadata_ids[i:i + bach_size] for i in range(0, len(record_metadata_ids), bach_size)]
    for record_metadata_id_batch in pages:
        # record_metadata_id_batch = record_metadata_ids[page:page+bach_size]
        record_metadata_list = RecordMetadata.query.filter(
            RecordMetadata.id.in_(record_metadata_id_batch)
        ).all()
        for record_metadata in record_metadata_list:
            record_metadata.json = _format_json(dict(record_metadata.json))
            flag_modified(record_metadata, "json")
            current_app.logger.info(f'    Updated record_metadata id: {record_metadata.id}')
            gc.collect()

    current_app.logger.info('update record_metadata records success')

def update_admin_settings():
    """update admin_settings for secret_URL_download """
    current_app.logger.info('update admin_settings start')
    
    restricted_access = AdminSettings.get('restricted_access', False)
    if not restricted_access:
        restricted_access = current_app.config['WEKO_ADMIN_RESTRICTED_ACCESS_SETTINGS']
    else:
        restricted_access['secret_URL_file_download'] = {
            "secret_download_limit": 10,
            "secret_expiration_date": 30,
            "secret_download_limit_unlimited_chk": False,
            "secret_expiration_date_unlimited_chk": False
        }
    AdminSettings.update('restricted_access', restricted_access)
    
    current_app.logger.info('update admin_settings success')

def elasticsearch_reindex( is_db_to_es ):
    """ 
    reindex *-weko-item-* of elasticsearch index

    Args:
    is_db_to_es : boolean
        if True,  index Documents from DB data
        if False, index Documents from ES data itself
    
    Returns:
        str : 'completed' 
        
    Raises:
    AssersionError 
        In case of the response code from ElasticSearch is not 200,
        Subsequent processing is interrupted.
    
    Todo:
        warning: Simultaneous execution is prohibited. 
        warning: Execution during operation is prohibited 
                because documents submitted during execution may not be reflected. 
                Please allow execution only during maintenance periods.
    """
    from invenio_oaiserver.percolator import _create_percolator_mapping
    # consts
    elasticsearch_host = os.environ.get('INVENIO_ELASTICSEARCH_HOST') 
    base_url = 'http://' + elasticsearch_host + ':9200/'
    reindex_url = base_url + '_reindex?pretty&refresh=true&wait_for_completion=true'
    
    # "{}-weko-item-v1.0.0".format(prefix)
    index = current_app.config['INDEXER_DEFAULT_INDEX']
    tmpindex = "{}-tmp".format(index)
    
    # "{}-weko".format(prefix)
    alias_name = current_app.config['SEARCH_UI_SEARCH_INDEX']

    # get base_index_definition (mappings and settings)
    current_path = os.path.dirname(os.path.abspath(weko_schema_ui.__file__))
    file_path = os.path.join(current_path, 'mappings', 'v6', 'weko', 'item-v1.0.0.json')
    with open(file_path,mode='r') as json_file:
        json_data = json_file.read()
        base_index_definition = json.loads(json_data)

    number_of_replicas = base_index_definition.get("settings").get("number_of_replicas")
    refresh_interval = base_index_definition.get("settings").get("refresh_interval")

    headers = {
        'Content-Type': 'application/json',
    }
    json_data_to_tmp = {
        'source': {
            'index': index,
        },
        'dest': {
            'index': tmpindex,
        },
    }
    json_data_to_dest = {
        'source': {
            'index': tmpindex,
        },
        'dest': {
            'index': index,
        },
    }
    json_data_set_alias = {
        "actions" : [
            { "add" : { "index" : index, "alias" : alias_name } }
        ]
    }

    current_app.logger.info(' START elasticsearch reindex: {}.'.format(index))

    # トランザクションログをLucenceに保存。
    response = requests.post(base_url + index + "/_flush?wait_if_ongoing=true") 
    current_app.logger.info(response.text)
    assert response.status_code == 200 ,response.text

    response = requests.get(base_url + '_cat/indices/?h=index&index=' + tmpindex )

    # 一時保管用のインデックスを作成
    # create tmp index
    current_app.logger.info("START create tmpindex") 
    current_app.logger.info("PUT tmpindex") 
    response = requests.put(base_url + tmpindex + "?pretty", headers=headers ,json=base_index_definition)
    current_app.logger.info(response.text)
    assert response.status_code == 200 ,response.text
    current_app.logger.info("add setting percolator") 

    _create_percolator_mapping(tmpindex, "item-v1.0.0")
    current_app.logger.info("END create tmpindex") 
    
    # 高速化を期待してインデックスの設定を変更。
    current_app.logger.info("START change setting for faster") 
    response = requests.put(base_url + tmpindex + "/_settings?pretty", headers=headers ,json={ "index" : {"number_of_replicas" : 0, "refresh_interval": -1 }})
    current_app.logger.info(response.text)
    assert response.status_code == 200 ,response.text #
    current_app.logger.info("END change setting for faster") 

    
    # document count
    current_app.logger.info("index document count:{}".format(requests.get(base_url + "_cat/count/"+ index ).text)) 
    current_app.logger.info("tmpindex document count:{}".format(requests.get(base_url + "_cat/count/"+ tmpindex ).text))

    # 一時保管用のインデックスに元のインデックスの再インデックスを行う
    # reindex from index to tmpindex
    current_app.logger.info("START reindex")
    response = requests.post(url=reindex_url, headers=headers, json=json_data_to_tmp)
    current_app.logger.info(response.text)
    assert response.status_code == 200 ,response.text
    current_app.logger.info("END reindex")

    # document count
    index_cnt = requests.get(base_url + "_cat/count/"+ index + "?h=count").text
    tmpindex_cnt = requests.get(base_url + "_cat/count/"+ tmpindex + "?h=count").text
    current_app.logger.info("index document count:{}".format(index_cnt)) 
    current_app.logger.info("tmpindex document count:{}".format(tmpindex_cnt))
    assert index_cnt == tmpindex_cnt,'Document counts do not match.'

    # 再インデックス前のインデックスを削除する
    current_app.logger.info("START delete index") 
    response = requests.delete(base_url + index)
    current_app.logger.info(response.text)
    assert response.status_code == 200 ,response.text
    current_app.logger.info("END delete index") 

    # 新しくインデックスを作成する
    #create index
    current_app.logger.info("START create index") 
    current_app.logger.info("PUT index") 
    response = requests.put(url = base_url + index + "?pretty", headers=headers ,json=base_index_definition)
    current_app.logger.info(response.text)
    assert response.status_code == 200 ,response.text
    current_app.logger.info("add setting percolator") 
    _create_percolator_mapping(index, "item-v1.0.0")
    current_app.logger.info("END create index") 

    # 高速化を期待してインデックスの設定を変更。
    current_app.logger.info("START change setting for faster") 
    response = requests.put(base_url + index + "/_settings?pretty", headers=headers ,json={ "index" : {"number_of_replicas" : 0, "refresh_interval": -1 }})
    current_app.logger.info(response.text)
    assert response.status_code == 200 ,response.text
    current_app.logger.info("END change setting for faster") 

    # aliasを再設定する。
    current_app.logger.info("START re-regist alias") 
    response = requests.post(base_url + "_aliases", headers=headers, json=json_data_set_alias )
    current_app.logger.info(response.text)
    assert response.status_code == 200 ,response.text
    current_app.logger.info("END re-regist alias") 

    # アイテムを再投入する。
    current_app.logger.info("START reindex")
    if is_db_to_es :
        current_app.logger.info("reindex es from db")
        response = _elasticsearch_remake_item_index(index_name=index)
        current_app.logger.info(response) # array

        response = requests.post(url=base_url + "_refresh")
        current_app.logger.info(response.text)
        assert response.status_code == 200 ,response.text
    else :
        current_app.logger.info("reindex es from es")
        # 一時保管用のインデックスから、新しく作成したインデックスに再インデックスを行う
        # reindex from tmpindex to index
        response = requests.post(url=reindex_url , headers=headers, json=json_data_to_dest)
        current_app.logger.info(response.text)
        assert response.status_code == 200 ,response.text
    current_app.logger.info("END reindex")

    # 高速化を期待して変更したインデックスの設定を元に戻す。
    current_app.logger.info("START revert setting for faster") 
    response = requests.put(base_url + index + "/_settings?pretty", headers=headers ,json={ "index" : {"number_of_replicas" : number_of_replicas, "refresh_interval": refresh_interval }})
    current_app.logger.info(response.text)
    assert response.status_code == 200 ,response.text 
    current_app.logger.info("END revert setting for faster") 

    # document count
    index_cnt = requests.get(base_url + "_cat/count/"+ index + "?h=count").text
    tmpindex_cnt = requests.get(base_url + "_cat/count/"+ tmpindex + "?h=count").text
    current_app.logger.info("index document count:{}".format(index_cnt)) 
    current_app.logger.info("tmpindex document count:{}".format(tmpindex_cnt))
    assert index_cnt == tmpindex_cnt ,'Document counts do not match.'


    # 一時保管用のインデックスを削除する 
    # delete tmp-index
    current_app.logger.info("START delete tmpindex") 
    response = requests.delete(base_url + tmpindex)
    current_app.logger.info(response.text)
    assert response.status_code == 200 ,response.text
    current_app.logger.info("END delete tmpindex") 

    current_app.logger.info(' END elasticsearch reindex: {}.'.format(index))
    
    return 'completed'

def _elasticsearch_remake_item_index(index_name):
    """ index Documents from DB (Private method) """
    from invenio_oaiserver.models import OAISet
    from invenio_oaiserver.percolator import _new_percolator
    returnlist = []
    # インデックスを登録
    current_app.logger.info(' START elasticsearch import from oaiserver_set')
    oaiset_ = OAISet.query.all()
    for target in oaiset_ :
        spec = target.spec
        search_pattern = target.search_pattern
        _new_percolator(spec , search_pattern)
    current_app.logger.info(' END elasticsearch import from oaiserver_set')

    # アイテムを登録
    current_app.logger.info(' START elasticsearch import from records_metadata')
    # get all registered record_metadata's ids
    uuids = (x[0] for x in PersistentIdentifier.query.filter_by(
        object_type='rec', status=PIDStatus.REGISTERED
    ).filter(
        PersistentIdentifier.pid_type.in_(['oai'])
    ).values(
        PersistentIdentifier.object_uuid
    ))
    indexer = RecordIndexer()
    for x in uuids:
        res = indexer.index_by_id(x)
        assert res != None ,'Index class is None.'
        assert res.get("_shards").get("failed") == 0 ,'Index fail.'
        returnlist.append(res)
    current_app.logger.info(' END elasticsearch import from records_metadata')
    
    return returnlist

if __name__ == '__main__':
    # start command
    # > invenio shell updateRestrictedRecords.py <restricted_item_type_property_id>

    args = sys.argv
    if len(args) > 1:
        restricted_item_type_id = int(args[1])
        main(restricted_item_type_id)

