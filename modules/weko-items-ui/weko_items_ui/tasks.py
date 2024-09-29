import json
import math
import traceback
import uuid
import os
from amqp import Channel
from celery import shared_task
from celery import current_app as current_celery_app
from flask import current_app

from kombu.compat import Consumer
from kombu.entity import Exchange, Queue
from invenio_pidstore.models import PersistentIdentifier
from invenio_oaiserver.response import is_private_index
from weko_admin.models import AdminSettings
from celery.utils.log import get_task_logger
from weko_authors.models import Authors
from weko_deposit.api import WekoRecord
from weko_index_tree.api import Indexes
from weko_items_ui.models import CRIS_Institutions, CRISLinkageResult
from weko_records.api import ItemsMetadata, Mapping
from weko_records.models import ItemTypeMapping
from weko_records.utils import json_loader
from weko_records_ui.permissions import check_publish_status, file_permission_factory 
from weko_schema_ui.schema import SchemaTree
from .linkage import Researchmap

logger = get_task_logger(__name__)

@shared_task(ignore_results=True)
def bulk_post_item_to_researchmap():
    """ receive cris_researchmap_linkage Queue and process sequential."""

    current_app.logger.debug("weko_item_ui.tasks.bulk_post_item_to_researchmap called")

    # make Exchange
    exchange : Exchange = current_app.config.get("LINKAGE_MQ_EXCHANGE")
    # make Queue
    queue : Queue= current_app.config.get("LINKAGE_MQ_QUEUE")
    with current_celery_app.pool.acquire(block=True) as conn:
        chan : Channel = conn.channel()
        exchange.declare(channel= chan)
        queue.declare( channel= chan )
        chan.queue_declare(queue=queue.name ,passive=True)
        with Consumer(connection=conn ,queue=queue.name,exchange=exchange.name ,routing_key='cris_researchmap_linkage') as consumer:
            for message in consumer.iterqueue(infinite=False):
                current_app.logger.debug(message)
                if message is not None:
                    process_researchmap_queue(message.decode() ,message)
                    


def process_researchmap_queue(body , message):
    """main process for regist to researchmap"""
    
    # body in item_uuid
    current_app.logger.debug(body)
    item_uuid = body["item_uuid"]
    recid = None

    with current_app.test_request_context():
        try:
            recid = PersistentIdentifier.get_by_object(pid_type='recid',
                                            object_type='rec',
                                            object_uuid=item_uuid)

            current_app.logger.debug(recid.pid_value)
            pid_int :int= math.floor(float(recid.pid_value))

            # アイテムを取得
            current_app.logger.debug("get_item")
            record , item = get_item(item_uuid)
            current_app.logger.info(record)
            current_app.logger.info(item)

            _ , jrc , _= json_loader(data=item.json ,pid=recid)
            mapping = Mapping.get_record(item.item_type_id)

            # 非公開は送付しない
            current_app.logger.debug("is_public")
            if not is_public(record,pid_int):
                register_linkage_result(pid_int,False ,item_uuid ,'非公開')
                return

            # 連携対象著者一覧取得
            current_app.logger.debug("get_authors")
            authors:list = get_authors(jrc)

            # 連携対象なし
            if len(authors) == 0:
                register_linkage_result(pid_int,False ,item_uuid ,'連携対象者無し')
                return 

            # 連携モード取得
            current_app.logger.debug("get_merge_mode")
            merge_mode = get_merge_mode()

            # 連携形式取得
            current_app.logger.debug("get_achievement_type")
            achievement_type = get_achievement_type(jrc)
            if not achievement_type:
                register_linkage_result(pid_int,False ,item_uuid ,'連携形式対象外')
                return 

            # 業績情報生成
            current_app.logger.debug("build_achievement")
            achievement_obj = build_achievement(record,item ,recid,mapping,jrc,achievement_type)

            jsons = []
            for author in authors:
                # 送信JSON作成
                data  = build_one_data(achievement_obj,merge_mode,author ,achievement_type)
                jsons.append(json.dumps(data))
            
            # 送信, 失敗時自動再送
            sender = Researchmap()
            current_app.logger.info(jsons)
            response_txt = sender.post_data('\r\n'.join(jsons))
            current_app.logger.error("rmap:{}".format(response_txt))
            res :dict = json.loads(response_txt)
            url :str = res.get("url" ,"")

            # 結果取得（取得完了まで待機、失敗時自動リトライ）
            result = sender.get_result(url)

            # 結果の書き戻し
            code = json.loads(result.splitlines()[0]).get('code')

            # v2api.pdf p17
            is_success = code == 200 or code == 201 or code == 204 or code == 304

            register_linkage_result(pid_int,is_success ,item_uuid ,result)

        except: 
            traceback.print_exc()

            if not recid :
                recid = PersistentIdentifier.get_by_object(pid_type='recid',
                                                object_type='rec',
                                                object_uuid=item_uuid)
            pid_int :int= math.floor(float(recid.pid_value))

            # 結果の書き戻し
            register_linkage_result(pid_int,False ,item_uuid ,traceback.format_exc())

        finally:
            # キュー削除
            message.ack()


