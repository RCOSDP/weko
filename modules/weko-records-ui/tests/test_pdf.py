import pytest
import uuid
import copy
import json
from mock import MagicMock, patch
from six import BytesIO

from invenio_files_rest.models import Bucket, Location, ObjectVersion
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_pidrelations.contrib.versioning import PIDVersioning
from invenio_pidrelations.contrib.records import RecordDraft
from invenio_records_files.models import RecordsBuckets

from weko_deposit.api import WekoIndexer, WekoRecord
from weko_deposit.api import WekoDeposit as aWekoDeposit
from weko_records.models import ItemType, ItemTypeMapping, ItemTypeName
from weko_records.api import ItemsMetadata

from weko_records_ui.pdf import get_east_asian_width_count,make_combined_pdf


# def get_east_asian_width_count(text):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_pdf.py::test_get_east_asian_width_count -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_get_east_asian_width_count():
    assert get_east_asian_width_count("日本語")==6
    assert get_east_asian_width_count("english")==7
    

def make_record(indexer, id, publisher, subjects, creator,affiliation, lang_langs, is_license=False):
    filepath = "tests/data/helloworld.pdf"
    filename = "helloworld.pdf"
    mimetype = "application/pdf"
    file_head=True
    licensetype = "licensefree" if is_license else ""
    licensefree = "test_license" if is_license else ""
    record_data = {
        "_oai":{"id":"oai:weko3.example.org:000000{}".format(id),"sets":["1710997084761"]},
        "path": ["1710997084761"],
        "owner":"1","recid":id,
        "title":["title1"],
        "pubdate":{"attribute_name":"PubDate","attribute_value":"2024-03-21"},
        "_buckets":{},
        "_deposit":{
            "id":id,"pid":{"type":"depid","value":id,"revision_id":0},
            "owner":"1","owners":[1],"status":"published"
        },
        "item_title":"title1",
        "author_link":[],
        "itemtype_id":"xxxxx",
        "publish_date":"2024-03-21","publish_status":"0","weko_shared_id":-1,
        "item_1711081249402":{"attribute_name":"Title","attribute_value_mlt":[{"subitem_title":"title1","subitem_title_language":"ja"}]},
        "item_1711081258940":{"attribute_name":"language01","attribute_value_mlt":[{"subitem_language":lang_langs[0]}]},
        "item_1711083729173":{"attribute_name":"language02","attribute_value_mlt":[{"subitem_language":lang} for lang in lang_langs]},
        "item_1711081274859":{
            "attribute_name":"publisher01",
            "attribute_value_mlt":[
                {"subitem_publisher": publisher["val"], "subitem_publisher_language": publisher["lang"]}
            ]
        },
        "item_1711081333893":{
            "attribute_name":"subject01",
            "attribute_value_mlt":[
                {"subitem_subject": subject["val"], "subitem_subject_language": subject["lang"]} for subject in subjects
            ]
        },
        "item_1711081408726":{
            "attribute_name":"creator01","attribute_type":"creator",
            "attribute_value_mlt":[
                {
                    "creatorMails":[{"creatorMail":"test.taro@test.org"}],
                    "creatorNames":[{"creatorName": creator["val"],"creatorNameLang":creator["lang"]}],
                    "nameIdentifier":[{"nameIdentifier":"1","nameIdentifierScheme":"WEKO"}],
                    "creatorAffiliations":[{"affiliationNames":[{"affiliationName":affiliation["val"],"affiliationNameLang":affiliation["lang"]}]}]
                }
            ]
        },
        "item_1617605131499":{
            "attribute_name":"File","attribute_type":"file",
            "attribute_value_mlt":[
                {
                    "url":{"url":"https://weko3.example.org/record/{0}/files/{1}".format(id,filename)},
                    "date": [{"dateType": "Available","dateValue": "2024-03-21"}],
                    "format": mimetype,"filename":filename,"filesize":[{"value":"10 KB"}],
                    "accessrole": "open_access",
                    "version_id": "94b16710-d2a5-4fbb-8915-9b63f3eaf21e",
                    "licensetype":licensetype,
                    "licensefree":licensefree
                }
            ]
        }
    }

    item_data = {
        "id":id,"pid":{"type":"depid","value":id,"revision_id":0},
        "lang":"ja","owner":"1","title":"title1","owners":[1],"status":"published",
        "$schema":"/items/jsonschema/xxxxx",
        "pubdate":"2024-03-21","created_by":1,"shared_user_id":-1,
        "item_1711081249402": [{"subitem_title": "title1","subitem_title_language": "ja"}],
        "item_1711081258940":{"subitem_language":lang_langs[0]},
        "item_1711083729173":[{"subitem_language":lang} for lang in lang_langs],
        "item_1711081274859": [{"subitem_publisher": publisher["val"],"subitem_publisher_language": publisher["lang"]}],
        "item_1711081333893": [{"subitem_subject": subject["val"],"subitem_subject_language": subject["lang"]} for subject in subjects],
        "item_1711081408726": [
            {
                "creatorMails":[{"creatorMail":"test.taro@test.org"}],
                "creatorNames":[{"creatorName":creator["val"],"creatorNameLang":creator["lang"]}],
                "nameIdentifiers":[{"nameIdentifier":"1","nameIdentifierScheme":"WEKO"}],
                "creatorAffiliations":[{"affiliationNames":[{"affiliationName":affiliation["val"],"affiliationNameLang":affiliation["lang"]}]}]
            }
        ],
        "item_1617605131499":[
            {
                "url": {"url": "https://weko3.example.org/record/{}/files/{}".format(id,filename)},
                "date":[{"dateType":"Available","dateValue":"2024-03-21"}],
                "format":mimetype, "filename":filename,"filesize":[{"value":"10 KB"}],
                "accessrole":"open_access","version_id": "94b16710-d2a5-4fbb-8915-9b63f3eaf21e",
                "licensetype":licensetype,"licensefree":licensefree
            }
        ]
    }
    
    
    rec_uuid = uuid.uuid4()

    recid = PersistentIdentifier.create(
        "recid",
        str(id),
        object_type="rec",
        object_uuid=rec_uuid,
        status=PIDStatus.REGISTERED,
    )
    depid = PersistentIdentifier.create(
        "depid",
        str(id),
        object_type="rec",
        object_uuid=rec_uuid,
        status=PIDStatus.REGISTERED,
    )
    parent = None
    doi = None
    hdl = None
    recid_v1 = PersistentIdentifier.create(
        "recid",
        str(id + 0.1),
        object_type="rec",
        object_uuid=rec_uuid,
        status=PIDStatus.REGISTERED,
    )
    rec_uuid2 = uuid.uuid4()
    depid_v1 = PersistentIdentifier.create(
        "depid",
        str(id + 0.1),
        object_type="rec",
        object_uuid=rec_uuid2,
        status=PIDStatus.REGISTERED,
    )
    parent = PersistentIdentifier.create(
        "parent",
        "parent:{}".format(id),
        object_type="rec",
        object_uuid=rec_uuid2,
        status=PIDStatus.REGISTERED,
    )

    h1 = PIDVersioning(parent=parent)
    h1.insert_child(child=recid)
    h1.insert_child(child=recid_v1)
    RecordDraft.link(recid, depid)
    RecordDraft.link(recid_v1, depid_v1)

    if id % 2 == 1:
        doi = PersistentIdentifier.create(
            "doi",
            "https://doi.org/10.xyz/{}".format((str(id)).zfill(10)),
            object_type="rec",
            object_uuid=rec_uuid,
            status=PIDStatus.REGISTERED,
        )
        hdl = PersistentIdentifier.create(
            "hdl",
            "https://hdl.handle.net/0000/{}".format((str(id)).zfill(10)),
            object_type="rec",
            object_uuid=rec_uuid,
            status=PIDStatus.REGISTERED,
        )

    record = WekoRecord.create(record_data, id_=rec_uuid)
    # from six import BytesIO
    import base64

    bucket = Bucket.create()
    record_buckets = RecordsBuckets.create(record=record.model, bucket=bucket)

    # stream = BytesIO(b"Hello, World")
    obj = None
    with open(filepath, "rb") as f:
        stream = BytesIO(f.read())
        record.files[filename] = stream
        record["item_1617605131499"]["attribute_value_mlt"][0]["file"] = (
            base64.b64encode(stream.getvalue())
        ).decode("utf-8")
    with open(filepath, "rb") as f:
        obj = ObjectVersion.create(bucket=bucket.id, key=filename, stream=f)
        obj.is_head = file_head
    deposit = aWekoDeposit(record, record.model)
    deposit.commit()
    record["item_1617605131499"]["attribute_value_mlt"][0]["version_id"] = str(
        obj.version_id
    )

    record_data["content"] = [
        {
            "date": [{"dateValue": "2021-07-12", "dateType": "Available"}],
            "accessrole": "open_access",
            "displaytype": "simple",
            "filename": filename,
            "attachment": {},
            "format": mimetype,
            "mimetype": mimetype,
            "filesize": [{"value": "1 KB"}],
            "version_id": "{}".format(obj.version_id),
            "url": {"url": "http://localhost/record/{0}/files/{1}".format(id, filename)},
            "file": (base64.b64encode(stream.getvalue())).decode("utf-8"),
        }
    ]
    indexer.upload_metadata(record_data, rec_uuid, 1, False)
    item = ItemsMetadata.create(item_data, id_=rec_uuid, item_type_id=1)

    record_v1 = WekoRecord.create(record_data, id_=rec_uuid2)
    # from six import BytesIO
    import base64

    bucket_v1 = Bucket.create()
    record_buckets = RecordsBuckets.create(record=record_v1.model, bucket=bucket_v1)
    # stream = BytesIO(b"Hello, World")
    record_v1.files[filename] = stream
    obj_v1 = ObjectVersion.create(bucket=bucket_v1.id, key=filename, stream=stream)
    obj_v1.is_head = False
    record_v1["item_1617605131499"]["attribute_value_mlt"][0]["file"] = (
        base64.b64encode(stream.getvalue())
    ).decode("utf-8")
    deposit_v1 = aWekoDeposit(record_v1, record_v1.model)
    deposit_v1.commit()
    record_v1["item_1617605131499"]["attribute_value_mlt"][0]["version_id"] = str(
        obj_v1.version_id
    )

    record_data_v1 = copy.deepcopy(record_data)
    record_data_v1["content"] = [
        {
            "date": [{"dateValue": "2021-07-12", "dateType": "Available"}],
            "accessrole": "open_access",
            "displaytype": "simple",
            "filename": filename,
            "attachment": {},
            "format": mimetype,
            "mimetype": mimetype,
            "filesize": [{"value": "1 KB"}],
            "version_id": "{}".format(obj_v1.version_id),
            "url": {"url": "http://localhost/record/{0}/files/{1}".format(id, filename)},
            "file": (base64.b64encode(stream.getvalue())).decode("utf-8"),
        }
    ]
    indexer.upload_metadata(record_data_v1, rec_uuid2, 1, False)
    item_v1 = ItemsMetadata.create(item_data, id_=rec_uuid2, item_type_id=1)
    return record

