import sys
import uuid
import pytest
import json
from mock import patch

from weko_workflow.models import Activity
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from elasticsearch import ConnectionError
from demo.fix_metadata_53602 import (
    parse_args,
    get_item_type_info,
    change_metadata,
    main,
    change_resource_type_metadata,
    change_identifier_registration_metadata,
    change_radiobutton_metadata,
    change_listbox_metadata,
    change_dcndl_original_language_metadata,
    change_jpcoar_format_metadata,
    change_jpcoar_holding_agent_metadata,
    change_jpcoar_catalog_metadata
)


def run_parse_args(monkeypatch, argv):
    monkeypatch.setattr(sys, "argv", ["fix_metadata_53602.py"] + argv)
    return parse_args()


# .tox/c1/bin/pytest --cov=scripts tests/test_fix_metadata_53602.py::test_parse_args -vv -s --cov-branch --cov-report=term --cov-report=xml --basetemp=/code/scripts/.tox/c1/tmp
def test_parse_args(monkeypatch, capsys):
    # case 1
    startDate, endDate, recordId, itemTypeId = run_parse_args(monkeypatch, [])
    assert startDate == ""
    assert endDate == ""
    assert recordId == ""
    assert itemTypeId == ""

    # case 2
    id = str(uuid.uuid4())
    startDate, endDate, recordId, itemTypeId = run_parse_args(monkeypatch, ["--start-date", "2025-01-01", "--end-date", "2025-01-01", "--id", id, "--item-type-id", "1"])
    assert startDate == "2025-01-01T00:00:00"
    assert endDate == "2025-01-02T00:00:00"
    assert recordId == id
    assert itemTypeId == "1"

    # case 3
    startDate, endDate, recordId, itemTypeId = run_parse_args(monkeypatch, ["--start-date", "2025-01-01T12:00:00"])
    assert startDate == "2025-01-01T12:00:00"
    assert endDate == ""
    assert recordId == ""
    assert itemTypeId == ""

    # case 4
    startDate, endDate, recordId, itemTypeId = run_parse_args(monkeypatch, ["--start-date", "2025-01-01"])
    assert startDate == "2025-01-01T00:00:00"
    assert endDate == ""
    assert recordId == ""
    assert itemTypeId == ""

    # case 5
    startDate, endDate, recordId, itemTypeId = run_parse_args(monkeypatch, ["--start-date", "2025-01"])
    assert startDate == "2025-01-01T00:00:00"
    assert endDate == ""
    assert recordId == ""
    assert itemTypeId == ""

    # case 6
    startDate, endDate, recordId, itemTypeId = run_parse_args(monkeypatch, ["--start-date", "2025"])
    assert startDate == "2025-01-01T00:00:00"
    assert endDate == ""
    assert recordId == ""
    assert itemTypeId == ""

    # case 7
    startDate, endDate, recordId, itemTypeId = run_parse_args(monkeypatch, ["--end-date", "2025-01-01T12:00:00"])
    assert startDate == ""
    assert endDate == "2025-01-01T12:00:01"
    assert recordId == ""
    assert itemTypeId == ""

    # case 8
    startDate, endDate, recordId, itemTypeId = run_parse_args(monkeypatch, ["--end-date", "2025-01-01"])
    assert startDate == ""
    assert endDate == "2025-01-02T00:00:00"
    assert recordId == ""
    assert itemTypeId == ""

    # case 8
    startDate, endDate, recordId, itemTypeId = run_parse_args(monkeypatch, ["--end-date", "2025-01-01"])
    assert startDate == ""
    assert endDate == "2025-01-02T00:00:00"
    assert recordId == ""
    assert itemTypeId == ""

    # case 9
    startDate, endDate, recordId, itemTypeId = run_parse_args(monkeypatch, ["--end-date", "2025-01"])
    assert startDate == ""
    assert endDate == "2025-02-01T00:00:00"
    assert recordId == ""
    assert itemTypeId == ""

    # case 10
    startDate, endDate, recordId, itemTypeId = run_parse_args(monkeypatch, ["--end-date", "2025"])
    assert startDate == ""
    assert endDate == "2026-01-01T00:00:00"
    assert recordId == ""
    assert itemTypeId == ""

    # case 64
    with pytest.raises(SystemExit):
        run_parse_args(monkeypatch, ["--start-date", "2025-02-30"])
    result = capsys.readouterr()
    assert result.err == "Error: --start-date option is out of range.\n"

    # case 65
    with pytest.raises(SystemExit):
        run_parse_args(monkeypatch, ["--start-date", "225"])
    result = capsys.readouterr()
    assert result.err == "Error: The format of the --start-date option is incorrect. Supported formats are yyyy-MM-ddTHH:mm:ss, yyyy-MM-dd, yyyy-MM and yyyy.\n"

    # case 66
    with pytest.raises(SystemExit):
        run_parse_args(monkeypatch, ["--start-date", "aaa"])
    result = capsys.readouterr()
    assert result.err == "Error: The format of the --start-date option is incorrect. Supported formats are yyyy-MM-ddTHH:mm:ss, yyyy-MM-dd, yyyy-MM and yyyy.\n"

    # case 67
    with pytest.raises(SystemExit):
        run_parse_args(monkeypatch, ["--end-date"])
    result = capsys.readouterr()
    assert "error: argument --end-date: expected one argument" in result.err

    # case 68
    with pytest.raises(SystemExit):
        run_parse_args(monkeypatch, ["--end-date", "2025-02-30"])
    result = capsys.readouterr()
    assert result.err == "Error: --end-date option is out of range.\n"

    # case 69
    with pytest.raises(SystemExit):
        run_parse_args(monkeypatch, ["--end-date", "aaa"])
    result = capsys.readouterr()
    assert result.err == "Error: The format of the --end-date option is incorrect. Supported formats are yyyy-MM-ddTHH:mm:ss, yyyy-MM-dd, yyyy-MM and yyyy.\n"

    # case 70
    with pytest.raises(SystemExit):
        run_parse_args(monkeypatch, ["--start-date", "2025", "--end-date", "2024"])
    result = capsys.readouterr()
    assert result.err == "Error: The --start-date must be earlier than the --end-date.\n"

    # case 71
    with pytest.raises(SystemExit):
        run_parse_args(monkeypatch, ["--id", "abc"])
    result = capsys.readouterr()
    assert result.err == "Error: The format of the --id option is invalid. Please use a UUID.\n"

    # case 72
    with pytest.raises(SystemExit):
        run_parse_args(monkeypatch, ["--item-type-id", "abc"])
    result = capsys.readouterr()
    assert result.err == "Error: The format of the --item-type-id option is invalid. Please use integer.\n"

    # case 81
    with pytest.raises(SystemExit):
        startDate, endDate, recordId, itemTypeId = run_parse_args(monkeypatch, ["--end-date", str])


class DummyItemType:
    def __init__(self, render=None):
        self.render = render or {}


def mock_item_type(render):
    return DummyItemType(render)


