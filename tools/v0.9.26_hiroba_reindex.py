import os
from elasticsearch import Elasticsearch
import datetime
import psycopg2
import pytz
import orjson
import requests
from flask import current_app
from weko_index_tree.api import Indexes

def reindex_and_add_items():
    """
    reindex *-record-view-*,*-file-download-*,*-file-preview-* of elasticsearch index
    and add index_id and is_open_access to *-events-stats-file-download-* and *-events-stats-file-preview-*

    Returns:
        str : 'all completed'
    """

    try:

        stats_record_view_index=os.environ.get('SEARCH_INDEX_PREFIX', 'tenant1') + '-stats-record-view-000001'
        events_stats_file_preview_index=os.environ.get('SEARCH_INDEX_PREFIX', 'tenant1') + '-events-stats-file-preview-000001'
        stats_file_preview_index=os.environ.get('SEARCH_INDEX_PREFIX', 'tenant1') + '-stats-file-preview-000001'
        events_stats_file_download_index=os.environ.get('SEARCH_INDEX_PREFIX', 'tenant1') + '-events-stats-file-download-000001'
        stats_file_download_index=os.environ.get('SEARCH_INDEX_PREFIX', 'tenant1') + '-stats-file-download-000001'

        alias_stats_record_view=os.environ.get('SEARCH_INDEX_PREFIX', 'tenant1') + '-stats-record-view-test'
        alias_events_stats_file_preview=os.environ.get('SEARCH_INDEX_PREFIX', 'tenant1') + '-events-stats-file-preview-test'
        alias_stats_file_preview=os.environ.get('SEARCH_INDEX_PREFIX', 'tenant1') + '-stats-file-preview-test'
        alias_events_stats_file_download=os.environ.get('SEARCH_INDEX_PREFIX', 'tenant1') + '-events-stats-file-download-test'
        alias_stats_file_download=os.environ.get('SEARCH_INDEX_PREFIX', 'tenant1') + '-stats-file-download-test'

        reindex_target = {}

        reindex_target['stats-record-view'] = {'index':stats_record_view_index,'alias_name':alias_stats_record_view,'file_path':'/aggregations/aggr_record_view/v6/aggr-record-view-v1.json','refresh_interval':'1m'}
        reindex_target['events-stats-file-preview'] = {'index':events_stats_file_preview_index,'alias_name':alias_events_stats_file_preview,'file_path':'/file_preview/v6/file-preview-v1.json','refresh_interval':'5s'}
        reindex_target['stats-file-preview'] = {'index':stats_file_preview_index,'alias_name':alias_stats_file_preview,'file_path':'/aggregations/aggr_file_preview/v6/aggr-file-preview-v1.json','refresh_interval':'1m'}
        reindex_target['events-stats-file-download'] = {'index':events_stats_file_download_index,'alias_name':alias_events_stats_file_download,'file_path':'/file_download/v6/file-download-v1.json','refresh_interval':'5s'}
        reindex_target['stats-file-download'] = {'index':stats_file_download_index,'alias_name':alias_stats_file_download,'file_path':'/aggregations/aggr_file_download/v6/aggr-file-download-v1.json','refresh_interval':'1m'}

        #reindex
        for index, value in reindex_target.items():
            current_app.logger.info('reindex call {}'.format(index))
            elasticsearch_reindex(value)

        current_app.logger.info("called reindex completed")

        #add items
        timezone_from = pytz.timezone('UTC')
        timezone_to = pytz.timezone('Asia/Tokyo')

        HOST = os.environ['INVENIO_POSTGRESQL_HOST']
        PORT = '25401'
        DATABASE = os.environ['INVENIO_POSTGRESQL_DBNAME']
        USER = os.environ['INVENIO_POSTGRESQL_DBUSER']
        PASSWORD = os.environ['INVENIO_POSTGRESQL_DBPASS']

        connector = psycopg2.connect(
            'postgresql://{user}:{password}@{host}:{port}/{dbname}'.format(
                user=USER,
                password=PASSWORD,
                host=HOST,
                port=PORT,
                dbname=DATABASE
            )
        )
        cur = connector.cursor()

        es = Elasticsearch(
            'http://' + os.environ.get('INVENIO_ELASTICSEARCH_HOST', 'localhost') + ':9200')

        for index in [events_stats_file_download_index, events_stats_file_preview_index]:

            current_app.logger.info("index",index)

            # 対象インデックスのドキュメント件数取得
            count = es.count(
                index=index
            )
            current_app.logger.info("count",count)

            #add index_id
            current_app.logger.info('add index_id')

            # ドキュメントのitem_id,buckets_idのみを取得
            search_result = es.search(
                index=index,
                _source=['item_id','bucket_id'],
                size=count['count']
            )

            # 取得結果のドキュメント部のみを抽出
            hits_documents = search_result['hits']['hits']

            for document in hits_documents:
                if not 'index_id' in document['_source']:
                    # buckets_idからindex_idを取得
                    index_id_result = get_index_list(cur,document)

                    # ドキュメントにindex_idを追加
                    es.update(
                        index=document['_index'],
                        doc_type=document['_type'],
                        id=document['_id'],
                        body={'doc': {'index_id': index_id_result}}
                    )

            #add is_open_access
            current_app.logger.info('add is_open_access')

            # ダウンロード履歴のあるファイルのIDを取得
            item_id_list = list(set(d.get('_source').get('item_id') for d in hits_documents))

            # item_idでループ
            for item_id in item_id_list:
                # item_idが一致するドキュメントを取得
                resp = es.search(
                    index=index,
                    size=count['count'],
                    body={'query': {'term': {'item_id': item_id}}}
                )

                # 取得結果のドキュメント部のみを抽出
                documents = resp['hits']['hits']
                
                # メタデータ取得
                cur.execute("SELECT \
                                json, updated \
                            FROM \
                                item_metadata_version \
                            WHERE \
                                json ->> 'id' = '{}'"
                            .format(item_id))
                results = cur.fetchall()
                file_data_list = []
                
                # テーブルの検索結果でループ
                for result in results:
                    # レコードのvalue単位でループ
                    for value in result[0].values():
                        # valueが要素を含むlist型、かつその1つ目の要素がdict型で、その中にaccessroleが含まれる場合
                        if type(value) == list and len(value) > 0 and type(value[0]) == dict and 'accessrole' in value[0].keys():
                            file_data_list.append({
                                'file_name': value[0]['filename'],
                                'access_role': value[0]['accessrole'],
                                'open_date': value[0]['date'][0]['dateValue'],
                                'update_date': result[1]
                            })
                # 取得したメタデータを更新日の降順でソート
                file_data_list = sorted(file_data_list, key=lambda x: x['update_date'], reverse=True)
                
                # 取得したドキュメントでループ
                for document in documents:
                    
                    # オープンアクセス判定の初期化
                    is_open_access = False
                    # is_open_accessのフィールドがない場合
                    if not 'is_open_access' in document['_source']:

                        # タイムゾーンを東京に変更したダウンロード実行日時を取得
                        download_date_str = document['_source']['timestamp']
                        download_date = datetime.datetime.strptime(download_date_str, '%Y-%m-%dT%H:%M:%S')
                        download_date = timezone_from.localize(download_date)
                        download_date = download_date.astimezone(timezone_to)

                        # インデックスの公開状態の確認
                        # public_state = True かつ (download >= public_date または download >= created(public_dateがnullの場合))
                        # 親がいる場合は親も公開状態であること

                        public_index_list = Indexes.get_public_indexes_list()

                        is_index_open = False
                        target_index_list = []
                        cur.execute("SELECT \
                                json \
                            FROM \
                                records_metadata_version \
                            WHERE \
                                json -> '_buckets' ->> 'deposit' = '{}'"
                            .format(document['_source']['bucket_id']))
                        metadata_results = cur.fetchall()
                        index_list = get_index_list(cur,document)
                        target_index_list = index_list.split('|')
                        for metadata in metadata_results:
                            for record in metadata:
                                if not set(public_index_list).isdisjoint(target_index_list) \
                                and check_publish_status(record,download_date,timezone_from,timezone_to):
                                        is_index_open = True

                        current_app.logger.info("is_index_open",is_index_open)

                        if is_index_open:
                            # accessroleの値を取得
                            accessrole = document['_source']['accessrole']
                            # accessroleがopen_accessの場合、オープンアクセス判定をTrueに設定する
                            if accessrole == 'open_access':
                                is_open_access = True
                            # accessroleがopen_dateの場合
                            elif accessrole == 'open_date':
                                # メタデータのリストでループ
                                for file_data in file_data_list:
                                    # タイムゾーンを東京に変更したメタデータ更新日時を取得
                                    update_date = file_data['update_date']
                                    update_date = timezone_from.localize(update_date)
                                    update_date = update_date.astimezone(timezone_to)
                                    # ダウンロード実行日時がメタデータ更新日時より大きい場合
                                    if download_date >= update_date:
                                        # ダウンロードしたファイル名とメタデータに登録されているファイル名をそれぞれ取得
                                        download_file_name = document['_source']['file_key']
                                        item_file_name = file_data['file_name']
                                        # ファイル名が一致した場合、そのメタデータはダウンロード時のメタデータとなる
                                        if item_file_name == download_file_name:
                                            # メタデータの公開日を取得
                                            open_date_str = file_data['open_date']
                                            open_date = datetime.datetime.strptime(open_date_str, '%Y-%m-%d')
                                            # ダウンロード実行日時が公開日以降の場合、オープンアクセス判定をTrueに設定する
                                            if download_date.date() >= open_date.date():
                                                is_open_access = True
                                            # オープンアクセス判定が終わったため、メタデータのループを停止する
                                            break
                            
                        #ドキュメントにオープンアクセス判定を追加
                        es.update(
                            index=document['_index'],
                            doc_type=document['_type'],
                            id=document['_id'],
                            body={'doc': {'is_open_access': is_open_access}}
                        )
                        current_app.logger.info("update is_open_access",is_open_access)

        current_app.logger.info('add is_open_access completed')
        return 'all completed'
    except Exception as e:
        current_app.logger.info('error:{}'.format(e))
        raise e