# def make_combined_pdf(pid, fileobj, obj, lang_user):
#     def pixels_to_mm(val):
#     def resize_to_fit(imgFilename):
#     def get_center_position(imgFilename):
#     def get_right_position(imgFilename):
#     def get_pid_object(pid_value):
#     def get_current_activity_id(pid_object):
#     def get_url(pid_value):
#     def get_oa_policy(activity_id):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_pdf.py::test_make_combined_pdf -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_make_combined_pdf(app, db, esindex, location, pdfcoverpagesetting, mocker):
    temp_path = "tests/data"
    mocker.patch("weko_records_ui.pdf.tempfile.gettempdir", return_value=temp_path)
    import shutil, os
    if os.path.isdir(temp_path+"/comb_pdfs"):
        shutil.rmtree(temp_path+"/comb_pdfs")
    item_type_name = ItemTypeName(id=1, name="test_itemtype")
    item_type_schema = dict()
    with open("tests/data/item_type_schema_pdftest.json", "r") as f:
        item_type_schema = json.load(f)

    item_type_form = dict()
    with open("tests/data/item_type_form_pdftest.json", "r") as f:
        item_type_form = json.load(f)

    item_type_render = dict()
    with open("tests/data/item_type_render_pdftest.json", "r") as f:
        item_type_render = json.load(f)

    item_type_mapping = dict()
    with open("tests/data/item_type_mapping_pdftest.json", "r") as f:
        item_type_mapping = json.load(f)
    item_type = ItemType(
        id=1, name_id=1, schema=item_type_schema, form=item_type_form, render=item_type_render, tag=1
    )
    itemtype_mapping = ItemTypeMapping(id=1, item_type_id=1, mapping=item_type_mapping)
    with db.session.begin_nested():
        db.session.add(item_type_name)
        db.session.add(item_type)
        db.session.add(itemtype_mapping)
    db.session.commit()
    indexer = WekoIndexer()
    indexer.get_es_index()
    records = []
    records.append(make_record(indexer, 1, {"val": "test_publisher", "lang": "en"}, [{"val": "test_subject", "lang": "en"}, {"val": "テスト主題", "lang": "ja"}], {"val": "test, taro", "lang": "en"}, {"val": "test_affiliation", "lang": "en"}, ["eng"]))
    records.append(make_record(indexer, 2, {"val": "test_publisher", "lang": ""  }, [{"val": "test_subject", "lang": "en"}, {"val": "テスト主題", "lang": "ja"}], {"val": "test, taro", "lang": ""  }, {"val": "test_affiliation", "lang": ""  }, ["jpn", "eng"]))
    records.append(make_record(indexer, 3, {"val": ""              , "lang": "en"}, [{"val": "test_subject", "lang": "en"}, {"val": "テスト主題", "lang": "ja"}], {"val": ""          , "lang": "en"}, {"val": ""                , "lang": "en"}, ["fra", "jpn"],True))
    records.append(make_record(indexer, 4, {"val": "test_publisher", "lang": "en"}, [{"val": "", "lang": ""}], {"val": "test, taro", "lang": "en"}, {"val": "test_affiliation", "lang": "en"}, ["eng"]))
    db.session.commit()
    
    tests = [
        (
            "Language: English\nPublisher: test_publisher\nDate of Publication: 2024-03-21\nKeywords: test_subject\nAuthor: test, taro\nE-mail: \nAffiliation: test_affiliation",
            "言語: English\n出版者: test_publisher\n公開日: 2024-03-21\nキーワード: テスト主題\n作成者: test, taro\nメールアドレス: \n所属: test_affiliation",
            "Language: English\nPublisher: test_publisher\nDate of Publication: 2024-03-21\nKeywords: test_subject\nAuthor: test, taro\nE-mail: test.taro@test.org\nAffiliation: test_affiliation",
            "Language: English\nPublisher: \nDate of Publication: 2024-03-21\nKeywords: \nAuthor: \nE-mail: \nAffiliation: "
        ),
        (
            "Language: Japanese\nPublisher: \nDate of Publication: 2024-03-21\nKeywords: test_subject\nAuthor: \nE-mail: \nAffiliation: ",
            "言語: Japanese\n出版者: \n公開日: 2024-03-21\nキーワード: テスト主題\n作成者: \nメールアドレス: \n所属: ",
            "Language: Japanese\nPublisher: \nDate of Publication: 2024-03-21\nKeywords: test_subject\nAuthor: \nE-mail: test.taro@test.org\nAffiliation: ",
            "Language: Japanese, English\nPublisher: \nDate of Publication: 2024-03-21\nKeywords: \nAuthor: \nE-mail: \nAffiliation: "
        ),
        (
            "Language: fra\nPublisher: \nDate of Publication: 2024-03-21\nKeywords: test_subject\nAuthor: \nE-mail: \nAffiliation: ",
            "言語: fra\n出版者: \n公開日: 2024-03-21\nキーワード: テスト主題\n作成者: \nメールアドレス: \n所属: ",
            "Language: fra\nPublisher: \nDate of Publication: 2024-03-21\nKeywords: test_subject\nAuthor: \nE-mail: test.taro@test.org\nAffiliation: ",
            "Language: fra, Japanese\nPublisher: \nDate of Publication: 2024-03-21\nKeywords: \nAuthor: \nE-mail: \nAffiliation: "
        ),
        (
            "Language: English\nPublisher: test_publisher\nDate of Publication: 2024-03-21\nKeywords: \nAuthor: test, taro\nE-mail: \nAffiliation: test_affiliation",
            "言語: English\n出版者: test_publisher\n公開日: 2024-03-21\nキーワード: \n作成者: test, taro\nメールアドレス: \n所属: test_affiliation",
            "Language: English\nPublisher: test_publisher\nDate of Publication: 2024-03-21\nKeywords: \nAuthor: test, taro\nE-mail: test.taro@test.org\nAffiliation: test_affiliation",
            "Language: English\nPublisher: \nDate of Publication: 2024-03-21\nKeywords: \nAuthor: \nE-mail: \nAffiliation: "
        )
    ]

    filename = "helloworld.pdf"
    mock_page_setting = MagicMock()
    mock_page_setting.header_output_string = "Weko Univ"
    from fpdf import FPDF
    mock_multi_cell = mocker.spy(FPDF, "multi_cell")
    with patch("weko_records_ui.pdf.PDFCoverPageSettings.find", return_value=mock_page_setting):
        for i, record in enumerate(records):
            fileobj = record.files[filename]
            obj = fileobj.obj
            # header_display_position=left, header_desplay_type=string, 
            mock_page_setting.header_output_image = "tests/data/image01.jpg"
            mock_page_setting.header_display_position = "left"
            mock_page_setting.header_display_type = "string"
            with app.test_request_context(headers=[('Accept-Language', 'en')]):
                res = make_combined_pdf(record.pid, fileobj, obj, None)
            args_list = mock_multi_cell.call_args_list
            assert args_list[2][0][3] == tests[i][0]
            mock_multi_cell.call_args_list.clear()

            # header_display_position=center, header_output_image_name is exist, header_desplay_type=Image, 
            mock_page_setting.header_display_position = "center"
            mock_page_setting.header_output_image = "tests/data/image01.jpg"
            mock_page_setting.header_display_type = "Image"
            with app.test_request_context(headers=[('Accept-Language', 'ja')]):
                res = make_combined_pdf(record.pid, fileobj, obj, None)
            args_list = mock_multi_cell.call_args_list
            assert args_list[1][0][3] == tests[i][1]
            mock_multi_cell.call_args_list.clear()

            # header_display_position=center, header_output_image_name is not  exist, header_desplay_type=Image, 
            mock_page_setting.header_display_position = "center"
            mock_page_setting.header_output_image = ""
            mock_page_setting.header_display_type = "Image"
            with app.test_request_context(headers=[('Accept-Language', 'fr')]):
                res = make_combined_pdf(record.pid, fileobj, obj, None)
            args_list = mock_multi_cell.call_args_list
            assert args_list[1][0][3] == tests[i][0]
            mock_multi_cell.call_args_list.clear()

            # header_display_position=right, header_output_image_name is exist, header_desplay_type=string, 
            mock_page_setting.header_display_position = "right"
            mock_page_setting.header_output_image = "tests/data/image01.jpg"
            mock_page_setting.header_display_type = "string"
            res = make_combined_pdf(record.pid, fileobj, obj, None)
            args_list = mock_multi_cell.call_args_list
            assert args_list[2][0][3] == tests[i][0]
            mock_multi_cell.call_args_list.clear()

            # header_display_position=right, header_output_image_name isnot  exist, header_desplay_type=string, 
            mock_page_setting.header_display_position = "right"
            mock_page_setting.header_output_image = ""
            mock_page_setting.header_display_type = "string"
            res = make_combined_pdf(record.pid, fileobj, obj, None)
            args_list = mock_multi_cell.call_args_list
            assert args_list[2][0][3] == tests[i][0]
            mock_multi_cell.call_args_list.clear()

            # header_display_position=left, header_output_image_name is not exist, header_desplay_type=string, 
            # item_setting_show_email is True
            mock_page_setting.header_display_position = "left"
            mock_page_setting.header_output_image = ""
            mock_page_setting.header_display_type = "string"
            with patch("weko_records_ui.pdf.item_setting_show_email", return_value=True):
                res = make_combined_pdf(record.pid, fileobj, obj, None)
                args_list = mock_multi_cell.call_args_list
                assert args_list[2][0][3] == tests[i][2]
                mock_multi_cell.call_args_list.clear()
            
            # publisher, subject, creatorMail, creatorName, affiliationName are hide,
            # language is list
            hide_list = [
                "item_1711081274859.subitem_publisher",
                "item_1711081333893.subitem_subject",
                "item_1711081408726.creatorMails.creatorMail",
                "item_1711081408726.creatorNames.creatorName",
                "item_1711081408726.creatorAffiliations.affiliationNames.affiliationName"
            ]
            item_map = {
                "title.@value": "item_1711081249402.subitem_title",
                "title.@attributes.xml:lang": "item_1711081249402.subitem_title_language",
                "language.@value": "item_1711083729173.subitem_language",
                "publisher.@value": "item_1711081274859.subitem_publisher",
                "publisher.@attributes.xml:lang": "item_1711081274859.subitem_publisher_language",
                "subject.@value": "item_1711081333893.subitem_subject",
                "subject.@attributes.xml:lang": "item_1711081333893.subitem_subject_language",
                "subject.@attributes.subjectURI": "item_1711081333893.subitem_subject_uri",
                "subject.@attributes.subjectScheme": "item_1711081333893.subitem_subject_scheme",
                "creator.affiliation.nameIdentifier.@value": "item_1711081408726.creatorAffiliations.affiliationNameIdentifiers.affiliationNameIdentifier",
                "creator.affiliation.nameIdentifier.@attributes.nameIdentifierURI": "item_1711081408726.creatorAffiliations.affiliationNameIdentifiers.affiliationNameIdentifierURI",
                "creator.affiliation.nameIdentifier.@attributes.nameIdentifierScheme": "item_1711081408726.creatorAffiliations.affiliationNameIdentifiers.affiliationNameIdentifierScheme",
                "creator.affiliation.affiliationName.@value": "item_1711081408726.creatorAffiliations.affiliationNames.affiliationName",
                "creator.affiliation.affiliationName.@attributes.xml:lang": "item_1711081408726.creatorAffiliations.affiliationNames.affiliationNameLang",
                "creator.creatorName.@value": "item_1711081408726.creatorNames.creatorName",
                "creator.creatorName.@attributes.xml:lang": "item_1711081408726.creatorNames.creatorNameLang",
                "creator.creatorAlternative.@value": "item_1711081408726.creatorAlternatives.creatorAlternative",
                "creator.creatorAlternative.@attributes.xml:lang": "item_1711081408726.creatorAlternatives.creatorAlternativeLang",
                "type.@value": "item_1711083182141.resourcetype",
                "type.@attributes.rdf:resource": "item_1711083182141.resourceuri",
                "file.URI.@value": "item_1711083273218.url.url",
                "file.URI.@attributes.label": "item_1711083273218.url.label",
                "file.URI.@attributes.objectType": "item_1711083273218.url.objectType",
                "file.date.@value": "item_1711083273218.fileDate.fileDateValue",
                "file.date.@attributes.dateType": "item_1711083273218.fileDate.fileDateType",
                "file.extent.@value": "item_1711083273218.filesize.value",
                "file.version.@value": "item_1711083273218.version",
                "file.mimeType.@value": "item_1711083273218.format"
            }
            with patch("weko_items_ui.utils.get_hide_list_by_schema_form", return_value=hide_list):
                with patch("weko_records_ui.pdf.get_mapping", return_value=item_map):
                    res = make_combined_pdf(record.pid, fileobj, obj, None)
            args_list = mock_multi_cell.call_args_list
            assert args_list[2][0][3] == tests[i][3]
            mock_multi_cell.call_args_list.clear()
            
            # publisher, subject, creator are not exist
            item_map = {
                "title.@value": "item_1711081249402.subitem_title",
                "title.@attributes.xml:lang": "item_1711081249402.subitem_title_language"
            }
            with patch("weko_records_ui.pdf.get_mapping",return_value=item_map):
                res = make_combined_pdf(record.pid, fileobj, obj, None)
            args_list = mock_multi_cell.call_args_list
            assert args_list[2][0][3] == "Language: ja\nPublisher: \nDate of Publication: 2024-03-21\nKeywords: \nAuthor: \nE-mail: \nAffiliation: "
            mock_multi_cell.call_args_list.clear()
    if os.path.isdir(temp_path+"/comb_pdfs"):
        shutil.rmtree(temp_path+"/comb_pdfs")