# .tox/c1/bin/pytest --cov=scripts tests/test_fix_metadata_53602.py::test_get_item_type_info -vv -s --cov-branch --cov-report=term --cov-report=xml --basetemp=/code/scripts/.tox/c1/tmp
def test_get_item_type_info(capsys, app):
    check_prop_ids = {
        "cus_001": "type1",
        "cus_1046": "radio",
        "cus_1047": "listbox"
    }

    # case 11
    dummy = mock_item_type({
        "meta_list": {
            "item_0001": {"input_type": "cus_001"}
        },
        "table_row_map": {"schema": {"properties": {}}}
    })
    check_item_keys = {}
    with patch("weko_records.api.ItemTypes.get_by_id", return_value=dummy):
        get_item_type_info(check_item_keys, "1", check_prop_ids)
        assert check_item_keys["1"] == {"item_0001": "type1"}

    # case 12
    dummy = mock_item_type({
        "meta_list": {
            "item_0001": {"input_type": "cus_005"}
        },
        "table_row_map": {"schema": {"properties": {}}}
    })
    check_item_keys = {}
    with patch("weko_records.api.ItemTypes.get_by_id", return_value=dummy):
        get_item_type_info(check_item_keys, "1", check_prop_ids)
        assert check_item_keys["1"] == {}

    # case 13
    check_item_keys = {}
    with patch("weko_records.api.ItemTypes.get_by_id", return_value=None):
        get_item_type_info(check_item_keys, "2", check_prop_ids)
        assert check_item_keys["2"] == {}

    # case 14
    dummy = mock_item_type({
        "meta_list": {
            "item_0001": {
                "input_type": "cus_1046",
                "option": {"multiple": False}
            }
        },
        "table_row_map": {
            "schema": {
                "properties": {
                    "item_0001": {
                        "properties": {
                            "subitem_radio_item": {
                                "format": "radios"
                            }
                        }
                    }
                }
            }
        }
    })
    check_item_keys = {}
    with patch("weko_records.api.ItemTypes.get_by_id", return_value=dummy):
        get_item_type_info(check_item_keys, "1", check_prop_ids)
        assert check_item_keys["1"] == {"item_0001": "radio"}

    # case 15
    dummy = mock_item_type({
        "meta_list": {
            "item_0001": {
                "input_type": "cus_1046",
                "option": {"multiple": True}
            }
        },
        "table_row_map": {
            "schema": {
                "properties": {
                    "item_0001": {
                        "items": {
                            "properties": {
                                "subitem_radio_item": {
                                    "format": "radios"
                                }
                            }
                        }
                    }
                }
            }
        }
    })
    check_item_keys = {}
    with patch("weko_records.api.ItemTypes.get_by_id", return_value=dummy):
        get_item_type_info(check_item_keys, "1", check_prop_ids)
        assert check_item_keys["1"] == {"item_0001": "radio"}
    
    # case 16
    dummy = mock_item_type({
        "meta_list": {
            "item_0001": {
                "input_type": "cus_1046",
                "option": {"multiple": False}
            }
        },
        "table_row_map": {
            "schema": {
                "properties": {
                    "item_0001": {
                        "properties": {
                            "subitem_textarea_value": {}
                        }
                    }
                }
            }
        }
    })
    check_item_keys = {}
    with patch("weko_records.api.ItemTypes.get_by_id", return_value=dummy):
        get_item_type_info(check_item_keys, "1", check_prop_ids)
        assert check_item_keys["1"] == {"item_0001": "radio"}

    # case 17
    dummy = mock_item_type({
        "meta_list": {
            "item_0001": {
                "input_type": "cus_1046",
                "option": {"multiple": True}
            }
        },
        "table_row_map": {
            "schema": {
                "properties": {
                    "item_0001": {
                        "items": {
                            "properties": {
                                "subitem_textarea_value": {}
                            }
                        }
                    }
                }
            }
        }
    })
    check_item_keys = {}
    with patch("weko_records.api.ItemTypes.get_by_id", return_value=dummy):
        get_item_type_info(check_item_keys, "1", check_prop_ids)
        assert check_item_keys["1"] == {"item_0001": "radio"}

    # case 82
    dummy = mock_item_type({
        "meta_list": {
            "item_0001": {
                "input_type": "cus_1046",
                "option": {"multiple": False}
            }
        },
        "table_row_map": {
            "schema": {
                "properties": {
                    "item_0001": {
                        "properties": {
                            "subitem_radio_item": {
                                "format": "checkboxes"
                            }
                        }
                    }
                }
            }
        }
    })
    check_item_keys = {}
    with patch("weko_records.api.ItemTypes.get_by_id", return_value=dummy):
        get_item_type_info(check_item_keys, "1", check_prop_ids)
        assert check_item_keys["1"] == {}

    # case 83
    dummy = mock_item_type({
        "meta_list": {
            "item_0001": {
                "input_type": "cus_1046",
                "option": {"multiple": True}
            }
        },
        "table_row_map": {
            "schema": {
                "properties": {
                    "item_0001": {
                        "items": {
                            "properties": {
                                "subitem_radio_item": {
                                    "format": "checkboxes"
                                }
                            }
                        }
                    }
                }
            }
        }
    })
    check_item_keys = {}
    with patch("weko_records.api.ItemTypes.get_by_id", return_value=dummy):
        get_item_type_info(check_item_keys, "1", check_prop_ids)
        assert check_item_keys["1"] == {}

    # case 18
    dummy = mock_item_type({
        "meta_list": {
            "item_0001": {
                "input_type": "cus_1047",
                "option": {"multiple": False}
            }
        },
        "table_row_map": {
            "schema": {
                "properties": {
                    "item_0001": {
                        "properties": {
                            "subitem_select_item": {
                                "format": "select"
                            }
                        }
                    }
                }
            }
        }
    })
    check_item_keys = {}
    with patch("weko_records.api.ItemTypes.get_by_id", return_value=dummy):
        get_item_type_info(check_item_keys, "1", check_prop_ids)
        assert check_item_keys["1"] == {"item_0001": "listbox"}

    # case 19
    dummy = mock_item_type({
        "meta_list": {
            "item_0001": {
                "input_type": "cus_1047",
                "option": {"multiple": True}
            }
        },
        "table_row_map": {
            "schema": {
                "properties": {
                    "item_0001": {
                        "items": {
                            "properties": {
                                "subitem_select_item": {
                                    "format": "select"
                                }
                            }
                        }
                    }
                }
            }
        }
    })
    check_item_keys = {}
    with patch("weko_records.api.ItemTypes.get_by_id", return_value=dummy):
        get_item_type_info(check_item_keys, "1", check_prop_ids)
        assert check_item_keys["1"] == {"item_0001": "listbox"}
    
    # case 20
    dummy = mock_item_type({
        "meta_list": {
            "item_0001": {
                "input_type": "cus_1047",
                "option": {"multiple": False}
            }
        },
        "table_row_map": {
            "schema": {
                "properties": {
                    "item_0001": {
                        "properties": {
                            "subitem_textarea_value": {}
                        }
                    }
                }
            }
        }
    })
    check_item_keys = {}
    with patch("weko_records.api.ItemTypes.get_by_id", return_value=dummy):
        get_item_type_info(check_item_keys, "1", check_prop_ids)
        assert check_item_keys["1"] == {"item_0001": "listbox"}

    # case 21
    dummy = mock_item_type({
        "meta_list": {
            "item_0001": {
                "input_type": "cus_1047",
                "option": {"multiple": True}
            }
        },
        "table_row_map": {
            "schema": {
                "properties": {
                    "item_0001": {
                        "items": {
                            "properties": {
                                "subitem_textarea_value": {}
                            }
                        }
                    }
                }
            }
        }
    })
    check_item_keys = {}
    with patch("weko_records.api.ItemTypes.get_by_id", return_value=dummy):
        get_item_type_info(check_item_keys, "1", check_prop_ids)
        assert check_item_keys["1"] == {"item_0001": "listbox"}

    # case 84
    dummy = mock_item_type({
        "meta_list": {
            "item_0001": {
                "input_type": "cus_1047",
                "option": {"multiple": False}
            }
        },
        "table_row_map": {
            "schema": {
                "properties": {
                    "item_0001": {
                        "properties": {
                            "subitem_select_item": {
                                "format": "checkboxes"
                            }
                        }
                    }
                }
            }
        }
    })
    check_item_keys = {}
    with patch("weko_records.api.ItemTypes.get_by_id", return_value=dummy):
        get_item_type_info(check_item_keys, "1", check_prop_ids)
        assert check_item_keys["1"] == {}

    # case 85
    dummy = mock_item_type({
        "meta_list": {
            "item_0001": {
                "input_type": "cus_1047",
                "option": {"multiple": True}
            }
        },
        "table_row_map": {
            "schema": {
                "properties": {
                    "item_0001": {
                        "items": {
                            "properties": {
                                "subitem_select_item": {
                                    "format": "checkboxes"
                                }
                            }
                        }
                    }
                }
            }
        }
    })
    check_item_keys = {}
    with patch("weko_records.api.ItemTypes.get_by_id", return_value=dummy):
        get_item_type_info(check_item_keys, "1", check_prop_ids)
        assert check_item_keys["1"] == {}

    # case 73
    with pytest.raises(SQLAlchemyError):
        with patch("weko_records.api.ItemTypes.get_by_id", side_effect=SQLAlchemyError("Test error")):
            get_item_type_info(check_item_keys, "1", check_prop_ids)


# .tox/c1/bin/pytest --cov=scripts tests/test_fix_metadata_53602.py::test_change_metadata -vv -s --cov-branch --cov-report=term --cov-report=xml --basetemp=/code/scripts/.tox/c1/tmp
def test_change_metadata():
    item = {}
    rec = {}

    # case 22
    with patch("demo.fix_metadata_53602.change_resource_type_metadata", return_value=True):
        assert change_metadata("resource_type", "item_resource_type", item, rec) == True
    
    # case 23
    with patch("demo.fix_metadata_53602.change_identifier_registration_metadata", return_value=True):
        assert change_metadata("identifier_registration", "item_identifier_registration", item, rec) == True

    # case 24
    with patch("demo.fix_metadata_53602.change_radiobutton_metadata", return_value=True):
        assert change_metadata("radiobutton", "item_radiobutton", item, rec) == True
    
    # case 25
    with patch("demo.fix_metadata_53602.change_listbox_metadata", return_value=True):
        assert change_metadata("listbox", "item_listbox", item, rec) == True

    # case 26
    with patch("demo.fix_metadata_53602.change_dcndl_original_language_metadata", return_value=True):
        assert change_metadata("dcndl_original_language", "item_dcndl_original_language", item, rec) == True

    # case 27
    with patch("demo.fix_metadata_53602.change_jpcoar_format_metadata", return_value=True):
        assert change_metadata("jpcoar_format", "item_jpcoar_format", item, rec) == True

    # case 28
    with patch("demo.fix_metadata_53602.change_jpcoar_holding_agent_metadata", return_value=True):
        assert change_metadata("jpcoar_holding_agent", "item_jpcoar_holding_agent", item, rec) == True

    # case 29
    with patch("demo.fix_metadata_53602.change_jpcoar_catalog_metadata", return_value=True):
        assert change_metadata("jpcoar_catalog", "item_jpcoar_catalog", item, rec) == True

    # case 30
    assert change_metadata("temp", "item_temp", item, rec) == False


# .tox/c1/bin/pytest --cov=scripts tests/test_fix_metadata_53602.py::test_main_nodata -vv -s --cov-branch --cov-report=term --cov-report=xml --basetemp=/code/scripts/.tox/c1/tmp
def test_main_nodata(monkeypatch, app, db):
    # case 31, 32
    monkeypatch.setattr(sys, "argv", ["fix_metadata_53602.py", "--item-type-id", "1"])
    main()


class DummyDBData:
    def __init__(self, activity_id=None, temp_data=None, item_type_id=None):
        self.id = ""
        self.item_type_id = ""
        self.itemtype_id = item_type_id or ""
        self.activity_id = activity_id or ""
        self.temp_data = temp_data or "{}"


# .tox/c1/bin/pytest --cov=scripts tests/test_fix_metadata_53602.py::test_main -vv -s --cov-branch --cov-report=term --cov-report=xml --basetemp=/code/scripts/.tox/c1/tmp
def test_main(monkeypatch, capsys, app, db, item_data):
    # case 33
    monkeypatch.setattr(sys, "argv", ["fix_metadata_53602.py", "--start-date", "2025"])
    main()

    dummy = mock_item_type({
        "meta_list": {
            "item_0001": {"input_type": "cus_1014"},
            "item_0002": {"input_type": "cus_1018"}
        },
        "table_row_map": {"schema": {"properties": {}}}
    })
    with patch("weko_records.api.ItemTypes.get_by_id", return_value=dummy):
        monkeypatch.setattr(sys, "argv", ["fix_metadata_53602.py", "--id", str(item_data[1])])
        with patch("weko_deposit.api.WekoIndexer.get_es_index", return_value=True), \
             patch("weko_deposit.api.WekoIndexer.upload_metadata", side_effect=ConnectionError("", "", "")):
            # case 76
            main()
        result = capsys.readouterr()
        assert "Error updating Item UUID=" in result.err

        monkeypatch.setattr(sys, "argv", ["fix_metadata_53602.py", "--end-date", "2025"])
        with patch("weko_deposit.api.WekoIndexer.get_es_index", return_value=True), \
             patch("weko_deposit.api.WekoIndexer.upload_metadata", return_value=True):
            # case 34, 35
            main()

        actviities = [
            DummyDBData("A1", json.dumps(None), 1),
            DummyDBData("A2", json.dumps({"item_0001": {"resourcetype": "periodical"}}), 1),
            DummyDBData("A3", json.dumps({"item_0001": {"resourcetype": "periodical", "resourceuri": ""}}), 2)
        ]
        with patch("flask_sqlalchemy.BaseQuery.all", return_value=actviities), \
             patch("flask_sqlalchemy.BaseQuery.one_or_none", return_value=Activity()), \
             patch("sqlalchemy.orm.attributes.flag_modified", return_value=True), \
             patch("invenio_db.db.session.commit", return_value=True):
            # case 36, 37, 77
            main()
        result = capsys.readouterr()
        assert "Unexpected error UUID=" in result.err

        with pytest.raises(Exception):
            with patch("flask_sqlalchemy.BaseQuery.all", side_effect=SQLAlchemyError("test error")):
                # case 75
                main()
            result = capsys.readouterr()
            assert "Fatal error:" in result.err

        with patch("flask_sqlalchemy.BaseQuery.all", return_value=actviities), \
             patch("flask_sqlalchemy.BaseQuery.one_or_none", return_value=Activity()), \
             patch("sqlalchemy.orm.attributes.flag_modified", return_value=True), \
             patch("invenio_db.db.session.commit", side_effect=OperationalError("test error", "", "")):
            # case 74
            main()

        actviities = [
            DummyDBData("A3", json.dumps({"item_0001": {"resourcetype": "periodical", "resourceuri": ""}}), 2)
        ]
        with patch("flask_sqlalchemy.BaseQuery.all", return_value=actviities), \
             patch("json.loads", side_effect=json.JSONDecodeError("", "", 0)):
            # case 79
            main()

        with patch("flask_sqlalchemy.BaseQuery.all", return_value=actviities), \
             patch("flask_sqlalchemy.BaseQuery.one_or_none", return_value=Activity()), \
             patch("json.loads", side_effect=SyntaxError()):
            # case 80
            main()


