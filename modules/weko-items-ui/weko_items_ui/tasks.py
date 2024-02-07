import json
import math
import traceback
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
from weko_items_ui.models import CRISLinkageResult
from weko_records.api import ItemsMetadata, Mapping
from weko_records.models import ItemTypeMapping
from weko_records.utils import json_loader
from weko_records_ui.permissions import check_publish_status, file_permission_factory 
from weko_schema_ui.schema import SchemaTree
from .linkage import Reseachmap

logger = get_task_logger(__name__)

@shared_task(ignore_results=True)
def bulk_post_item_to_researchmap():
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
                    __callback(message.decode() ,message)
                    
                # else :
                #     consumer.cancel()

            # c.drain_events()

def __callback(body , message):
    
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
            current_app.logger.debug("get_achevement_type")
            achievement_type = get_achevement_type(jrc)

            # 業績情報生成
            current_app.logger.debug("build_achievement")
            achevement_obj = build_achievement(record,item ,recid,mapping,jrc,achievement_type)

            jsons = []
            for author in authors:
                # 送信JSON作成
                data  = build_one_data(achevement_obj,merge_mode,author ,achievement_type)
                jsons.append(json.dumps(data))
            
            # 送信, 失敗時自動再送
            sender = Reseachmap()
            current_app.logger.info(jsons)
            response_txt = sender.post_data('\r\n'.join(jsons))

            res :dict = json.loads(response_txt)
            url :str = res.get("url" ,"")

            # 結果取得（取得完了まで待機、失敗時自動リトライ）
            result = sender.get_result(url)

            # 結果の書き戻し
            code = json.loads(result.splitlines()[0]).get('code')
            is_success = code == 200 or code == 304

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

def file_is_public(record):
    """ファイル公開状況確認"""
    return file_permission_factory(record).can() # type: ignore

def get_authors(jrc):
    """著者取得"""

    author_links = jrc.get("author_link")

    authors:list = Authors.get_authorIdInfo('researchmap' , author_links)

    return authors
    
def convert_jpcore(records):
    return SchemaTree.get_jpcoar_json(records)

def get_merge_mode():
    """マージモード取得"""

    SETTINGS_NAME = current_app.config["WEKO_ADMIN_SETTINGS_RESERCHMAP_LINKAGE_SETTINGS"]# type: ignore
    settings:dict = AdminSettings.get(SETTINGS_NAME , False) # type: ignore

    merge_mode = settings.get("merge_mode")
    if not merge_mode:
        merge_mode = current_app.config["WEKO_ITEMS_UI_CRIS_LINKAGE_RESEACHMAP_MERGE_MODE_DEFAULT"]# type: ignore

    return merge_mode

def get_achevement_type(jrc):
    """業績種別取得"""

    # fixme
    return "published_papers"