def elasticsearch_reindex(value):
    """ 
    reindex *-record-view-*,*-file-download-*,*-file-preview-* of elasticsearch index

    Args:
        value (dict): elastic search index information 
    
    Returns:
        str : 'completed' 
        
    Raises:
        AssersionError :
        In case of the response code from ElasticSearch is not 200,
        Subsequent processing is interrupted.
    """
    # consts
    elasticsearch_host = os.environ.get('INVENIO_ELASTICSEARCH_HOST') 
    base_url = 'http://' + elasticsearch_host + ':9200/'
    reindex_url = base_url + '_reindex?pretty&refresh=true&wait_for_completion=true'
    
    # "{}-v1.0.0".format(prefix)
    index = value['index']
    tmpindex = "{}-tmp".format(index)
    
    # alias format(prefix)
    alias_name = value['alias_name']

    file_path = './modules/invenio-stats/invenio_stats/contrib' + value['file_path']
    with open(file_path,mode='r') as json_file:
        json_data = json_file.read()
        base_index_definition = orjson.loads(json_data)

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
    assert response.status_code == 200 ,response.text
    current_app.logger.info("add setting percolator") 

    current_app.logger.info("END create tmpindex") 
    
    # 高速化を期待してインデックスの設定を変更。
    current_app.logger.info("START change setting for faster") 
    response = requests.put(base_url + tmpindex + "/_settings?pretty", headers=headers ,json={ "index" : {"number_of_replicas" : 0, "refresh_interval": -1 }})
    current_app.logger.info(response.text)
    assert response.status_code == 200 ,response.text 
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
    # 一時保管用のインデックスから、新しく作成したインデックスに再インデックスを行う
    # reindex from tmpindex to index
    current_app.logger.info("reindex es from es")
    response = requests.post(url=reindex_url , headers=headers, json=json_data_to_dest)
    current_app.logger.info(response.text)
    assert response.status_code == 200 ,response.text
    current_app.logger.info("END reindex")

    # 高速化を期待して変更したインデックスの設定を元に戻す。
    current_app.logger.info("START revert setting for faster") 
    response = requests.put(base_url + index + "/_settings?pretty", headers=headers ,json={ "index" : {"number_of_replicas" : 1, "refresh_interval": value['refresh_interval'] }})
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