# .tox/c1/bin/pytest --cov=scripts tests/test_fix_metadata_53602.py::test_change_resource_type_metadata -vv -s --cov-branch --cov-report=term --cov-report=xml --basetemp=/code/scripts/.tox/c1/tmp
def test_change_resource_type_metadata():
    item_key = "item_resource_type"

    # case 38
    item_data = {
        "id": "1",
        "item_resource_type": {
            "resourceuri": "http://purl.org/coar/resource_type/c_2659",
            "resourcetype": "periodical"
        }
    }
    rec_data = {
        "recid": "1",
        "item_title": "Sample",
        "item_type_id": "1",
        "item_resource_type": {
            "attribute_name": "resource_type",
            "attribute_value_mlt":[
                {
                    "resourceuri": "http://purl.org/coar/resource_type/c_2659",
                    "resourcetype": "periodical"
                }
            ]
        }
    }
    assert change_resource_type_metadata(item_key, item_data, rec_data) == True
    assert item_data == {
        "id": "1",
        "item_resource_type": {
            "resourceuri": "http://purl.org/coar/resource_type/c_0640",
            "resourcetype": "journal"
        }
    }
    assert rec_data == {
        "recid": "1",
        "item_title": "Sample",
        "item_type_id": "1",
        "item_resource_type": {
            "attribute_name": "resource_type",
            "attribute_value_mlt":[
                {
                    "resourceuri": "http://purl.org/coar/resource_type/c_0640",
                    "resourcetype": "journal"
                }
            ]
        }
    }

    # case 39
    item_data = {
        "id": "1",
        "item_resource_type": {
            "resourceuri": "http://purl.org/coar/resource_type/c_c94f",
            "resourcetype": "conference object"
        }
    }
    rec_data = {
        "recid": "1",
        "item_title": "Sample",
        "item_type_id": "1",
        "item_resource_type": {
            "attribute_name": "resource_type",
            "attribute_value_mlt":[
                {
                    "resourceuri": "http://purl.org/coar/resource_type/c_c94f",
                    "resourcetype": "conference object"
                }
            ]
        }
    }
    assert change_resource_type_metadata(item_key, item_data, rec_data) == True
    assert item_data == {
        "id": "1",
        "item_resource_type": {
            "resourceuri": "http://purl.org/coar/resource_type/c_c94f",
            "resourcetype": "conference output"
        }
    }
    assert rec_data == {
        "recid": "1",
        "item_title": "Sample",
        "item_type_id": "1",
        "item_resource_type": {
            "attribute_name": "resource_type",
            "attribute_value_mlt":[
                {
                    "resourceuri": "http://purl.org/coar/resource_type/c_c94f",
                    "resourcetype": "conference output"
                }
            ]
        }
    }

    # case 40
    item_data = {
        "id": "1",
        "item_resource_type": {
            "resourceuri": "http://purl.org/coar/resource_type/c_26e4",
            "resourcetype": "interview"
        }
    }
    rec_data = {
        "recid": "1",
        "item_title": "Sample",
        "item_type_id": "1",
        "item_resource_type": {
            "attribute_name": "resource_type",
            "attribute_value_mlt":[
                {
                    "resourceuri": "http://purl.org/coar/resource_type/c_26e4",
                    "resourcetype": "interview"
                }
            ]
        }
    }
    assert change_resource_type_metadata(item_key, item_data, rec_data) == True
    assert item_data == {
        "id": "1",
        "item_resource_type": {
            "resourceuri": "http://purl.org/coar/resource_type/c_1843",
            "resourcetype": "other"
        }
    }
    assert rec_data == {
        "recid": "1",
        "item_title": "Sample",
        "item_type_id": "1",
        "item_resource_type": {
            "attribute_name": "resource_type",
            "attribute_value_mlt":[
                {
                    "resourceuri": "http://purl.org/coar/resource_type/c_1843",
                    "resourcetype": "other"
                }
            ]
        }
    }

    # case 41
    item_data = {
        "id": "1",
        "item_resource_type": {
            "resourceuri": "http://purl.org/coar/resource_type/c_18ww",
            "resourcetype": "internal report"
        }
    }
    rec_data = {
        "recid": "1",
        "item_title": "Sample",
        "item_type_id": "1",
        "item_resource_type": {
            "attribute_name": "resource_type",
            "attribute_value_mlt":[
                {
                    "resourceuri": "http://purl.org/coar/resource_type/c_18ww",
                    "resourcetype": "internal report"
                }
            ]
        }
    }
    assert change_resource_type_metadata(item_key, item_data, rec_data) == True
    assert item_data == {
        "id": "1",
        "item_resource_type": {
            "resourceuri": "http://purl.org/coar/resource_type/c_1843",
            "resourcetype": "other"
        }
    }
    assert rec_data == {
        "recid": "1",
        "item_title": "Sample",
        "item_type_id": "1",
        "item_resource_type": {
            "attribute_name": "resource_type",
            "attribute_value_mlt":[
                {
                    "resourceuri": "http://purl.org/coar/resource_type/c_1843",
                    "resourcetype": "other"
                }
            ]
        }
    }

    # case 42
    item_data = {
        "id": "1",
        "item_resource_type": {
            "resourceuri": "http://purl.org/coar/resource_type/c_ba1f",
            "resourcetype": "report part"
        }
    }
    rec_data = None
    assert change_resource_type_metadata(item_key, item_data, rec_data) == True
    assert item_data == {
        "id": "1",
        "item_resource_type": {
            "resourceuri": "http://purl.org/coar/resource_type/c_1843",
            "resourcetype": "other"
        }
    }
    assert rec_data == None

    # case 43
    item_data = {
        "id": "1",
        "item_resource_type": {
            "resourceuri": "http://purl.org/coar/resource_type/c_1843",
            "resourcetype": "other"
        }
    }
    rec_data = {
        "recid": "1",
        "item_title": "Sample",
        "item_type_id": "1",
        "item_resource_type": {
            "attribute_name": "resource_type",
            "attribute_value_mlt":[
                {
                    "resourceuri": "http://purl.org/coar/resource_type/c_1843",
                    "resourcetype": "other"
                }
            ]
        }
    }
    assert change_resource_type_metadata(item_key, item_data, rec_data) == False
    assert item_data == {
        "id": "1",
        "item_resource_type": {
            "resourceuri": "http://purl.org/coar/resource_type/c_1843",
            "resourcetype": "other"
        }
    }
    assert rec_data == {
        "recid": "1",
        "item_title": "Sample",
        "item_type_id": "1",
        "item_resource_type": {
            "attribute_name": "resource_type",
            "attribute_value_mlt":[
                {
                    "resourceuri": "http://purl.org/coar/resource_type/c_1843",
                    "resourcetype": "other"
                }
            ]
        }
    }

    # case 86
    item_key = "item_test"
    item_data = {
        "id": "1",
        "item_resource_type": {
            "resourceuri": "http://purl.org/coar/resource_type/c_1843",
            "resourcetype": "other"
        }
    }
    rec_data = None
    assert change_resource_type_metadata(item_key, item_data, rec_data) == False
    assert item_data == {
        "id": "1",
        "item_resource_type": {
            "resourceuri": "http://purl.org/coar/resource_type/c_1843",
            "resourcetype": "other"
        }
    }
    assert rec_data == None


# .tox/c1/bin/pytest --cov=scripts tests/test_fix_metadata_53602.py::test_change_identifier_registration_metadata -vv -s --cov-branch --cov-report=term --cov-report=xml --basetemp=/code/scripts/.tox/c1/tmp
def test_change_identifier_registration_metadata():
    item_key = "item_identifier_registration"

    # case 44
    item_data = {
        "id": "1",
        "item_identifier_registration": {
            "subitem_identifier_reg_text": "10.18926",
            "subitem_identifier_reg_type": "PMID【現在不使用】"
        }
    }
    rec_data = {
        "recid": "1",
        "item_title": "Sample",
        "item_type_id": "1",
        "item_identifier_registration": {
            "attribute_name": "identifier_registration",
            "attribute_value_mlt":[
                {
                    "subitem_identifier_reg_text": "10.18926",
                    "subitem_identifier_reg_type": "PMID【現在不使用】"
                }
            ]
        }
    }
    assert change_identifier_registration_metadata(item_key, item_data, rec_data) == True
    assert item_data == {
        "id": "1",
        "item_identifier_registration": {
            "subitem_identifier_reg_text": "10.18926",
            "subitem_identifier_reg_type": "PMID"
        }
    }
    assert rec_data == {
        "recid": "1",
        "item_title": "Sample",
        "item_type_id": "1",
        "item_identifier_registration": {
            "attribute_name": "identifier_registration",
            "attribute_value_mlt":[
                {
                    "subitem_identifier_reg_text": "10.18926",
                    "subitem_identifier_reg_type": "PMID"
                }
            ]
        }
    }

    # case 87
    item_data = {
        "id": "1",
        "item_identifier_registration": {
            "subitem_identifier_reg_text": "10.18926",
            "subitem_identifier_reg_type": "PMID【現在不使用】"
        }
    }
    rec_data = None
    assert change_identifier_registration_metadata(item_key, item_data, rec_data) == True
    assert item_data == {
        "id": "1",
        "item_identifier_registration": {
            "subitem_identifier_reg_text": "10.18926",
            "subitem_identifier_reg_type": "PMID"
        }
    }
    assert rec_data == None

    # case 45
    item_data = {
        "id": "1",
        "item_identifier_registration": {
            "subitem_identifier_reg_text": "10.18926",
            "subitem_identifier_reg_type": "PMID"
        }
    }
    rec_data = {
        "recid": "1",
        "item_title": "Sample",
        "item_type_id": "1",
        "item_identifier_registration": {
            "attribute_name": "identifier_registration",
            "attribute_value_mlt":[
                {
                    "subitem_identifier_reg_text": "10.18926",
                    "subitem_identifier_reg_type": "PMID"
                }
            ]
        }
    }
    assert change_identifier_registration_metadata(item_key, item_data, rec_data) == False
    assert item_data == {
        "id": "1",
        "item_identifier_registration": {
            "subitem_identifier_reg_text": "10.18926",
            "subitem_identifier_reg_type": "PMID"
        }
    }
    assert rec_data == {
        "recid": "1",
        "item_title": "Sample",
        "item_type_id": "1",
        "item_identifier_registration": {
            "attribute_name": "identifier_registration",
            "attribute_value_mlt":[
                {
                    "subitem_identifier_reg_text": "10.18926",
                    "subitem_identifier_reg_type": "PMID"
                }
            ]
        }
    }