def build_achievement(record,item,recid,mapping,jrc, achievement_type):
    """業績種別JSON作成"""
    #e.g.
    # { "paper_title": {"ja": "ああああ", "en": "aaaaa"}
    #  ,"publication_date":"2024-01-25"
    #  ,"publication_name": {"ja": "ああああ", "en": "aaaaa"} }

    current_app.logger.debug(record)
    current_app.logger.debug(item.json)
    current_app.logger.debug(recid.pid_value)
    current_app.logger.debug(mapping)
    current_app.logger.debug(jrc)
    current_app.logger.debug(achievement_type)


    return_data = {}
    researchmap_mappings = [
        { 'type' : 'lang' , "rm_name" : 'paper_title', "jpcore_name" : 'dc:title' , "weko_name" :"title"}
        ,{'type' : 'lang' , "rm_name" : 'description', "jpcore_name" : 'datacite:description' , "weko_name" :"description"}
        ,{'type' : 'lang' , "rm_name" : 'publisher', "jpcore_name" : 'dc:publisher' , "weko_name" :"publisher"}
        ,{'type' : 'lang' , "rm_name" : 'publication_name ', "jpcore_name" : 'jpcoar:sourceTitle' , "weko_name" :"sourceTitle"}
        # ,{'type' : 'authors'    , "rm_name" : 'authors'     , "jpcore_name" : 'jpcoar:creator'  ,"weko_name": 'creator'}
        # ,{'type' : 'identifiers', "rm_name" : "identifiers" , "jpcore_name" : 'jpcoar:relation' ,"weko_name": 'relation'}
        ,{'type' : 'simple', "rm_name" : 'publication_date', "jpcore_name" :  'datacite:date' , "weko_name" : "date"}
        # ,{'type' : 'simple', "rm_name" : 'publication_date', "jpcore_name" :  'datacite:date' , "weko_name" : "publish_date"}
        ,{'type' : 'simple', "rm_name" : 'volume', "jpcore_name" :  'jpcoar:volume' , "weko_name" : "volume"}
        ,{'type' : 'simple', "rm_name" : 'number', "jpcore_name" :  'jpcoar:issue' , "weko_name" : "issue"}
        ,{'type' : 'simple', "rm_name" : 'starting_page', "jpcore_name" :  'jpcoar:pageStart' , "weko_name" : "pageStart"}
        ,{'type' : 'simple', "rm_name" : 'ending_page', "jpcore_name" :  'jpcoar:pageEnd' , "weko_name" : "pageEnd"}
        ,{'type' : 'simple', "rm_name" : 'languages', "jpcore_name" :  'dc:language' , "weko_name" : "language"}
    ]

    for rm_map in researchmap_mappings:
        # ja , en 取得
        if rm_map['type'] == 'lang':
            # if mapping:
            for parent_key in record.keys():
                jpcoar_mapping = mapping.get(parent_key,{}).get('jpcoar_mapping',"")
                current_app.logger.debug(jpcoar_mapping)
                property_name = rm_map["weko_name"]
                if jpcoar_mapping != "" and jpcoar_mapping.get(property_name):
                    prop = jpcoar_mapping[property_name]
                    value_path = prop.get('@value','')

                    lang_path  = prop.get('@attributes',{}).get('xml:lang','')
                    
                    langs_dict = {}
                    for record_child_node in record.get(parent_key).get('attribute_value_mlt'):
                        value = record_child_node.get(value_path)
                        lang = record_child_node.get(lang_path)
                        if lang == "en" or lang == "ja":
                            langs_dict.update({lang:value})
                    
                    if langs_dict != {}:
                        return_data.update({rm_map["rm_name"]:langs_dict})

        elif  rm_map['type'] == 'simple':
            value = jrc.get(rm_map["weko_name"])
            current_app.logger.debug({rm_map["rm_name"]:value})
            return_data.update({rm_map["rm_name"]:value})
            # print(jrc.get(rm_map["weko_name"]))

    current_app.logger.debug('return_data')
    current_app.logger.debug(return_data)
    return return_data

    # return { "paper_title": {"ja": "aaaaa", "en": "aaaaa"}
    #         ,"publication_date":"2024-01-25"
    #         ,"publication_name": {"ja": "aaaaa", "en": "aaaaa"} }


def build_one_data(achevement_obj:dict , merge_mode:str , author:str ,achievement_type:str):
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
        ret = {"insert": {"type": achievement_type, "permalink": author} , "merge" :achevement_obj}
    elif merge_mode == 'force':
        ret = {"insert": {"type": achievement_type, "permalink": author} , "force" :achevement_obj}
    elif merge_mode == 'similar_merge_similar_data':
        ret = {"insert": {"type": achievement_type ,"permalink": author} , "similar_merge" :achevement_obj ,"priority":"similar_data" }
    elif merge_mode == 'similar_merge_input_data':
        ret = {"insert": {"type": achievement_type, "permalink": author} , "similar_merge" :achevement_obj ,"priority":"input_data" }
    return ret

def register_linkage_result(pid_int,result,item_uuid, failed_log):
    return CRISLinkageResult().register_linkage_result(pid_int,"researchmap",result , item_uuid,failed_log)