def get_item(item_uuid):
    """アイテム取得"""
    record = WekoRecord.get_record_by_uuid(item_uuid)
    item_metadata = ItemsMetadata.get_by_object_id(item_uuid)
    return record,item_metadata

def is_public(record , pid):
    """公開状況確認"""
    
    """アイテム"""
    _is_item_published = check_publish_status(record)

    """インデックス"""
    _is_private_index = is_private_index(record)

    return _is_item_published and not _is_private_index

def get_authors(jrc):
    """著者取得"""

    author_links = jrc.get("author_link")

    authors:list = Authors.get_authorIdInfo('researchmap' , author_links)

    return authors
    
def get_merge_mode():
    """マージモード取得"""

    SETTINGS_NAME = current_app.config["WEKO_ADMIN_SETTINGS_RESEARCHMAP_LINKAGE_SETTINGS"]# type: ignore
    settings:dict = AdminSettings.get(SETTINGS_NAME , False) # type: ignore

    merge_mode = settings.get("merge_mode")
    if not merge_mode:
        merge_mode = current_app.config["WEKO_ITEMS_UI_CRIS_LINKAGE_RESEARCHMAP_MERGE_MODE_DEFAULT"]# type: ignore

    return merge_mode

def get_achievement_type(jrc):
    """業績種別取得"""

    researchtype_mappings = current_app.config["WEKO_ITEMS_UI_CRIS_LINKAGE_RESEARCHMAP_TYPE_MAPPINGS"]# type: ignore
    
    current_app.logger.debug('jrc')
    current_app.logger.debug(jrc)
    for mapping in researchtype_mappings:
        if mapping.get('JPCOAR_resource_type') == jrc.get("type")[0]:
            return mapping.get('achievement_type')

    return None