# .tox/c1/bin/pytest --cov=scripts tests/test_fix_metadata_53602.py::test_change_radiobutton_metadata -vv -s --cov-branch --cov-report=term --cov-report=xml --basetemp=/code/scripts/.tox/c1/tmp
def test_change_radiobutton_metadata():
    item_key = "item_radiobutton"

    # case 46
    item_data = {
        "id": "1",
        "item_radiobutton": {
            "subitem_textarea_value": "R1",
            "subitem_textarea_language": "en"
        }
    }
    rec_data = {
        "recid": "1",
        "item_title": "Sample",
        "item_type_id": "1",
        "item_radiobutton": {
            "attribute_name": "radiobutton",
            "attribute_value_mlt":[
                {
                    "subitem_textarea_value": "R1",
                    "subitem_textarea_language": "en"
                }
            ]
        }
    }
    assert change_radiobutton_metadata(item_key, item_data, rec_data) == True
    assert item_data == {
        "id": "1",
        "item_radiobutton": {
            "subitem_radio_item": "R1",
            "subitem_radio_language": "en"
        }
    }
    assert rec_data == {
        "recid": "1",
        "item_title": "Sample",
        "item_type_id": "1",
        "item_radiobutton": {
            "attribute_name": "radiobutton",
            "attribute_value_mlt":[
                {
                    "subitem_radio_item": "R1",
                    "subitem_radio_language": "en"
                }
            ]
        }
    }

    # case 47
    item_data = {
        "id": "1",
        "item_radiobutton": [
            {
                "subitem_radio_item": ["R1", "R2"],
                "subitem_radio_language": "en"
            }
        ]
    }
    rec_data = {
        "recid": "1",
        "item_title": "Sample",
        "item_type_id": "1",
        "item_radiobutton": {
            "attribute_name": "radiobutton",
            "attribute_value_mlt":[
                {
                    "subitem_radio_item": ["R1", "R2"],
                    "subitem_radio_language": "en"
                }
            ]
        }
    }
    assert change_radiobutton_metadata(item_key, item_data, rec_data) == True
    assert item_data == {
        "id": "1",
        "item_radiobutton": [
            {
                "subitem_radio_item": "R1",
                "subitem_radio_language": "en"
            }
        ]
    }
    assert rec_data == {
        "recid": "1",
        "item_title": "Sample",
        "item_type_id": "1",
        "item_radiobutton": {
            "attribute_name": "radiobutton",
            "attribute_value_mlt":[
                {
                    "subitem_radio_item": "R1",
                    "subitem_radio_language": "en"
                }
            ]
        }
    }

    # case 48
    item_data = {
        "id": "1",
        "item_radiobutton": [
            {
                "subitem_radio_item": "R1",
                "subitem_radio_language": "en"
            }
        ]
    }
    rec_data = {
        "recid": "1",
        "item_title": "Sample",
        "item_type_id": "1",
        "item_radiobutton": {
            "attribute_name": "radiobutton",
            "attribute_value_mlt":[
                {
                    "subitem_radio_item": "R1",
                    "subitem_radio_language": "en"
                }
            ]
        }
    }
    assert change_radiobutton_metadata(item_key, item_data, rec_data) == False
    assert item_data == {
        "id": "1",
        "item_radiobutton": [
            {
                "subitem_radio_item": "R1",
                "subitem_radio_language": "en"
            }
        ]
    }
    assert rec_data == {
        "recid": "1",
        "item_title": "Sample",
        "item_type_id": "1",
        "item_radiobutton": {
            "attribute_name": "radiobutton",
            "attribute_value_mlt":[
                {
                    "subitem_radio_item": "R1",
                    "subitem_radio_language": "en"
                }
            ]
        }
    }

    # case 88
    item_data = {
        "id": "1",
        "item_radiobutton": "R1"
    }
    rec_data = {}
    assert change_radiobutton_metadata(item_key, item_data, rec_data) == False
    assert item_data == {
        "id": "1",
        "item_radiobutton": "R1"
    }
    assert rec_data == {}

    # case 89
    item_data = {
        "id": "1",
        "item_test": {}
    }
    rec_data = {}
    assert change_radiobutton_metadata(item_key, item_data, rec_data) == False
    assert item_data == {
        "id": "1",
        "item_test": {}
    }
    assert rec_data == {}

    # case 90
    item_data = {
        "id": "1",
        "item_radiobutton": {
            "subitem_textarea_value": "R1"
        }
    }
    rec_data = {}
    assert change_radiobutton_metadata(item_key, item_data, rec_data) == True
    assert item_data == {
        "id": "1",
        "item_radiobutton": {
            "subitem_radio_item": "R1"
        }
    }
    assert rec_data == {}


# .tox/c1/bin/pytest --cov=scripts tests/test_fix_metadata_53602.py::test_change_listbox_metadata -vv -s --cov-branch --cov-report=term --cov-report=xml --basetemp=/code/scripts/.tox/c1/tmp
def test_change_listbox_metadata():
    item_key = "item_listbox"

    # case 49
    item_data = {
        "id": "1",
        "item_listbox": {
            "subitem_textarea_value": "L1",
            "subitem_textarea_language": "en"
        }
    }
    rec_data = {
        "recid": "1",
        "item_title": "Sample",
        "item_type_id": "1",
        "item_listbox": {
            "attribute_name": "listbox",
            "attribute_value_mlt":[
                {
                    "subitem_textarea_value": "L1",
                    "subitem_textarea_language": "en"
                }
            ]
        }
    }
    assert change_listbox_metadata(item_key, item_data, rec_data) == True
    assert item_data == {
        "id": "1",
        "item_listbox": {
            "subitem_select_item": "L1",
            "subitem_select_language": "en"
        }
    }
    assert rec_data == {
        "recid": "1",
        "item_title": "Sample",
        "item_type_id": "1",
        "item_listbox": {
            "attribute_name": "listbox",
            "attribute_value_mlt":[
                {
                    "subitem_select_item": "L1",
                    "subitem_select_language": "en"
                }
            ]
        }
    }

    # case 50
    item_data = {
        "id": "1",
        "item_listbox": [
            {
                "subitem_select_item": ["L1", "L2"],
                "subitem_select_language": "en"
            }
        ]
    }
    rec_data = {
        "recid": "1",
        "item_title": "Sample",
        "item_type_id": "1",
        "item_listbox": {
            "attribute_name": "listbox",
            "attribute_value_mlt":[
                {
                    "subitem_select_item": ["L1", "L2"],
                    "subitem_select_language": "en"
                }
            ]
        }
    }
    assert change_listbox_metadata(item_key, item_data, rec_data) == True
    assert item_data == {
        "id": "1",
        "item_listbox": [
            {
                "subitem_select_item": "L1",
                "subitem_select_language": "en"
            }
        ]
    }
    assert rec_data == {
        "recid": "1",
        "item_title": "Sample",
        "item_type_id": "1",
        "item_listbox": {
            "attribute_name": "listbox",
            "attribute_value_mlt":[
                {
                    "subitem_select_item": "L1",
                    "subitem_select_language": "en"
                }
            ]
        }
    }

    # case 51
    item_data = {
        "id": "1",
        "item_listbox": [
            {
                "subitem_select_item": "L1",
                "subitem_select_language": "en"
            }
        ]
    }
    rec_data = {
        "recid": "1",
        "item_title": "Sample",
        "item_type_id": "1",
        "item_listbox": {
            "attribute_name": "listbox",
            "attribute_value_mlt":[
                {
                    "subitem_select_item": "L1",
                    "subitem_select_language": "en"
                }
            ]
        }
    }
    assert change_listbox_metadata(item_key, item_data, rec_data) == False
    assert item_data == {
        "id": "1",
        "item_listbox": [
            {
                "subitem_select_item": "L1",
                "subitem_select_language": "en"
            }
        ]
    }
    assert rec_data == {
        "recid": "1",
        "item_title": "Sample",
        "item_type_id": "1",
        "item_listbox": {
            "attribute_name": "listbox",
            "attribute_value_mlt":[
                {
                    "subitem_select_item": "L1",
                    "subitem_select_language": "en"
                }
            ]
        }
    }

    # case 91
    item_data = {
        "id": "1",
        "item_listbox": "L1"
    }
    rec_data = {}
    assert change_listbox_metadata(item_key, item_data, rec_data) == False
    assert item_data == {
        "id": "1",
        "item_listbox": "L1"
    }
    assert rec_data == {}

    # case 92
    item_data = {
        "id": "1",
        "item_test": {}
    }
    rec_data = {}
    assert change_listbox_metadata(item_key, item_data, rec_data) == False
    assert item_data == {
        "id": "1",
        "item_test": {}
    }
    assert rec_data == {}

    # case 93
    item_data = {
        "id": "1",
        "item_listbox": {
            "subitem_textarea_value": "L1"
        }
    }
    rec_data = {}
    assert change_listbox_metadata(item_key, item_data, rec_data) == True
    assert item_data == {
        "id": "1",
        "item_listbox": {
            "subitem_select_item": "L1"
        }
    }
    assert rec_data == {}


