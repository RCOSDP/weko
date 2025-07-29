import pytest
from mock import MagicMock, patch ,sentinel
from invenio_pidstore.models import PersistentIdentifier
from weko_items_ui.models import CRIS_Institutions, CRISLinkageResult
from weko_items_ui.tasks import build_achievement, build_one_data, bulk_post_item_to_researchmap, get_achievement_type, get_merge_mode, process_researchmap_queue ,get_item,is_public, register_linkage_result,get_authors
from weko_records.api import Mapping
from weko_records.models import ItemMetadata, ItemTypeMapping
from weko_records.utils import json_loader

# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_tasks.py::test_bulk_post_item_to_researchmap -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko_items-ui/.tox/c1/tmp
def test_bulk_post_item_to_researchmap(app):
    with patch('weko_items_ui.tasks.process_researchmap_queue' , return_value = ""):
        with patch('weko_items_ui.tasks.current_celery_app' , return_value = MagicMock()):
            with patch('weko_items_ui.tasks.current_app' , return_value = MagicMock()):
                message = MagicMock()
                with patch('weko_items_ui.tasks.Consumer.iterqueue' , return_value = [message, None]):
                        bulk_post_item_to_researchmap()

# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_tasks.py::test_process_researchmap_queue -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko_items_ui/.tox/c1/tmp --full-trace
def test_process_researchmap_queue(app ,db, db_records_researchmap):
    # item = ItemsMetadata.create(db_records[0][0].object_uuid, id_=rec_uuid)
    db.session.commit()
    # process_researchmap_queue({"item_uuid" : db_records_researchmap[0]}  ,MagicMock())
    with patch('weko_items_ui.models.CRISLinkageResult.register_linkage_result' , return_value = True):
        with patch('weko_items_ui.models.PersistentIdentifier.get_by_object' , side_effect = [Exception(),MagicMock()]):
            process_researchmap_queue({"item_uuid" : db_records_researchmap[0]}  ,MagicMock())
        process_researchmap_queue({"item_uuid" : db_records_researchmap[0]}  ,MagicMock())
        with patch('weko_items_ui.tasks.check_publish_status' , return_value = True):
            with patch('weko_items_ui.tasks.is_private_index' , return_value = False):
                process_researchmap_queue({"item_uuid" : db_records_researchmap[0]}  ,MagicMock())
                with patch('weko_items_ui.tasks.get_authors' , return_value = ["auth1","auth2"]):
                    process_researchmap_queue({"item_uuid" : db_records_researchmap[0]}  ,MagicMock())
                    with patch('weko_items_ui.tasks.get_achievement_type' , return_value = {}):
                        with patch('weko_items_ui.tasks.build_achievement' , return_value = None):
                            process_researchmap_queue({"item_uuid" : db_records_researchmap[0]}  ,MagicMock())
                    with patch('weko_items_ui.tasks.get_achievement_type' , return_value = {"hoge":"fuga"}):
                        with patch('weko_items_ui.tasks.build_achievement' , return_value = {}):
                            with patch('weko_items_ui.tasks.Researchmap.post_data' , return_value = '{"url" : "hoge"}'):
                                with patch('weko_items_ui.tasks.Researchmap.get_result' , return_value = '{"code" : 200}'):
                                    process_researchmap_queue({"item_uuid" : db_records_researchmap[0]}  ,MagicMock())

# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_tasks.py::test_get_item -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko_items_ui/.tox/c1/tmp --full-trace
def test_get_item(app , db_records):
    assert get_item(db_records[0][0].object_uuid)

def test_is_public():
    with patch('weko_items_ui.tasks.check_publish_status' , return_value = True):
        with patch('weko_items_ui.tasks.is_private_index' , return_value = False):
            assert is_public("hoge" , "") == True
    
        with patch('weko_items_ui.tasks.is_private_index' , return_value = True):
            assert is_public("hoge" , "") == False

    with patch('weko_items_ui.tasks.check_publish_status' , return_value = False):
        with patch('weko_items_ui.tasks.is_private_index' , return_value = True):
            assert is_public("hoge" , "") == False

def test_get_authors(db_author):
    assert get_authors({"author_link" : ['1']})

# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_tasks.py::test_get_merge_mode -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko_items_ui/.tox/c1/tmp --full-trace
def test_get_merge_mode(app ,db_admin_setting):
    assert get_merge_mode()
    with patch("weko_items_ui.tasks.AdminSettings.get" , return_value={}):
        assert get_merge_mode()

# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_tasks.py::test_get_achievement_type -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko_items-ui/.tox/c1/tmp
def test_get_achievement_type(app):
    assert get_achievement_type({"type" : ["article"]}) == 'published_papers'
    assert get_achievement_type({"type" : ["hoge"]}) == None

# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_tasks.py::test_build_achievement -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko_items-ui/.tox/c1/tmp
def test_build_achievement(app,db_records_researchmap):
    recid = PersistentIdentifier.get_by_object(pid_type='recid', object_type='rec', object_uuid=db_records_researchmap[0]) 
    record,item = get_item(db_records_researchmap[0])
    # mapping = Mapping.get_record(item.item_type_id)
    mapping = ItemTypeMapping.query.filter(ItemTypeMapping.mapping != None).first().mapping
    #  db_itemtype_15["item_type_mapping"] 
    _ , jrc , _= json_loader(data=item.json ,pid=recid) 
    assert build_achievement(record,item,recid,mapping,jrc, 'published_papers')
    assert build_achievement(record,item,recid,mapping,jrc, 'misc')
    assert build_achievement(record,item,recid,mapping,jrc, 'books_etc')
    assert build_achievement(record,item,recid,mapping,jrc, 'presentations')
    assert build_achievement(record,item,recid,mapping,jrc, 'works')
    assert build_achievement(record,item,recid,mapping,jrc, 'others')
    recid = PersistentIdentifier.get_by_object(pid_type='recid', object_type='rec', object_uuid=db_records_researchmap[1]) 
    record,item = get_item(db_records_researchmap[1])
    _ , jrc , _= json_loader(data=item.json ,pid=recid) 
    assert build_achievement(record,item,recid,mapping,jrc, 'published_papers')
    assert build_achievement(record,item,recid,mapping,jrc, 'misc')
    assert build_achievement(record,item,recid,mapping,jrc, 'books_etc')
    assert build_achievement(record,item,recid,mapping,jrc, 'presentations')
    assert build_achievement(record,item,recid,mapping,jrc, 'works')
    assert build_achievement(record,item,recid,mapping,jrc, 'others')
    recid = PersistentIdentifier.get_by_object(pid_type='recid', object_type='rec', object_uuid=db_records_researchmap[2]) 
    record,item = get_item(db_records_researchmap[2])
    _ , jrc , _= json_loader(data=item.json ,pid=recid) 
    assert build_achievement(record,item,recid,mapping,jrc, 'published_papers')
    assert build_achievement(record,item,recid,mapping,jrc, 'misc')
    assert build_achievement(record,item,recid,mapping,jrc, 'books_etc')
    assert build_achievement(record,item,recid,mapping,jrc, 'presentations')
    assert build_achievement(record,item,recid,mapping,jrc, 'works')
    assert build_achievement(record,item,recid,mapping,jrc, 'others')

    # err cases
    recid = PersistentIdentifier.get_by_object(pid_type='recid', object_type='rec', object_uuid=db_records_researchmap[3]) 
    record,item = get_item(db_records_researchmap[3])
    _ , jrc , _= json_loader(data=item.json ,pid=recid) 
    assert build_achievement(record,item,recid,mapping,jrc, 'published_papers') == {
        "ending_page": None, "languages": None, "number": None, "published_paper_type": "",
        "see_also": [{'@id': 'https://weko3.example.org/records/19', "label": "url"}],
        "starting_page": None, "total_page": None, "volume": None
    }
    
    app.config.update(WEKO_ITEMS_UI_CRIS_LINKAGE_RESEARCHMAP_MAPPINGS= [{ 'type' : 'hoge' , "rm_name" : 'paper_title', "jpcoar_name" : 'dc:title' , "weko_name" :"title"}])
    assert build_achievement(record,item,recid,mapping,jrc, 'published_papers') == {"see_also": [{"@id": "https://weko3.example.org/records/19", "label": "url"}]}



# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_tasks.py::test_build_one_data -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko_items_ui/.tox/c1/tmp --full-trace
def test_build_one_data(app):
    assert build_one_data({"hoge" : "foo"} , 'merge' ,'author',"publish_papaers").get("merge") == {"hoge" : "foo"}
    assert build_one_data({"hoge" : "foo"} , 'force' ,'author',"publish_papaers").get("force") == {"hoge" : "foo"}
    assert build_one_data({} , 'similar_merge_similar_data' ,'author',"publish_papaers").get("priority") == "similar_data"
    assert build_one_data({} , 'similar_merge_input_data' ,'author',"publish_papaers").get("priority") == "input_data"
    assert {} == build_one_data({} , '' ,'author',"publish_papaers")

# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_tasks.py::test_register_linkage_result -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko_items_ui/.tox/c1/tmp --full-trace
def test_register_linkage_result(db,db_records):
    with patch('weko_items_ui.models.CRISLinkageResult.register_linkage_result' , return_value = True):
        assert register_linkage_result(db_records[0][0].pid_value , True , db_records[0][0].object_uuid, None )