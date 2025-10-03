import json
import copy
import uuid
from os.path import dirname, join
from flask import url_for

from invenio_db import db
from invenio_pidstore import current_pidstore
from invenio_pidstore.models import PersistentIdentifier, PIDStatus, RecordIdentifier
from invenio_pidrelations.models import PIDRelation
from weko_records.api import ItemsMetadata, WekoRecord
from weko_deposit.api import WekoIndexer, WekoDeposit, WekoRecord
from invenio_files_rest.models import Bucket, ObjectVersion
from invenio_records_files.models import RecordsBuckets


def json_data(filename):
    with open(join(dirname(__file__),filename), "r") as f:
        return json.load(f)


#def create_record(record_data, item_data):
#    """Create a test record."""
#    with db.session.begin_nested():
#        record_data = copy.deepcopy(record_data)
#        item_data = copy.deepcopy(item_data)
#        rec_uuid = uuid.uuid4()
#        recid = PersistentIdentifier.create(
#            'recid',
#            record_data['recid'],
#            object_type='rec',
#            object_uuid=rec_uuid,
#            status=PIDStatus.REGISTERED
#        )
#        depid = PersistentIdentifier.create(
#            'depid',
#            record_data['recid'],
#            object_type='rec',
#            object_uuid=rec_uuid,
#            status=PIDStatus.REGISTERED
#        )
#        record = WekoRecord.create(record_data, id_=rec_uuid)
#        item = ItemsMetadata.create(item_data, id_=rec_uuid)
#    return recid, record, item
def create_record(record_data, item_data):
    """Create a test record."""
    with db.session.begin_nested():
        record_data = copy.deepcopy(record_data)
        item_data = copy.deepcopy(item_data)
        rec_uuid = uuid.uuid4()
        recid = PersistentIdentifier.create('recid', record_data["recid"],object_type='rec', object_uuid=rec_uuid,status=PIDStatus.REGISTERED)
        depid = PersistentIdentifier.create('depid', record_data["recid"],object_type='rec', object_uuid=rec_uuid,status=PIDStatus.REGISTERED)
        rel = PIDRelation.create(recid,depid,3)
        db.session.add(rel)
        parent=None
        doi = None
        if "item_1617186819068" in record_data:
            doi_url = "https://doi.org/"+record_data["item_1617186819068"]["attribute_value_mlt"][0]["subitem_identifier_reg_text"]
            try:
                PersistentIdentifier.get("doi",doi_url)
            except PIDDoesNotExistError:
                doi = PersistentIdentifier.create('doi',doi_url,object_type='rec', object_uuid=rec_uuid,status=PIDStatus.REGISTERED)
        if '.' in record_data["recid"]:
            parent = PersistentIdentifier.get("recid",int(float(record_data["recid"])))
            recid_p = PIDRelation.get_child_relations(parent).one_or_none()
            PIDRelation.create(recid_p.parent, recid,2)
        else:
            parent = PersistentIdentifier.create('parent', "parent:{}".format(record_data["recid"]),object_type='rec', object_uuid=rec_uuid,status=PIDStatus.REGISTERED)
            rel = PIDRelation.create(parent, recid,2,0)
            db.session.add(rel)
            RecordIdentifier.next()
        record = WekoRecord.create(record_data, id_=rec_uuid)
        item = ItemsMetadata.create(item_data, id_=rec_uuid)
        deposit = WekoDeposit(record, record.model)

        deposit.commit()

    return recid, depid, record, item, parent, doi, deposit

def login(app, client, obj = None, email=None, password=None):
    """Log the user in with the test client."""
    with app.test_request_context():
        login_url = url_for('security.login')

    if obj:
        email = obj.email
        password = obj.password_plaintext
        client.post(login_url, data=dict(
            email=email or app.config['TEST_USER_EMAIL'],
            password=password or app.config['TEST_USER_PASSWORD'],
        ))
    else:
        client.post(login_url, data=dict(
            email=email or app.config['TEST_USER_EMAIL'],
            password=password or app.config['TEST_USER_PASSWORD'],
        ))

def logout(app,client):
    with app.test_request_context():
        logout_url = url_for("security.logout")
    client.get(logout_url)