def build_achievement(record,item,recid,mapping,jrc, achievement_type):
    """業績種別JSON作成"""
    #e.g.
    # { "paper_title": {"ja": "ああああ", "en": "aaaaa"}
    #  ,"publication_date":"2024-01-25"
    #  ,"publication_name": {"ja": "ああああ", "en": "aaaaa"} }

    current_app.logger.debug("record:{}".format(record))
    current_app.logger.debug("item.json:{}".format(item.json))
    current_app.logger.debug("recid.pid_value:{}".format(recid.pid_value))
    current_app.logger.debug("mapping:{}".format(mapping))
    current_app.logger.debug("jrc:{}".format(jrc))
    current_app.logger.debug("achievement_type:{}".format(achievement_type))




    return_data = {}
    DEFAULT_LANG = current_app.config["WEKO_ITEMS_UI_DEFAULT_LANG"] # type: ignore
    researchmap_mappings = current_app.config["WEKO_ITEMS_UI_CRIS_LINKAGE_RESEARCHMAP_MAPPINGS"] # type: ignore
    researchtype_mappings = current_app.config["WEKO_ITEMS_UI_CRIS_LINKAGE_RESEARCHMAP_TYPE_MAPPINGS"]# type: ignore

    def __get_child_node(rm_map,prop):
        if rm_map.get("child_node"):
            nodes:list = rm_map.get("child_node").split('.')

            for node in nodes:
                prop = prop.get(node)

        return prop


    for rm_map in researchmap_mappings:
        # ja , en 取得
        if rm_map['type'] == 'lang':
            # if mapping:
            for parent_key in record.keys():
                jpcoar_mapping = mapping.get(parent_key,{}).get('jpcoar_mapping',"")
                property_name = rm_map["weko_name"]
                if jpcoar_mapping != "" and jpcoar_mapping.get(property_name):
                    prop = jpcoar_mapping[property_name]

                    prop =  __get_child_node(rm_map,prop)
                    if not prop:
                        continue

                    value_path = prop.get('@value','')

                    lang_path  = prop.get('@attributes',{}).get('xml:lang','')
                    
                    langs_dict = {}
                    for record_child_node in record.get(parent_key).get('attribute_value_mlt'):

                        if len(value_path.split('.')) > 1:
                            def __get_recursive( value , value_path ,lang , lang_path,idx):
                                if type(value) == list:
                                    li = []
                                    for i in range(len(value)):
                                        li.append(__get_recursive(value[i] , value_path ,lang[i] , lang_path,idx))
                                    return li
                                elif type(value) == dict:
                                    value = value.get(value_path.split('.')[idx])
                                    lang = lang.get(lang_path.split('.')[idx])
                                    return __get_recursive(value , value_path,lang , lang_path, idx + 1)

                                else:
                                    if lang == "en" or lang == "ja":
                                        langs_dict.update({lang:value})
                                    elif (lang == None or lang == "" ) and value != None:
                                        # nothing lang is also "ja" as default
                                        langs_dict.update({DEFAULT_LANG:value})
                                    return langs_dict
                            
                            langs_dict = __get_recursive(record_child_node , value_path ,record_child_node , lang_path,0)

                        else:
                            value = record_child_node.get(value_path)
                            lang = record_child_node.get(lang_path)

                            if lang == "en" or lang == "ja":
                                langs_dict.update({lang:value})
                            elif (lang == None or lang == "" ) and value != None:
                                # nothing lang is also "ja" as default
                                langs_dict.update({DEFAULT_LANG:value})

                    
                    if langs_dict != {}:
                        return_data.update({rm_map["rm_name"]:langs_dict})

        elif  rm_map['type'] == 'simple':
            if not rm_map.get("child_node"):
                value = jrc.get(rm_map["weko_name"])
                return_data.update({rm_map["rm_name"]:value})
            else :
                value = jrc.get(rm_map["weko_name"] , {}).get(rm_map.get("child_node"))
                if value:
                    return_data.update({rm_map["rm_name"]:value})


        elif rm_map['type'] == 'simple_value':
            value = jrc.get(rm_map["weko_name"],[{}])[0].get('value')
            if value:
                return_data.update({rm_map["rm_name"]:value})

        elif  rm_map['type'] == 'identifiers':
            identifer_kv = {}
            index = 0
            for relatedIdentifier in jrc.get(rm_map["weko_name"] ,{}).get('relatedIdentifier', []):
                identifierType =relatedIdentifier.get('identifierType')
                if identifierType.upper() == "DOI" or identifierType.upper() == "ISBN" :
                    ## 他の項目はresearchmapのAPI定義上更新不可。

                    value = jrc.get(rm_map["weko_name"]).get('relatedIdentifier')[index].get('value')
                    identifer_kv = {identifierType.lower():value}
                return_data.update({rm_map["rm_name"]:identifer_kv})
                index = index + 1
            # current_app.logger.debug('identifiers')

        elif  rm_map['type'] == 'authors':
            current_app.logger.debug('authors')
            # if mapping:
            for parent_key in record.keys():
                jpcoar_mapping = mapping.get(parent_key,{}).get('jpcoar_mapping',"")
                property_name = rm_map["weko_name"]
                if jpcoar_mapping != "" and jpcoar_mapping.get(property_name):
                    current_app.logger.debug(jpcoar_mapping)

                    prop = jpcoar_mapping[property_name]['creatorName']
                    value_path = prop.get('@value','')
                    lang_path  = prop.get('@attributes',{}).get('xml:lang','')

                    langs_dict = {}
                    en_list = []
                    ja_list = []
                    current_app.logger.debug('record.get(parent_key)')
                    current_app.logger.debug(record.get(parent_key))
                    for record_child_node in record.get(parent_key).get('attribute_value_mlt'):

                        def __dive( value_path, lang_path ,value_record_child_node,lang_record_child_node , path_depth_index = 0):
                            current_app.logger.debug(path_depth_index)
                            # finish
                            if isinstance(value_record_child_node ,str ):
                                lang = lang_record_child_node
                                value = value_record_child_node
                                if lang == None or lang == "": 
                                    lang = DEFAULT_LANG
                                
                                if lang == "en" :
                                    en_list.append({"name":value})
                                elif lang == "ja":
                                    ja_list.append({"name":value})
                            else:
                                if isinstance(value_record_child_node ,dict ):
                                    value_record_child_node = value_record_child_node.get(value_path.split('.')[path_depth_index])
                                    lang_record_child_node = lang_record_child_node.get(lang_path.split('.')[path_depth_index])
                                    # dive into deeper depth
                                    path_depth_index = path_depth_index + 1
                                    __dive( value_path, lang_path ,value_record_child_node,lang_record_child_node , path_depth_index)

                                elif isinstance(value_record_child_node ,list ):
                                    for index in range(len(value_record_child_node)):
                                        # dive into deeper depth
                                        __dive( value_path, lang_path ,value_record_child_node[index],lang_record_child_node[index] , path_depth_index)

                        # execute
                        __dive( value_path, lang_path ,record_child_node,record_child_node)
                    if len(en_list) > 0:
                        langs_dict.update({"en":en_list})
                    if len(ja_list) > 0:
                        langs_dict.update({"ja":ja_list})
                    
                    if langs_dict != {}:
                        return_data.update({rm_map["rm_name"]:langs_dict})
        elif  rm_map['type'] == 'type':
            if rm_map['achievement_type'] != achievement_type:
                continue
            
            resource_type = jrc.get(rm_map["weko_name"])[0]

            for researchtype_mapping in researchtype_mappings:
                if researchtype_mapping['achievement_type'] == achievement_type and \
                    researchtype_mapping['JPCOAR_resource_type'] == resource_type:
                    type_name = researchtype_mapping['detail_type_name']
                    return_data.update({rm_map["rm_name"]:type_name})
                    ## 2つある場合はDefault　'' の値に。
                    break

    # DOI
    for identifier in jrc.get('identifierRegistration', []):
            identifierType =identifier.get('identifierType')
            if identifierType.upper() == "JALC" or identifierType.upper()=="CROSSREF" or identifierType.upper()=="DATACITE":
                value = identifier.get('value')
                identifer_kv = {"doi":value}
            return_data.update({"identifiers":identifer_kv})

    # see_also
    # Handle>URLの順番で紐づける    
    see_also = []
    pid_int :int= math.floor(float(recid.pid_value))
    pid = PersistentIdentifier.query.filter_by(pid_type='parent',
                                        object_type='rec',
                                        pid_value='parent:{}'.format(pid_int)).first()
    if pid:
        hdl = PersistentIdentifier.query.filter_by(pid_type='hdl',
                                        object_uuid=pid.object_uuid).first()
        if hdl:
            see_also.append({"@id":hdl.pid_value,"label":"url"}) 
    
    url = "{}://{}/records/{}".format(os.environ['INVENIO_WEB_PROTOCOL'],os.environ['INVENIO_WEB_HOST_NAME'],pid_int)
    see_also.append({"@id":url,"label":"url"})

    # 現状、ファイルの添付は不可
    # file = jrc.get('file', None)
    # if file:
    #     for i,uri in enumerate(file.get('URI',[])):
    #         access_url = uri.get('value',None)
    #         if access_url:
    #            see_also.append({"@id":access_url,"label":"url"})
    
    return_data.update({"see_also":see_also})



    current_app.logger.debug('return_data:{}'.format(return_data))
    
    return return_data

    # return { "paper_title": {"ja": "aaaaa", "en": "aaaaa"}
    #         ,"publication_date":"2024-01-25"
    #         ,"publication_name": {"ja": "aaaaa", "en": "aaaaa"} }