# .tox/c1/bin/pytest --cov=scripts tests/test_fix_metadata_53602.py::test_change_dcndl_original_language_metadata -vv -s --cov-branch --cov-report=term --cov-report=xml --basetemp=/code/scripts/.tox/c1/tmp
def test_change_dcndl_original_language_metadata():
    item_key = "item_dcndl_original_language"

    # case 52
    item_data = {
        "id": "1",
        "item_dcndl_original_language": {
            "original_language": "Japan",
            "original_language_language": "en"
        }
    }
    rec_data = {
        "recid": "1",
        "item_title": "Sample",
        "item_type_id": "1",
        "item_dcndl_original_language": {
            "attribute_name": "dcndl_original_language",
            "attribute_value_mlt":[
                {
                    "original_language": "Japan",
                    "original_language_language": "en"
                }
            ]
        }
    }
    assert change_dcndl_original_language_metadata(item_key, item_data, rec_data) == True
    assert item_data == {
        "id": "1",
        "item_dcndl_original_language": {
            "original_language": "eng"
        }
    }
    assert rec_data == {
        "recid": "1",
        "item_title": "Sample",
        "item_type_id": "1",
        "item_dcndl_original_language": {
                "attribute_name": "dcndl_original_language",
                "attribute_value_mlt":[
                {
                    "original_language": "eng"
                }
            ]
        }
    }

    # case 53
    item_data = {
        "id": "1",
        "item_dcndl_original_language": [
            {
                "original_language": "日本語"
            },
            {
                "original_language": "japan"
            }
        ]
    }
    rec_data = {
        "recid": "1",
        "item_title": "Sample",
        "item_type_id": "1",
        "item_dcndl_original_language": {
            "attribute_name": "dcndl_original_language",
            "attribute_value_mlt":[
                {
                    "original_language": "日本語"
                },
                {
                    "original_language": "japan"
                }
            ]
        }
    }
    assert change_dcndl_original_language_metadata(item_key, item_data, rec_data) == True
    assert item_data == {
        "id": "1",
        "item_dcndl_original_language": [
            {
                "original_language": "jpn"
            },
            {
                "original_language": "japan"
            }
        ]
    }
    assert rec_data == {
        "recid": "1",
        "item_title": "Sample",
        "item_type_id": "1",
        "item_dcndl_original_language": {
            "attribute_name": "dcndl_original_language",
            "attribute_value_mlt":[
                {
                    "original_language": "jpn"
                },
                {
                    "original_language": "japan"
                }
            ]
        }
    }

    # case 54
    item_data = {
        "id": "1",
        "item_dcndl_original_language": [
            {
                "original_language": "jpn"
            },
            {
                "original_language": "japan"
            }
        ]
    }
    rec_data = {
        "recid": "1",
        "item_title": "Sample",
        "item_type_id": "1",
        "item_dcndl_original_language": {
            "attribute_name": "dcndl_original_language",
            "attribute_value_mlt":[
                {
                    "original_language": "jpn"
                },
                {
                    "original_language": "japan"
                }
            ]
        }
    }
    assert change_dcndl_original_language_metadata(item_key, item_data, rec_data) == False
    assert item_data == {
        "id": "1",
        "item_dcndl_original_language": [
            {
                "original_language": "jpn"
            },
            {
                "original_language": "japan"
            }
        ]
    }
    assert rec_data == {
        "recid": "1",
        "item_title": "Sample",
        "item_type_id": "1",
        "item_dcndl_original_language": {
            "attribute_name": "dcndl_original_language",
            "attribute_value_mlt":[
                {
                    "original_language": "jpn"
                },
                {
                    "original_language": "japan"
                }
            ]
        }
    }

    # case 94
    item_data = {
        "id": "1",
        "item_dcndl_original_language": {
            "original_language": "jpn",
            "original_language_language": ""
        }
    }
    rec_data = {}
    assert change_dcndl_original_language_metadata(item_key, item_data, rec_data) == True
    item_data = {
        "id": "1",
        "item_dcndl_original_language": {
            "original_language": "jpn"
        }
    }
    rec_data = {}

    # case 95
    item_data = {
        "id": "1",
        "item_dcndl_original_language": {
            "original_language": "jpn"
        }
    }
    rec_data = {}
    assert change_dcndl_original_language_metadata(item_key, item_data, rec_data) == False
    assert item_data == {
        "id": "1",
        "item_dcndl_original_language": {
            "original_language": "jpn"
        }
    }
    assert rec_data == {}

    # case 96
    item_data = {
        "id": "1",
        "item_dcndl_original_language": [
            {
                "original_language": "jpn"
            }
        ]
    }
    rec_data = {}
    assert change_dcndl_original_language_metadata(item_key, item_data, rec_data) == False
    assert item_data == {
        "id": "1",
        "item_dcndl_original_language": [
            {
                "original_language": "jpn"
            }
        ]
    }
    assert rec_data == {}

    # case 97
    item_data = {
        "id": "1",
        "item_dcndl_original_language": "jpn"
    }
    rec_data = {}
    assert change_dcndl_original_language_metadata(item_key, item_data, rec_data) == False
    assert item_data == {
        "id": "1",
        "item_dcndl_original_language": "jpn"
    }
    assert rec_data == {}

    # case 98
    item_data = {
        "id": "1",
        "item_original_language": {
            "original_language": "jpn"
        }
    }
    rec_data = {}
    assert change_dcndl_original_language_metadata(item_key, item_data, rec_data) == False
    assert item_data == {
        "id": "1",
        "item_original_language": {
            "original_language": "jpn"
        }
    }
    assert rec_data == {}


# .tox/c1/bin/pytest --cov=scripts tests/test_fix_metadata_53602.py::test_change_jpcoar_format_metadata -vv -s --cov-branch --cov-report=term --cov-report=xml --basetemp=/code/scripts/.tox/c1/tmp
def test_change_jpcoar_format_metadata():
    item_key = "item_jpcoar_format"

    # case 55
    item_data = {
        "id": "1",
        "item_jpcoar_format": [
            {
                "jpcoar_format": "折本",
                "json_format_language": "ja"
            }
        ]
    }
    rec_data = {
        "recid": "1",
        "item_title": "Sample",
        "item_type_id": "1",
        "item_jpcoar_format": {
            "attribute_name": "jpcoar_format",
            "attribute_value_mlt":[
                {
                    "jpcoar_format": "折本",
                    "json_format_language": "ja"
                }
            ]
        }
    }
    assert change_jpcoar_format_metadata(item_key, item_data, rec_data) == True
    assert item_data == {
        "id": "1",
        "item_jpcoar_format": [
            {
                "jpcoar_format": "折本",
                "jpcoar_format_language": "ja"
            }
        ]
    }
    assert rec_data == {
        "recid": "1",
        "item_title": "Sample",
        "item_type_id": "1",
        "item_jpcoar_format": {
            "attribute_name": "jpcoar_format",
            "attribute_value_mlt":[
                {
                    "jpcoar_format": "折本",
                    "jpcoar_format_language": "ja"
                }
            ]
        }
    }

    # case 56
    item_data = {
        "id": "1",
        "item_jpcoar_format": [
            {
                "jpcoar_format": "折本",
                "jpcoar_format_language": "ja"
            }
        ]
    }
    rec_data = {
        "recid": "1",
        "item_title": "Sample",
        "item_type_id": "1",
        "item_jpcoar_format": {
                "attribute_name": "jpcoar_format",
                "attribute_value_mlt":[
                {
                    "jpcoar_format": "折本",
                    "jpcoar_format_language": "ja"
                }
            ]
        }
    }
    assert change_jpcoar_format_metadata(item_key, item_data, rec_data) == False
    assert item_data == {
        "id": "1",
        "item_jpcoar_format": [
            {
                "jpcoar_format": "折本",
                "jpcoar_format_language": "ja"
            }
        ]
    }
    assert rec_data == {
        "recid": "1",
        "item_title": "Sample",
        "item_type_id": "1",
        "item_jpcoar_format": {
                "attribute_name": "jpcoar_format",
                "attribute_value_mlt":[
                {
                    "jpcoar_format": "折本",
                    "jpcoar_format_language": "ja"
                }
            ]
        }
    }

    # case 99
    item_data = {
        "id": "1",
        "item_format": [
            {
                "jpcoar_format": "折本",
                "jpcoar_format_language": "ja"
            }
        ]
    }
    rec_data = {}
    assert change_jpcoar_format_metadata(item_key, item_data, rec_data) == False
    assert item_data == {
        "id": "1",
        "item_format": [
            {
                "jpcoar_format": "折本",
                "jpcoar_format_language": "ja"
            }
        ]
    }
    assert rec_data == {}

    # case 100
    item_data = {
        "id": "1",
        "item_jpcoar_format": {
            "jpcoar_format": "折本",
            "jpcoar_format_language": "ja"
        }
    }
    rec_data = {}
    assert change_jpcoar_format_metadata(item_key, item_data, rec_data) == False
    assert item_data == {
        "id": "1",
        "item_jpcoar_format": {
            "jpcoar_format": "折本",
            "jpcoar_format_language": "ja"
        }
    }
    assert rec_data == {}

    # case 101
    item_data = {
        "id": "1",
        "item_jpcoar_format": "折本"
    }
    rec_data = {}
    assert change_jpcoar_format_metadata(item_key, item_data, rec_data) == False
    assert item_data == {
        "id": "1",
        "item_jpcoar_format": "折本"
    }
    assert rec_data == {}