def create_record_with_pdf(rec_uuid, recid):
    indexer = WekoIndexer()
    indexer.get_es_index()
    record_data = {
        "_oai": {"id": f"oai:weko3.example.org:{recid}","sets": ["1732762571081"]},
        "path": ["1732762571081"],
        "owner": "1",
        "recid": str(recid),
        "title": ["test"],
        "pubdate": {"attribute_name": "PubDate","attribute_value": "2024-12-06"},
        "_buckets": {"deposit": "42bd95d5-8b69-4675-975c-8ebeb0894ed6"},
        "_deposit": {"id": str(recid),"owners": [1],"status": "draft","created_by": 1,"owners_ext": {"email": "wekosoftware@nii.ac.jp","username": None,"displayname": "sysadmin user"}},
        "item_title": "test",
        "author_link": [],
        "item_type_id": "15",
        "publish_date": "2024-12-06",
        "control_number": str(recid),
        "publish_status": "2",
        "weko_shared_id": -1,
        "item_1617186331708": {"attribute_name": "Title","attribute_value_mlt": [{"subitem_title": "test","subitem_title_language": "ja"}]},
        "item_1617258105262": {"attribute_name": "Resource Type","attribute_value_mlt": [{"resourceuri": "http://purl.org/coar/resource_type/c_5794","resourcetype": "conference paper"}]},
        "item_1617605131499": {
            "attribute_name": "File",
            "attribute_type": "file",
            "attribute_value_mlt": [
                {
                    "url": {
                        "url": f"https://192.168.56.134/record/{recid}/files/test_file_82K.pdf"
                    },
                    "date": [
                        {
                            "dateType": "Available",
                            "dateValue": "2024-12-06"
                        }
                    ],
                    "format": "application/pdf",
                    "filename": "test_file_82K.pdf",
                    "filesize": [
                        {
                            "value": "81 KB"
                        }
                    ],
                    "accessrole": "open_access",
                    "version_id": ""
                },
                {
                    "url": {
                        "url": f"https://192.168.56.134/record/{recid}/files/test_file_1.2M.pdf"
                    },
                    "date": [
                        {
                            "dateType": "Available",
                            "dateValue": "2024-12-06"
                        }
                    ],
                    "format": "application/pdf",
                    "filename": "test_file_1.2M.pdf",
                    "filesize": [
                        {
                            "value": "81 KB"
                        }
                    ],
                    "accessrole": "open_access",
                    "version_id": ""
                },
                {
                    "url": {
                        "url": f"https://weko3.example.org/record/{recid}/files/test.png"
                    },
                    "date": [
                    {
                        "dateType": "Available",
                        "dateValue": "2024-12-02"
                    }
                    ],
                    "format": "image/png",
                    "filename": "test.png",
                    "filesize": [
                    {
                        "value": "3 KB"
                    }
                    ],
                    "mimetype": "image/png",
                    "accessrole": "open_access",
                    "version_id": "9cd56273-ccb5-420e-94e0-7d29dbaff777",
                    "displaytype": "preview"
                },
                {
                    "version_id": "a5c67cff-f40c-41b6-9db6-0b7651143775",
                    "filename": "not_exist.pdf",
                    "filesize": [
                        {
                            "value": "81 KB"
                        }
                    ],
                    "format": "application/pdf",
                    "date": [
                        {
                            "dateValue": "2024-12-06",
                            "dateType": "Available"
                        }
                    ],
                    "accessrole": "open_access",
                    "url": {
                        "url": f"https://192.168.56.134/record/{recid}/files/not_exist.pdf"
                    },
                    "mimetype": "application/pdf"
                },
                {
                    "version_id": "63e3b70e-56a6-44e7-b7b4-cd187f20420c",
                    "filename": "sample_word.docx",
                    "filesize": [
                        {
                            "value": "14 KB"
                        }
                    ],
                    "format": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    "date": [
                        {
                            "dateValue": "2024-12-06",
                            "dateType": "Available"
                        }
                    ],
                    "accessrole": "open_access",
                    "url": {
                        "url": f"https://192.168.56.134/record/{recid}/files/sample_word.docx"
                    },
                    "mimetype": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                },
                {
                    "version_id": "0a9446bf-6ac1-4fa4-b7af-a8a291debb0e",
                    "filename": "sample.txt",
                    "filesize": [
                        {
                            "value": "1 KB"
                        }
                    ],
                    "format": "text/plain",
                    "date": [
                        {
                            "dateValue": "2024-12-06",
                            "dateType": "Available"
                        }
                    ],
                    "accessrole": "open_access",
                    "url": {
                        "url": f"https://192.168.56.134/record/{recid}/files/sample.txt"
                    },
                    "mimetype": "text/plain"
                },
            ]
        },
        "relation_version_is_last": True
    }
    es_data = {
        "file": {
            "URI": [
                {"value": f"https://192.168.56.134/record/{recid}/files/test_file_82K.pdf"},
                {"value": f"https://192.168.56.134/record/{recid}/files/test_file_1.2M.pdf"},
                {"value": f"https://192.168.56.134/record/{recid}/files/test.png"},
                {"value": f"https://192.168.56.134/record/{recid}/files/not_exist.pdf"},
                {"value": f"https://192.168.56.134/record/{recid}/files/sample_word.docx"},
                {"value": f"https://192.168.56.134/record/{recid}/files/sample.txt"},
            ],
            "mimeType": [
                "application/pdf",
                "application/pdf",
                "image/png",
                "application/pdf",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "text/plain"
            ],
            "date": [
                {"dateType": "fileDate.fileDateType"},
                {"dateType": "fileDate.fileDateType"},
                {"dateType": "fileDate.fileDateType"},
                {"dateType": "fileDate.fileDateType"},
                {"dateType": "fileDate.fileDateType"},
                {"dateType": "fileDate.fileDateType"}
            ],
            "extent": [
                "81 KB",
                "81 KB",
                "3 KB",
                "81 KB",
                "14 KB",
                "1 KB"
            ],
            "version": []
        },
        "title": ["test"],
        "type": ["conference paper"],
        "control_number": str(recid),
        "_oai": {"id": f"oai:weko3.example.org:{recid}","sets": ["1732762571081"]},
        "_item_metadata": {
            "pubdate": {"attribute_name": "PubDate","attribute_value": "2024-12-06"},
            "item_1617186331708": {"attribute_name": "Title","attribute_value_mlt": [{"subitem_title": "test","subitem_title_language": "ja"}]},
            "item_1617605131499": {
                "attribute_name": "File",
                "attribute_type": "file",
                "attribute_value_mlt": [
                    {
                        "version_id": "6a2502c3-7139-4cb8-901e-f97ffddf3097",
                        "filename": "test_file_82K.pdf",
                        "filesize": [
                            {
                                "value": "81 KB"
                            }
                        ],
                        "format": "application/pdf",
                        "date": [
                            {
                                "dateValue": "2024-12-06",
                                "dateType": "Available"
                            }
                        ],
                        "accessrole": "open_access",
                        "url": {
                            "url": f"https://192.168.56.134/record/{recid}/files/test_file_82K.pdf"
                        },
                        "mimetype": "application/pdf"
                    },
                    {
                        "version_id": "a5c67cff-f40c-41b6-9db6-0b7651143775",
                        "filename": "test_file_1.2M.pdf",
                        "filesize": [
                            {
                                "value": "81 KB"
                            }
                        ],
                        "format": "application/pdf",
                        "date": [
                            {
                                "dateValue": "2024-12-06",
                                "dateType": "Available"
                            }
                        ],
                        "accessrole": "open_access",
                        "url": {
                            "url": f"https://192.168.56.134/record/{recid}/files/test_file_1.2M.pdf"
                        },
                        "mimetype": "application/pdf"
                    },
                    {
                        "url": {
                        "url": f"https://weko3.example.org/record/{recid}/files/test.png"
                        },
                        "date": [
                        {
                            "dateType": "Available",
                            "dateValue": "2024-12-02"
                        }
                        ],
                        "format": "image/png",
                        "filename": "test.png",
                        "filesize": [
                        {
                            "value": "3 KB"
                        }
                        ],
                        "mimetype": "image/png",
                        "accessrole": "open_access",
                        "version_id": "9cd56273-ccb5-420e-94e0-7d29dbaff777",
                        "displaytype": "preview"
                    },
                    {
                        "version_id": "a5c67cff-f40c-41b6-9db6-0b7651143775",
                        "filename": "not_exist.pdf",
                        "filesize": [
                            {
                                "value": "81 KB"
                            }
                        ],
                        "format": "application/pdf",
                        "date": [
                            {
                                "dateValue": "2024-12-06",
                                "dateType": "Available"
                            }
                        ],
                        "accessrole": "open_access",
                        "url": {
                            "url": f"https://192.168.56.134/record/{recid}/files/not_exist.pdf"
                        },
                        "mimetype": "application/pdf"
                    },
                    {
                        "version_id": "63e3b70e-56a6-44e7-b7b4-cd187f20420c",
                        "filename": "sample_word.docx",
                        "filesize": [
                            {
                                "value": "14 KB"
                            }
                        ],
                        "format": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        "date": [
                            {
                                "dateValue": "2024-12-06",
                                "dateType": "Available"
                            }
                        ],
                        "accessrole": "open_access",
                        "url": {
                            "url": f"https://192.168.56.134/record/{recid}/files/sample_word.docx"
                        },
                        "mimetype": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    },
                    {
                        "version_id": "0a9446bf-6ac1-4fa4-b7af-a8a291debb0e",
                        "filename": "sample.txt",
                        "filesize": [
                            {
                                "value": "1 KB"
                            }
                        ],
                        "format": "text/plain",
                        "date": [
                            {
                                "dateValue": "2024-12-06",
                                "dateType": "Available"
                            }
                        ],
                        "accessrole": "open_access",
                        "url": {
                            "url": f"https://192.168.56.134/record/{recid}/files/sample.txt"
                        },
                        "mimetype": "text/plain"
                    },
                ]
            },
            "item_1617258105262": {"attribute_name": "Resource Type","attribute_value_mlt": [{"resourcetype": "conference paper","resourceuri": "http://purl.org/coar/resource_type/c_5794"}]},
            "item_title": "test",
            "item_type_id": "15",
            "control_number": str(recid),
            "author_link": [],
            "_oai": {"id": f"oai:weko3.example.org:{recid}","sets": ["1732762571081"]},
            "weko_shared_id": -1,
            "owner": "1",
            "publish_date": "2024-12-06",
            "title": ["test"],
            "relation_version_is_last": True,
            "path": ["1732762571081"],
            "publish_status": "2"
        },
        "itemtype": "デフォルトアイテムタイプ（フル）",
        "publish_date": "2024-12-06",
        "author_link": [],
        "weko_creator_id": "1",
        "weko_shared_id": -1,
        "path": [
            "1732762571081"
        ],
        "publish_status": "2",
        "_created": "2024-12-06T02:27:18.553183+00:00",
        "_updated": "2024-12-06T02:27:39.552181+00:00",
        "content": [
            {
                "version_id": "a5c67cff-f40c-41b6-9db6-0b7651143775",
                "filename": "test_file_1.2M.pdf",
                "filesize": [
                    {
                        "value": "81 KB"
                    }
                ],
                "format": "application/pdf",
                "date": [
                    {
                        "dateValue": "2024-12-06",
                        "dateType": "Available"
                    }
                ],
                "accessrole": "open_access",
                "url": {
                    "url": f"https://192.168.56.134/record/{recid}/files/test_file_1.2M.pdf"
                },
                "mimetype": "application/pdf",
                "attachment": {
                    "content": ""
                }
            },
            {
                "version_id": "6a2502c3-7139-4cb8-901e-f97ffddf3097",
                "filename": "test_file_82K.pdf",
                "filesize": [
                    {
                        "value": "81 KB"
                    }
                ],
                "format": "application/pdf",
                "date": [
                    {
                        "dateValue": "2024-12-06",
                        "dateType": "Available"
                    }
                ],
                "accessrole": "open_access",
                "url": {
                    "url": f"https://192.168.56.134/record/{recid}/files/test_file_82K.pdf"
                },
                "mimetype": "application/pdf",
                "attachment": {
                    "content": ""
                }
            },
            {
                "url": {
                    "url": f"http://localhost/record/{recid}/files/test.png"
                },
                "date": [
                {
                    "dateType": "Available",
                    "dateValue": "2024-12-02"
                }
                ],
                "format": "image/png",
                "filename": "test.png",
                "filesize": [
                {
                    "value": "3 KB"
                }
                ],
                "mimetype": "image/png",
                "accessrole": "open_access",
                "version_id": "9cd56273-ccb5-420e-94e0-7d29dbaff777",
                "displaytype": "preview",
                "attachment": {}
            },
            {
                "version_id": "6a2502c3-7139-4cb8-901e-f97ffddf3097",
                "filename": "not_exist.pdf",
                "filesize": [
                    {
                        "value": "81 KB"
                    }
                ],
                "format": "application/pdf",
                "date": [
                    {
                        "dateValue": "2024-12-06",
                        "dateType": "Available"
                    }
                ],
                "accessrole": "open_access",
                "url": {
                    "url": f"https://192.168.56.134/record/{recid}/files/not_exist.pdf"
                },
                "mimetype": "application/pdf",
                "attachment": {
                    "content": ""
                }
            },
            {
                "version_id": "63e3b70e-56a6-44e7-b7b4-cd187f20420c",
                "filename": "sample_word.docx",
                "filesize": [
                    {
                        "value": "14 KB"
                    }
                ],
                "format": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "date": [
                    {
                        "dateValue": "2024-12-06",
                        "dateType": "Available"
                    }
                ],
                "accessrole": "open_access",
                "url": {
                    "url": f"https://192.168.56.134/record/{recid}/files/sample_word.docx"
                },
                "mimetype": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "attachment": {
                    "content": ""
                }
            },
            {
                "version_id": "0a9446bf-6ac1-4fa4-b7af-a8a291debb0e",
                "filename": "sample.txt",
                "filesize": [
                    {
                        "value": "1 KB"
                    }
                ],
                "format": "text/plain",
                "date": [
                    {
                        "dateValue": "2024-12-06",
                        "dateType": "Available"
                    }
                ],
                "accessrole": "open_access",
                "url": {
                    "url": f"https://192.168.56.134/record/{recid}/files/sample.txt"
                },
                "mimetype": "text/plain",
                "attachment": {
                    "content": ""
                }
            },
        ]
    }
    
    item_metadata = {
        "id": str(recid),
        "pid":{"type":"depid","value":str(recid),"revision_id":0},
        "lang": "ja", "owner": "1",
        "title":"test",
        "owners":[1],"status":"published","$schema":"/items/jsonschema/1",
        "pubdate":"2024-12-06","created_by":1,"shared_user_id":-1,
        "item_1617186331708":[{"subitem_title": "test","subitem_title_language": "ja"}],
        "item_1617258105262":[{"resourceuri": "http://purl.org/coar/resource_type/c_5794","resourcetype": "conference paper"}],
        "item_1617605131499":[
            {
                "url": {
                    "url": f"https://192.168.56.134/record/{recid}/files/test_file_82K.pdf"
                },
                "date": [
                    {
                        "dateType": "Available",
                        "dateValue": "2024-12-06"
                    }
                ],
                "format": "application/pdf",
                "filename": "test_file_82K.pdf",
                "filesize": [
                    {
                        "value": "81 KB"
                    }
                ],
                "accessrole": "open_access",
                "version_id": ""
            },
            {
                "url": {
                    "url": f"https://192.168.56.134/record/{recid}/files/test_file_1.2M.pdf"
                },
                "date": [
                    {
                        "dateType": "Available",
                        "dateValue": "2024-12-06"
                    }
                ],
                "format": "application/pdf",
                "filename": "test_file_1.2M.pdf",
                "filesize": [
                    {
                        "value": "81 KB"
                    }
                ],
                "accessrole": "open_access",
                "version_id": ""
            },
            {
                "url": {
                    "url": f"https://weko3.example.org/record/{recid}/files/test.png"
                },
                "date": [
                {
                    "dateType": "Available",
                    "dateValue": "2024-12-02"
                }
                ],
                "format": "image/png",
                "filename": "test.png",
                "filesize": [
                {
                    "value": "3 KB"
                }
                ],
                "mimetype": "image/png",
                "accessrole": "open_access",
                "version_id": "9cd56273-ccb5-420e-94e0-7d29dbaff777",
                "displaytype": "preview"
            },
            {
                "version_id": "a5c67cff-f40c-41b6-9db6-0b7651143775",
                "filename": "not_exist.pdf",
                "filesize": [
                    {
                        "value": "81 KB"
                    }
                ],
                "format": "application/pdf",
                "date": [
                    {
                        "dateValue": "2024-12-06",
                        "dateType": "Available"
                    }
                ],
                "accessrole": "open_access",
                "url": {
                    "url": f"https://192.168.56.134/record/{recid}/files/not_exist.pdf"
                },
                "mimetype": "application/pdf"
            },
            {
                "version_id": "63e3b70e-56a6-44e7-b7b4-cd187f20420c",
                "filename": "sample_word.docx",
                "filesize": [
                    {
                        "value": "14 KB"
                    }
                ],
                "format": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "date": [
                    {
                        "dateValue": "2024-12-06",
                        "dateType": "Available"
                    }
                ],
                "accessrole": "open_access",
                "url": {
                    "url": f"https://192.168.56.134/record/{recid}/files/sample_word.docx"
                },
                "mimetype": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            },
            {
                "version_id": "0a9446bf-6ac1-4fa4-b7af-a8a291debb0e",
                "filename": "sample.txt",
                "filesize": [
                    {
                        "value": "1 KB"
                    }
                ],
                "format": "text/plain",
                "date": [
                    {
                        "dateValue": "2024-12-06",
                        "dateType": "Available"
                    }
                ],
                "accessrole": "open_access",
                "url": {
                    "url": f"https://192.168.56.134/record/{recid}/files/sample.txt"
                },
                "mimetype": "text/plain",
            },
        ]
    }
    record = WekoRecord.create(record_data, id_=rec_uuid)
    item = ItemsMetadata.create(item_metadata,id_=rec_uuid)
    bucket = Bucket.create()
    RecordsBuckets.create(record=record.model, bucket=bucket)
    
    # mini size file
    mini_filepath = "tests/data/test_files/test_file_82K.pdf"
    with open(mini_filepath, "rb") as f:
        obj=ObjectVersion.create(bucket=bucket.id, key='test_file_82K.pdf',stream=f)
    es_data["_item_metadata"]["item_1617605131499"]["attribute_value_mlt"][0]["version_id"] = obj.version_id
    es_data["content"][0]["version_id"] = obj.version_id
    
    # big size file
    big_filepath = "tests/data/test_files/test_file_1.2M.pdf"
    with open(big_filepath, "rb") as f:
        obj=ObjectVersion.create(bucket=bucket.id, key='test_file_1.2M.pdf',stream=f)
    es_data["_item_metadata"]["item_1617605131499"]["attribute_value_mlt"][1]["version_id"] = obj.version_id
    es_data["content"][1]["version_id"] = obj.version_id
    
    # word file
    word_filepath = "tests/data/test_files/sample_word.docx"
    with open(word_filepath, "rb") as f:
        obj=ObjectVersion.create(bucket=bucket.id, key='sample_word.docx',stream=f)
    es_data["_item_metadata"]["item_1617605131499"]["attribute_value_mlt"][4]["version_id"] = obj.version_id
    es_data["content"][4]["version_id"] = obj.version_id
    
    # png file
    png_filepath = "tests/data/test_files/test.png"
    with open(png_filepath, "rb") as f:
        obj=ObjectVersion.create(bucket=bucket.id, key='test.png',stream=f)
    es_data["_item_metadata"]["item_1617605131499"]["attribute_value_mlt"][2]["version_id"] = obj.version_id
    es_data["content"][2]["version_id"] = obj.version_id
    
    # txt file
    txt_filepath = "tests/data/test_files/sample.txt"
    with open(txt_filepath, "rb") as f:
        obj=ObjectVersion.create(bucket=bucket.id, key='sample.txt',stream=f)
    es_data["_item_metadata"]["item_1617605131499"]["attribute_value_mlt"][5]["version_id"] = obj.version_id
    es_data["content"][5]["version_id"] = obj.version_id
    
    # Phantom files
    from six import BytesIO
    f=BytesIO(b"this is not exist pdf.")
    obj = ObjectVersion.create(bucket=bucket.id, key="not_exist.pdf",stream=f)
    es_data["_item_metadata"]["item_1617605131499"]["attribute_value_mlt"][3]["version_id"] = obj.version_id
    es_data["content"][3]["version_id"] = obj.version_id
    obj.file.uri = "/not_exist_dir"+str(recid)
    db.session.merge(obj.file)
    db.session.commit()
    
    # only db file
    f=BytesIO(b"only db png.")
    obj = ObjectVersion.create(bucket=bucket.id, key="only_db.png",stream=f)
    obj.file.uri = "/only_db_"+str(recid)
    db.session.merge(obj.file)
    db.session.commit()
    indexer.upload_metadata(es_data,rec_uuid,1)
    
    pdf_files = {}
    # pdfファイル複数渡す
    deposit = WekoDeposit.get_record(rec_uuid)
    target_format = ["application/pdf","application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
    for file in deposit.files:
        if file.obj.mimetype in target_format:
            pdf_files[file.obj.key] = {"file":file,"is_pdf": file.obj.mimetype=="application/pdf"}
    return pdf_files, deposit