def build_one_data(achievement_obj:dict , merge_mode:str , author:str ,achievement_type:str):
    """1著者分レコード作成"""

    # e.g.
    # {"insert": {"type": "published_papers", "permalink": "M1cQhPtdmlrSRFo4"}
    # ,"similar_merge": {"paper_title": {"ja": "ああああ", "en": "aaaaa"}
    #                   ,"publication_date":"2024-01-25"
    #                   ,"publication_name": {"ja": "ああああ", "en": "aaaaa"}}
    #  ,"priority":"input_data"
    # }

    ret = {}
    current_app.logger.info(merge_mode)
    if merge_mode == 'merge':
        ret = {"insert": {"type": achievement_type, "permalink": author} , "merge" :achievement_obj}
    elif merge_mode == 'force':
        ret = {"insert": {"type": achievement_type, "permalink": author} , "force" :achievement_obj}
    elif merge_mode == 'similar_merge_similar_data':
        ret = {"insert": {"type": achievement_type ,"permalink": author} , "similar_merge" :achievement_obj ,"priority":"similar_data" }
    elif merge_mode == 'similar_merge_input_data':
        ret = {"insert": {"type": achievement_type, "permalink": author} , "similar_merge" :achievement_obj ,"priority":"input_data" }
    return ret

def register_linkage_result(pid_int:int,result:bool,item_uuid:uuid, failed_log :str):
    """ researchmap 連携結果の登録"""
    return CRISLinkageResult().register_linkage_result(pid_int,CRIS_Institutions.RM,result , item_uuid ,failed_log)