# .tox/c1/bin/pytest --cov=scripts tests/test_fix_metadata_53602.py::test_change_jpcoar_holding_agent_metadata -vv -s --cov-branch --cov-report=term --cov-report=xml --basetemp=/code/scripts/.tox/c1/tmp
def test_change_jpcoar_holding_agent_metadata():
    item_key = "item_jpcoar_holding_agent"

    # case 57
    item_data = {
        "id": "1",
        "item_jpcoar_holding_agent": {
                "holding_agent_name_identifier": {
                "holding_agent_name_identifier_scheme": "ISNI",
                "holding_agent_name_idenfitier_value": "121691048"
            },
            "holding_agent_names": [
                {
                    "holding_agent_name": "The University of Tokyo",
                    "holding_agent_names_language": "en"
                }
            ]
        }
    }
    rec_data = {
        "recid": "1",
        "item_title": "Sample",
        "item_type_id": "1",
        "item_jpcoar_holding_agent": {
            "attribute_name": "jpcoar_holding_agent",
            "attribute_value_mlt":[
                {
                    "holding_agent_name_identifier": {
                        "holding_agent_name_identifier_scheme": "ISNI",
                        "holding_agent_name_idenfitier_value": "121691048"
                    },
                    "holding_agent_names": [
                        {
                            "holding_agent_name": "The University of Tokyo",
                            "holding_agent_names_language": "en"
                        }
                    ]
                }
            ]
        }
    }
    assert change_jpcoar_holding_agent_metadata(item_key, item_data, rec_data) == True
    assert item_data == {
        "id": "1",
        "item_jpcoar_holding_agent": {
            "holding_agent_name_identifier": {
                "holding_agent_name_identifier_scheme": "ISNI",
                "holding_agent_name_identifier_value": "121691048"
            },
            "holding_agent_names": [
                {
                    "holding_agent_name": "The University of Tokyo",
                    "holding_agent_name_language": "en"
                }
            ]
        }
    }
    assert rec_data == {
        "recid": "1",
        "item_title": "Sample",
        "item_type_id": "1",
        "item_jpcoar_holding_agent": {
            "attribute_name": "jpcoar_holding_agent",
            "attribute_value_mlt":[
                {
                    "holding_agent_name_identifier": {
                        "holding_agent_name_identifier_scheme": "ISNI",
                        "holding_agent_name_identifier_value": "121691048"
                    },
                    "holding_agent_names": [
                        {
                            "holding_agent_name": "The University of Tokyo",
                            "holding_agent_name_language": "en"
                        }
                    ]
                }
            ]
        }
    }

    # case 58
    item_data = {
        "id": "1",
        "item_jpcoar_holding_agent": {
            "holding_agent_name_identifier": {
                "holding_agent_name_identifier_scheme": "ISNI",
                "holding_agent_name_identifier_value": "121691048"
            },
            "holding_agent_names": [
                {
                    "holding_agent_name": "The University of Tokyo",
                    "holding_agent_name_language": "en"
                }
            ]
        }
    }
    rec_data = {
        "recid": "1",
        "item_title": "Sample",
        "item_type_id": "1",
        "item_jpcoar_holding_agent": {
            "attribute_name": "jpcoar_holding_agent",
            "attribute_value_mlt":[
                {
                    "holding_agent_name_identifier": {
                        "holding_agent_name_identifier_scheme": "ISNI",
                        "holding_agent_name_identifier_value": "121691048"
                    },
                    "holding_agent_names": [
                        {
                            "holding_agent_name": "The University of Tokyo",
                            "holding_agent_name_language": "en"
                        }
                    ]
                }
            ]
        }
    }
    assert change_jpcoar_holding_agent_metadata(item_key, item_data, rec_data) == False
    assert item_data == {
        "id": "1",
        "item_jpcoar_holding_agent": {
            "holding_agent_name_identifier": {
                "holding_agent_name_identifier_scheme": "ISNI",
                "holding_agent_name_identifier_value": "121691048"
            },
            "holding_agent_names": [
                {
                    "holding_agent_name": "The University of Tokyo",
                    "holding_agent_name_language": "en"
                }
            ]
        }
    }
    assert rec_data == {
        "recid": "1",
        "item_title": "Sample",
        "item_type_id": "1",
        "item_jpcoar_holding_agent": {
            "attribute_name": "jpcoar_holding_agent",
            "attribute_value_mlt":[
                {
                    "holding_agent_name_identifier": {
                        "holding_agent_name_identifier_scheme": "ISNI",
                        "holding_agent_name_identifier_value": "121691048"
                    },
                    "holding_agent_names": [
                        {
                            "holding_agent_name": "The University of Tokyo",
                            "holding_agent_name_language": "en"
                        }
                    ]
                }
            ]
        }
    }

    # case 102
    item_data = {
        "id": "1",
        "item_holding_agent": {
            "holding_agent_name_identifier": {
                "holding_agent_name_identifier_scheme": "ISNI",
                "holding_agent_name_identifier_value": "121691048"
            },
            "holding_agent_names": [
                {
                    "holding_agent_name": "The University of Tokyo",
                    "holding_agent_name_language": "en"
                }
            ]
        }
    }
    rec_data = {}
    assert change_jpcoar_holding_agent_metadata(item_key, item_data, rec_data) == False
    assert item_data == {
        "id": "1",
        "item_holding_agent": {
            "holding_agent_name_identifier": {
                "holding_agent_name_identifier_scheme": "ISNI",
                "holding_agent_name_identifier_value": "121691048"
            },
            "holding_agent_names": [
                {
                    "holding_agent_name": "The University of Tokyo",
                    "holding_agent_name_language": "en"
                }
            ]
        }
    }
    assert rec_data == {}

    # case 103
    item_data = {
        "id": "1",
        "item_jpcoar_holding_agent": {
            "holding_agent_names": [
                {
                    "holding_agent_name": "The University of Tokyo",
                    "holding_agent_name_language": "en"
                }
            ]
        }
    }
    rec_data = {}
    assert change_jpcoar_holding_agent_metadata(item_key, item_data, rec_data) == False
    assert item_data == {
        "id": "1",
        "item_jpcoar_holding_agent": {
            "holding_agent_names": [
                {
                    "holding_agent_name": "The University of Tokyo",
                    "holding_agent_name_language": "en"
                }
            ]
        }
    }
    assert rec_data == {}

    # case 104
    item_data = {
        "id": "1",
        "item_jpcoar_holding_agent": {
            "holding_agent_name_identifier": {
                "holding_agent_name_identifier_scheme": "ISNI",
                "holding_agent_name_identifier_value": "121691048"
            }
        }
    }
    rec_data = {}
    assert change_jpcoar_holding_agent_metadata(item_key, item_data, rec_data) == False
    assert item_data == {
        "id": "1",
        "item_jpcoar_holding_agent": {
            "holding_agent_name_identifier": {
                "holding_agent_name_identifier_scheme": "ISNI",
                "holding_agent_name_identifier_value": "121691048"
            }
        }
    }
    assert rec_data == {}

    # case 105
    item_data = {
        "id": "1",
        "item_jpcoar_holding_agent": {
            "holding_agent_name_identifier": {
                "holding_agent_name_identifier_scheme": "ISNI",
                "holding_agent_name_idenfitier_value": "121691048"
            },
            "holding_agent_names": [
                {
                    "holding_agent_name": "The University of Tokyo",
                    "holding_agent_names_language": "en"
                }
            ]
        }
    }
    rec_data = {
        "recid": "1",
        "item_title": "Sample",
        "item_type_id": "1",
        "item_jpcoar_holding_agent": {
            "attribute_name": "jpcoar_holding_agent",
            "attribute_value_mlt":[
                {
                    "holding_agent_name_identifier": {
                        "holding_agent_name_identifier_scheme": "ISNI",
                        "holding_agent_name_identifier_value": "121691048"
                    },
                    "holding_agent_names": [
                        {
                            "holding_agent_name": "The University of Tokyo",
                            "holding_agent_name_language": "en"
                        }
                    ]
                }
            ]
        }
    }
    assert change_jpcoar_holding_agent_metadata(item_key, item_data, rec_data) == True
    assert item_data == {
        "id": "1",
        "item_jpcoar_holding_agent": {
            "holding_agent_name_identifier": {
                "holding_agent_name_identifier_scheme": "ISNI",
                "holding_agent_name_identifier_value": "121691048"
            },
            "holding_agent_names": [
                {
                    "holding_agent_name": "The University of Tokyo",
                    "holding_agent_name_language": "en"
                }
            ]
        }
    }
    assert rec_data == {
        "recid": "1",
        "item_title": "Sample",
        "item_type_id": "1",
        "item_jpcoar_holding_agent": {
            "attribute_name": "jpcoar_holding_agent",
            "attribute_value_mlt":[
                {
                    "holding_agent_name_identifier": {
                        "holding_agent_name_identifier_scheme": "ISNI",
                        "holding_agent_name_identifier_value": "121691048"
                    },
                    "holding_agent_names": [
                        {
                            "holding_agent_name": "The University of Tokyo",
                            "holding_agent_name_language": "en"
                        }
                    ]
                }
            ]
        }
    }

    # case 106
    item_data = {
        "id": "1",
        "item_jpcoar_holding_agent": {
            "holding_agent_name_identifier": {
                "holding_agent_name_identifier_scheme": "ISNI",
                "holding_agent_name_idenfitier_value": "121691048"
            },
            "holding_agent_names": [
                {
                    "holding_agent_name": "The University of Tokyo",
                    "holding_agent_names_language": "en"
                }
            ]
        }
    }
    rec_data = {}
    assert change_jpcoar_holding_agent_metadata(item_key, item_data, rec_data) == True
    assert item_data == {
        "id": "1",
        "item_jpcoar_holding_agent": {
            "holding_agent_name_identifier": {
                "holding_agent_name_identifier_scheme": "ISNI",
                "holding_agent_name_identifier_value": "121691048"
            },
            "holding_agent_names": [
                {
                    "holding_agent_name": "The University of Tokyo",
                    "holding_agent_name_language": "en"
                }
            ]
        }
    }
    assert rec_data == {}