def get_index_list(cur,document):
    """get index list from elasticsearch document

    Args:
        cur (object): psycopg2 cursor object
        document (object): elasticsearch document

    Returns:
        str : index list
    """
    index_id_list = []
    str_index_id_list = ""
    bucket_id = document['_source']['bucket_id']
    cur.execute("SELECT \
                    json ->> 'path' \
                FROM \
                    records_metadata_version \
                WHERE \
                    json -> '_buckets' ->> 'deposit' = '{}'"
                .format(bucket_id))
    record_results = cur.fetchall()
    index_id_list.extend([result[0] for result in record_results if result[0] is not None])
    for index_id in set(index_id_list):
        id1 = index_id.replace('[', '')
        id2 = id1.replace(']', '')
        id3 = id2.replace('"', '')
        id = id3.replace(' ', '')
        path = id.replace(',', '|')
        str_index_id_list += str(path) + '|'
    index_id_result = str_index_id_list[:len(str_index_id_list) - 1]

    return index_id_result

def check_publish_status(record,download_date,timezone_from,timezone_to):
    """Check Publish Status.
    Args:
        record (dict): record
        download_date (datetime): download date
        timezone_from (pytz.timezone): timezone
        timezone_to (pytz.timezone): timezone

    Returns:
        bool : True or False
    """
    result = False
    pst = record.get('publish_status')
    pdt = record.get('pubdate', {}).get('attribute_value')
    try:
        # offset-naive
        pdt = datetime.datetime.strptime(pdt, '%Y-%m-%d')
        pdt = pdt.replace(tzinfo=timezone_from)
        pdt = pdt.astimezone(timezone_to)
        # offset-naive
        pdt = True if download_date >= pdt else False
    except BaseException as e:
        current_app.logger.error(e)
        pdt = False
    # if it's publish
    if pst and '0' in pst and pdt:
        result = True

    current_app.logger.info("check_publish_status result",result)
    return result

if __name__ == '__main__':
    reindex_and_add_items()