# .tox/c1/bin/pytest --cov=scripts tests/test_fix_metadata_53602.py::test_change_jpcoar_catalog_metadata -vv -s --cov-branch --cov-report=term --cov-report=xml --basetemp=/code/scripts/.tox/c1/tmp
def test_change_jpcoar_catalog_metadata():
    item_key = "item_jpcoar_catalog"

    # case 59
    item_data = {
        "id": "1",
        "item_jpcoar_catalog": {
            "catalog_subjects": [
                {
                    "catalog_subject_scheme": "e-Rad",
                    "catalog_subject": "人文学"
                }
            ]
        }
    }
    rec_data = {
        "recid": "1",
        "item_title": "Sample",
        "item_type_id": "1",
        "item_jpcoar_catalog": {
            "attribute_name": "jpcoar_catalog",
            "attribute_value_mlt":[
                {
                    "catalog_subjects": [
                        {
                            "catalog_subject_scheme": "e-Rad",
                            "catalog_subject": "人文学"
                        }
                    ]
                }
            ]
        }
    }
    assert change_jpcoar_catalog_metadata(item_key, item_data, rec_data) == True
    assert item_data == {
        "id": "1",
        "item_jpcoar_catalog": {
            "catalog_subjects": [
                {
                    "catalog_subject_scheme": "e-Rad_field",
                    "catalog_subject": "人文学"
                }
            ]
        }
    }
    assert rec_data == {
        "recid": "1",
        "item_title": "Sample",
        "item_type_id": "1",
        "item_jpcoar_catalog": {
            "attribute_name": "jpcoar_catalog",
            "attribute_value_mlt":[
                {
                    "catalog_subjects": [
                        {
                            "catalog_subject_scheme": "e-Rad_field",
                            "catalog_subject": "人文学"
                        }
                    ]
                }
            ]
        }
    }

    # case 107
    item_data = {
        "id": "1",
        "item_jpcoar_catalog": {
            "catalog_subjects": [
                {
                    "catalog_subject_scheme": "e-Rad_field",
                    "catalog_subject": "人文学"
                }
            ]
        }
    }
    rec_data = {}
    assert change_jpcoar_catalog_metadata(item_key, item_data, rec_data) == False
    assert item_data == {
        "id": "1",
        "item_jpcoar_catalog": {
            "catalog_subjects": [
                {
                    "catalog_subject_scheme": "e-Rad_field",
                    "catalog_subject": "人文学"
                }
            ]
        }
    }
    assert rec_data == {}

    # case 108
    item_data = {
        "id": "1",
        "item_jpcoar_catalog": {
            "catalog_subjects": [
                {
                    "catalog_subject_scheme": "e-Rad_field",
                    "catalog_subject": "人文学"
                }
            ]
        }
    }
    rec_data = {
        "recid": "1",
        "item_title": "Sample",
        "item_type_id": "1",
        "item_jpcoar_catalog": {
            "attribute_name": "jpcoar_catalog",
            "attribute_value_mlt":[
                {
                    "catalog_subjects": [
                        {
                            "catalog_subject_scheme": "e-Rad_field",
                            "catalog_subject": "人文学"
                        }
                    ]
                }
            ]
        }
    }
    assert change_jpcoar_catalog_metadata(item_key, item_data, rec_data) == False
    assert item_data == {
        "id": "1",
        "item_jpcoar_catalog": {
            "catalog_subjects": [
                {
                    "catalog_subject_scheme": "e-Rad_field",
                    "catalog_subject": "人文学"
                }
            ]
        }
    }
    assert rec_data == {
        "recid": "1",
        "item_title": "Sample",
        "item_type_id": "1",
        "item_jpcoar_catalog": {
            "attribute_name": "jpcoar_catalog",
            "attribute_value_mlt":[
                {
                    "catalog_subjects": [
                        {
                            "catalog_subject_scheme": "e-Rad_field",
                            "catalog_subject": "人文学"
                        }
                    ]
                }
            ]
        }
    }

    # case 60
    item_data = {
        "id": "1",
        "item_jpcoar_catalog": {
            "catalog_license": {
                "catalog_license_language": "en",
                "catalog_license_type": "metadata"
            },
            "catalog_licenses": [
                {
                    "catalog_license": "NO COPYRIGHT - CONTRACTUAL RESTRICTIONS"
                },
                {
                    "catalog_license": "Creative Commons CC0 1.0 Universal"
                }
            ]
        }
    }
    rec_data = {
        "recid": "1",
        "item_title": "Sample",
        "item_type_id": "1",
        "item_jpcoar_catalog": {
            "attribute_name": "jpcoar_catalog",
            "attribute_value_mlt":[
                {
                    "catalog_license": {
                        "catalog_license_language": "en",
                        "catalog_license_type": "metadata"
                    },
                    "catalog_licenses": [
                        {
                            "catalog_license": "NO COPYRIGHT - CONTRACTUAL RESTRICTIONS"
                        },
                        {
                            "catalog_license": "Creative Commons CC0 1.0 Universal"
                        }
                    ]
                }
            ]
        }
    }
    assert change_jpcoar_catalog_metadata(item_key, item_data, rec_data) == True
    assert item_data == {
        "id": "1",
        "item_jpcoar_catalog": {
            "catalog_licenses": [
                {
                    "catalog_license": "NO COPYRIGHT - CONTRACTUAL RESTRICTIONS",
                    "catalog_license_language": "en",
                    "catalog_license_type": "metadata"
                },
                {
                    "catalog_license": "Creative Commons CC0 1.0 Universal",
                    "catalog_license_language": "en",
                    "catalog_license_type": "metadata"
                }
            ]
        }
    }
    assert rec_data == {
        "recid": "1",
        "item_title": "Sample",
        "item_type_id": "1",
        "item_jpcoar_catalog": {
            "attribute_name": "jpcoar_catalog",
            "attribute_value_mlt":[
                {
                    "catalog_licenses": [
                        {
                            "catalog_license": "NO COPYRIGHT - CONTRACTUAL RESTRICTIONS",
                            "catalog_license_language": "en",
                            "catalog_license_type": "metadata"
                        },
                        {
                            "catalog_license": "Creative Commons CC0 1.0 Universal",
                            "catalog_license_language": "en",
                            "catalog_license_type": "metadata"
                        }
                    ]
                }
            ]
        }
    }

    # case 109
    item_data = {
        "id": "1",
        "item_jpcoar_catalog": {
            "catalog_license": {
                "catalog_license_language": "en",
                "catalog_license_type": "metadata"
            }
        }
    }
    rec_data = {
        "recid": "1",
        "item_title": "Sample",
        "item_type_id": "1",
        "item_jpcoar_catalog": {
            "attribute_name": "jpcoar_catalog",
            "attribute_value_mlt":[
                {
                    "catalog_license": {
                        "catalog_license_language": "en",
                        "catalog_license_type": "metadata"
                    }
                }
            ]
        }
    }
    assert change_jpcoar_catalog_metadata(item_key, item_data, rec_data) == True
    assert item_data == {
        "id": "1",
        "item_jpcoar_catalog": {
            "catalog_licenses": [
                {
                    "catalog_license_language": "en",
                    "catalog_license_type": "metadata"
                }
            ]
        }
    }
    assert rec_data == {
        "recid": "1",
        "item_title": "Sample",
        "item_type_id": "1",
        "item_jpcoar_catalog": {
            "attribute_name": "jpcoar_catalog",
            "attribute_value_mlt":[
                {
                    "catalog_licenses": [
                        {
                            "catalog_license_language": "en",
                            "catalog_license_type": "metadata"
                        }
                    ]
                }
            ]
        }
    }

    # case 110
    item_data = {
        "id": "1",
        "item_jpcoar_catalog": {
            "catalog_license": {
                "catalog_license_language": "en",
                "catalog_license_type": "metadata"
            },
            "catalog_licenses": [
                {
                    "catalog_license": "NO COPYRIGHT - CONTRACTUAL RESTRICTIONS",
                    "catalog_license_language": "en",
                    "catalog_license_type": "metadata"
                }
            ]
        }
    }
    rec_data = {
        "recid": "1",
        "item_title": "Sample",
        "item_type_id": "1",
        "item_jpcoar_catalog": {
            "attribute_name": "jpcoar_catalog",
            "attribute_value_mlt":[
                {
                    "catalog_license": {
                        "catalog_license_language": "en",
                        "catalog_license_type": "metadata"
                    },
                    "catalog_licenses": [
                        {
                            "catalog_license": "NO COPYRIGHT - CONTRACTUAL RESTRICTIONS",
                            "catalog_license_language": "en",
                            "catalog_license_type": "metadata"
                        }
                    ]
                }
            ]
        }
    }
    assert change_jpcoar_catalog_metadata(item_key, item_data, rec_data) == True
    assert item_data == {
        "id": "1",
        "item_jpcoar_catalog": {
            "catalog_licenses": [
                {
                    "catalog_license": "NO COPYRIGHT - CONTRACTUAL RESTRICTIONS",
                    "catalog_license_language": "en",
                    "catalog_license_type": "metadata"
                }
            ]
        }
    }
    assert rec_data == {
        "recid": "1",
        "item_title": "Sample",
        "item_type_id": "1",
        "item_jpcoar_catalog": {
            "attribute_name": "jpcoar_catalog",
            "attribute_value_mlt":[
                {
                    "catalog_licenses": [
                        {
                            "catalog_license": "NO COPYRIGHT - CONTRACTUAL RESTRICTIONS",
                            "catalog_license_language": "en",
                            "catalog_license_type": "metadata"
                        }
                    ]
                }
            ]
        }
    }

    # case 111
    item_data = {
        "id": "1",
        "item_jpcoar_catalog": {
            "catalog_license": {
                "catalog_license_language": "en",
                "catalog_license_type": "metadata"
            },
            "catalog_licenses": [
                {
                    "catalog_license": "NO COPYRIGHT - CONTRACTUAL RESTRICTIONS",
                    "catalog_license_language": "en",
                    "catalog_license_type": "metadata"
                }
            ]
        }
    }
    rec_data = {
        "recid": "1",
        "item_title": "Sample",
        "item_type_id": "1",
        "item_jpcoar_catalog": {
            "attribute_name": "jpcoar_catalog",
            "attribute_value_mlt":[
                {
                    "catalog_licenses": [
                        {
                            "catalog_license": "NO COPYRIGHT - CONTRACTUAL RESTRICTIONS",
                            "catalog_license_language": "en",
                            "catalog_license_type": "metadata"
                        }
                    ]
                }
            ]
        }
    }
    assert change_jpcoar_catalog_metadata(item_key, item_data, rec_data) == True
    assert item_data == {
        "id": "1",
        "item_jpcoar_catalog": {
            "catalog_licenses": [
                {
                    "catalog_license": "NO COPYRIGHT - CONTRACTUAL RESTRICTIONS",
                    "catalog_license_language": "en",
                    "catalog_license_type": "metadata"
                }
            ]
        }
    }
    assert rec_data == {
        "recid": "1",
        "item_title": "Sample",
        "item_type_id": "1",
        "item_jpcoar_catalog": {
            "attribute_name": "jpcoar_catalog",
            "attribute_value_mlt":[
                {
                    "catalog_licenses": [
                        {
                            "catalog_license": "NO COPYRIGHT - CONTRACTUAL RESTRICTIONS",
                            "catalog_license_language": "en",
                            "catalog_license_type": "metadata"
                        }
                    ]
                }
            ]
        }
    }

    # case 112
    item_data = {
        "id": "1",
        "item_jpcoar_catalog": {
            "catalog_license": {
                "catalog_license_language": "en",
                "catalog_license_type": "metadata"
            },
            "catalog_licenses": [
                {
                    "catalog_license": "NO COPYRIGHT - CONTRACTUAL RESTRICTIONS",
                    "catalog_license_language": "en",
                    "catalog_license_type": "metadata"
                }
            ]
        }
    }
    rec_data = {}
    assert change_jpcoar_catalog_metadata(item_key, item_data, rec_data) == True
    assert item_data == {
        "id": "1",
        "item_jpcoar_catalog": {
            "catalog_licenses": [
                {
                    "catalog_license": "NO COPYRIGHT - CONTRACTUAL RESTRICTIONS",
                    "catalog_license_language": "en",
                    "catalog_license_type": "metadata"
                }
            ]
        }
    }
    assert rec_data == {}

    # case 61
    item_data = {
        "id": "1",
        "item_jpcoar_catalog": {
            "catalog_access_rights": [
                {
                    "catalog_access_right_access_rights": "open access",
                    "catalog_access_right_rdf_resource": "http://purl.org/coar/access_right/c_abf2"
                },
                {
                    "catalog_access_right_access_rights": "restricted access",
                    "catalog_access_right_rdf_resource": "http://purl.org/coar/access_right/c_16ec"
                }
            ]
        }
    }
    rec_data = {
        "recid": "1",
        "item_title": "Sample",
        "item_type_id": "1",
        "item_jpcoar_catalog": {
            "attribute_name": "jpcoar_catalog",
            "attribute_value_mlt":[
                {
                    "catalog_access_rights": [
                        {
                            "catalog_access_right_access_rights": "open access",
                            "catalog_access_right_rdf_resource": "http://purl.org/coar/access_right/c_abf2"
                        },
                        {
                            "catalog_access_right_access_rights": "restricted access",
                            "catalog_access_right_rdf_resource": "http://purl.org/coar/access_right/c_16ec"
                        }
                    ]
                }
            ]
        }
    }
    assert change_jpcoar_catalog_metadata(item_key, item_data, rec_data) == True
    assert item_data == {
        "id": "1",
        "item_jpcoar_catalog": {
            "catalog_access_rights": [
                {
                    "catalog_access_right": "open access",
                    "catalog_access_right_rdf_resource": "http://purl.org/coar/access_right/c_abf2"
                },
                {
                    "catalog_access_right": "restricted access",
                    "catalog_access_right_rdf_resource": "http://purl.org/coar/access_right/c_16ec"
                }
            ]
        }
    }
    assert rec_data == {
        "recid": "1",
        "item_title": "Sample",
        "item_type_id": "1",
        "item_jpcoar_catalog": {
            "attribute_name": "jpcoar_catalog",
            "attribute_value_mlt":[
                {
                    "catalog_access_rights": [
                        {
                            "catalog_access_right": "open access",
                            "catalog_access_right_rdf_resource": "http://purl.org/coar/access_right/c_abf2"
                        },
                        {
                            "catalog_access_right": "restricted access",
                            "catalog_access_right_rdf_resource": "http://purl.org/coar/access_right/c_16ec"
                        }
                    ]
                }
            ]
        }
    }

    # case 113
    item_data = {
        "id": "1",
        "item_jpcoar_catalog": {
            "catalog_access_rights": [
                {
                    "catalog_access_right": "open access",
                    "catalog_access_right_rdf_resource": "http://purl.org/coar/access_right/c_abf2"
                }
            ]
        }
    }
    rec_data = {
        "recid": "1",
        "item_title": "Sample",
        "item_type_id": "1",
        "item_jpcoar_catalog": {
            "attribute_name": "jpcoar_catalog",
            "attribute_value_mlt":[
                {
                    "catalog_access_rights": [
                        {
                            "catalog_access_right": "open access",
                            "catalog_access_right_rdf_resource": "http://purl.org/coar/access_right/c_abf2"
                        }
                    ]
                }
            ]
        }
    }
    assert change_jpcoar_catalog_metadata(item_key, item_data, rec_data) == False
    assert item_data == {
        "id": "1",
        "item_jpcoar_catalog": {
            "catalog_access_rights": [
                {
                    "catalog_access_right": "open access",
                    "catalog_access_right_rdf_resource": "http://purl.org/coar/access_right/c_abf2"
                }
            ]
        }
    }
    assert rec_data == {
        "recid": "1",
        "item_title": "Sample",
        "item_type_id": "1",
        "item_jpcoar_catalog": {
            "attribute_name": "jpcoar_catalog",
            "attribute_value_mlt":[
                {
                    "catalog_access_rights": [
                        {
                            "catalog_access_right": "open access",
                            "catalog_access_right_rdf_resource": "http://purl.org/coar/access_right/c_abf2"
                        }
                    ]
                }
            ]
        }
    }

    # case 114
    item_data = {
        "id": "1",
        "item_jpcoar_catalog": {
            "catalog_access_rights": [
                {
                    "catalog_access_right": "open access",
                    "catalog_access_right_rdf_resource": "http://purl.org/coar/access_right/c_abf2"
                }
            ]
        }
    }
    rec_data = {}
    assert change_jpcoar_catalog_metadata(item_key, item_data, rec_data) == False
    assert item_data == {
        "id": "1",
        "item_jpcoar_catalog": {
            "catalog_access_rights": [
                {
                    "catalog_access_right": "open access",
                    "catalog_access_right_rdf_resource": "http://purl.org/coar/access_right/c_abf2"
                }
            ]
        }
    }
    assert rec_data == {}

    # case 62
    item_data = {
        "id": "1",
        "item_jpcoar_catalog": {
            "catalog_file": {
                "catalog_file_uri": "https://xxx.xxx.xxx.xxx/xxx/thumbnail.jpg",
                "catalog_file_object_type": "thumbnail"
            }
        }
    }
    rec_data = {
        "recid": "1",
        "item_title": "Sample",
        "item_type_id": "1",
        "item_jpcoar_catalog": {
            "attribute_name": "jpcoar_catalog",
            "attribute_value_mlt":[
                {
                    "catalog_file": {
                        "catalog_file_uri": "https://xxx.xxx.xxx.xxx/xxx/thumbnail.jpg",
                        "catalog_file_object_type": "thumbnail"
                    }
                }
            ]
        }
    }
    assert change_jpcoar_catalog_metadata(item_key, item_data, rec_data) == True
    assert item_data == {
        "id": "1",
        "item_jpcoar_catalog": {
            "catalog_file": {
                "catalog_file_uri": {
                    "catalog_file_uri_value": "https://xxx.xxx.xxx.xxx/xxx/thumbnail.jpg",
                    "catalog_file_object_type": "thumbnail"
                }
            }
        }
    }
    assert rec_data == {
        "recid": "1",
        "item_title": "Sample",
        "item_type_id": "1",
        "item_jpcoar_catalog": {
            "attribute_name": "jpcoar_catalog",
            "attribute_value_mlt":[
                {
                    "catalog_file": {
                        "catalog_file_uri": {
                            "catalog_file_uri_value": "https://xxx.xxx.xxx.xxx/xxx/thumbnail.jpg",
                            "catalog_file_object_type": "thumbnail"
                        }
                    }
                }
            ]
        }
    }

    # case 63
    item_data = {
        "id": "1",
        "item_jpcoar_catalog": {
            "catalog_file": {
                "catalog_file_uri": {
                    "catalog_file_uri_value": "https://xxx.xxx.xxx.xxx/xxx/thumbnail.jpg",
                    "catalog_file_object_type": "thumbnail"
                }
            }
        }
    }
    rec_data = {
        "recid": "1",
        "item_title": "Sample",
        "item_type_id": "1",
        "item_jpcoar_catalog": {
            "attribute_name": "jpcoar_catalog",
            "attribute_value_mlt":[
                {
                    "catalog_file": {
                        "catalog_file_uri": {
                            "catalog_file_uri_value": "https://xxx.xxx.xxx.xxx/xxx/thumbnail.jpg",
                            "catalog_file_object_type": "thumbnail"
                        }
                    }
                }
            ]
        }
    }
    assert change_jpcoar_catalog_metadata(item_key, item_data, rec_data) == False
    assert item_data == {
        "id": "1",
        "item_jpcoar_catalog": {
            "catalog_file": {
                "catalog_file_uri": {
                    "catalog_file_uri_value": "https://xxx.xxx.xxx.xxx/xxx/thumbnail.jpg",
                    "catalog_file_object_type": "thumbnail"
                }
            }
        }
    }
    assert rec_data == {
        "recid": "1",
        "item_title": "Sample",
        "item_type_id": "1",
        "item_jpcoar_catalog": {
            "attribute_name": "jpcoar_catalog",
            "attribute_value_mlt":[
                {
                    "catalog_file": {
                        "catalog_file_uri": {
                            "catalog_file_uri_value": "https://xxx.xxx.xxx.xxx/xxx/thumbnail.jpg",
                            "catalog_file_object_type": "thumbnail"
                        }
                    }
                }
            ]
        }
    }

    # case 115
    item_data = {
        "id": "1",
        "item_jpcoar_catalog": {
            "catalog_file": {
                "catalog_file_object_type": "thumbnail"
            }
        }
    }
    rec_data = {
        "recid": "1",
        "item_title": "Sample",
        "item_type_id": "1",
        "item_jpcoar_catalog": {
            "attribute_name": "jpcoar_catalog",
            "attribute_value_mlt":[
                {
                    "catalog_file": {
                        "catalog_file_object_type": "thumbnail"
                    }
                }
            ]
        }
    }
    assert change_jpcoar_catalog_metadata(item_key, item_data, rec_data) == True
    assert item_data == {
        "id": "1",
        "item_jpcoar_catalog": {
            "catalog_file": {
                "catalog_file_uri": {
                    "catalog_file_object_type": "thumbnail"
                }
            }
        }
    }
    assert rec_data == {
        "recid": "1",
        "item_title": "Sample",
        "item_type_id": "1",
        "item_jpcoar_catalog": {
            "attribute_name": "jpcoar_catalog",
            "attribute_value_mlt":[
                {
                    "catalog_file": {
                        "catalog_file_uri": {
                            "catalog_file_object_type": "thumbnail"
                        }
                    }
                }
            ]
        }
    }

    # case 116
    item_data = {
        "id": "1",
        "item_jpcoar_catalog": {
            "catalog_file": {
                "catalog_file_object_type": "thumbnail"
            }
        }
    }
    rec_data = {}
    assert change_jpcoar_catalog_metadata(item_key, item_data, rec_data) == True
    assert item_data == {
        "id": "1",
        "item_jpcoar_catalog": {
            "catalog_file": {
                "catalog_file_uri": {
                    "catalog_file_object_type": "thumbnail"
                }
            }
        }
    }
    assert rec_data == {}

    # case 117
    item_data = {
        "id": "1",
        "item_catalog": {
            "catalog_file": {
                "catalog_file_object_type": "thumbnail"
            }
        }
    }
    rec_data = {}
    assert change_jpcoar_catalog_metadata(item_key, item_data, rec_data) == False
    assert item_data == {
        "id": "1",
        "item_catalog": {
            "catalog_file": {
                "catalog_file_object_type": "thumbnail"
            }
        }
    }
    assert rec_data == {}
