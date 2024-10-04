
import re
import pytest
from unittest.mock import patch
import responses
from datetime import datetime
from weko_index_tree.models import Index
from weko_admin.models import AdminLangSettings

from invenio_oaiharvester.models import HarvestSettings,HarvestLogs,OAIHarvestConfig
from invenio_oaiharvester.errors import NameOrUrlMissing
from invenio_oaiharvester.api import (
    list_records,
    get_records,
    get_info_by_oai_name,
    send_run_status_mail
)

# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_api.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp

# def _(x):
# def list_records(metadata_prefix=None, from_date=None, until_date=None,
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_api.py::test_list_records -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
@responses.activate
def test_list_records(app,db,sample_list_xml_no_sets,mocker):
    source_name = "arXiv"
    source = OAIHarvestConfig(
        name=source_name,
        baseurl="http://export.arxiv.org/oai2",
        metadataprefix="arXiv",
        setspecs="physics",
    )
    source.save()
    db.session.commit()

    mocker.patch("invenio_oaiharvester.api.get_info_by_oai_name",return_value=("http://export.arxiv.org/oai2","oai_dc","2023-01-10",""))
    url = "http://export.arxiv.org/oai2"
    responses.add(
        responses.GET,
        re.compile(r'http?://export.arxiv.org/oai2.*'),
        body=sample_list_xml_no_sets,
        content_type='text/xml'
    )

    request, records = list_records(metadata_prefix="oai_dc",name="arXiv",setspecs="")

    assert len(records) == 150

# def get_records(identifiers, metadata_prefix=None, url=None, name=None,
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_api.py::test_get_records -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
@responses.activate
def test_get_records(app,db,sample_record_xml,mocker):

    mocker.patch("invenio_oaiharvester.api.get_info_by_oai_name",return_value=("http://export.arxiv.org/oai2","oai_dc","2023-01-10","physics"))
    url = "http://export.arxiv.org/oai2"
    responses.add(
        responses.GET,
        url,
        body=sample_record_xml,
        content_type="text/xml"
    )
    identifiers = ["oai:arXiv.org:1507.03011"]
    # not name
    request, records = get_records(identifiers,metadata_prefix="oai_dc",url=url,name=None,encoding="utf-8")
    assert request.encoding == "utf-8"
    assert request.endpoint == "http://export.arxiv.org/oai2"
    assert request.oai_namespace == "{http://www.openarchives.org/OAI/2.0/}"
    assert len(records) == 1
    data = records[0].metadata
    assert data["title"] == ["The Distribution of Star Formation and Metals in the Low Surface\\n  Brightness Galaxy UGC 628"]


    # not url
    request, records = get_records(identifiers,metadata_prefix="oai_dc",name="test_name",encoding="utf-8")
    assert request.encoding == "utf-8"
    assert request.endpoint == "http://export.arxiv.org/oai2"
    assert request.oai_namespace == "{http://www.openarchives.org/OAI/2.0/}"
    assert len(records) == 1
    data = records[0].metadata
    assert data["title"] == ["The Distribution of Star Formation and Metals in the Low Surface\\n  Brightness Galaxy UGC 628"]

    ## metadata_prefix is None
    request, records = get_records(identifiers,metadata_prefix=None,name="test_name",encoding="utf-8")
    assert request.encoding == "utf-8"
    assert request.endpoint == "http://export.arxiv.org/oai2"
    assert request.oai_namespace == "{http://www.openarchives.org/OAI/2.0/}"
    assert len(records) == 1
    data = records[0].metadata
    assert data["title"] == ["The Distribution of Star Formation and Metals in the Low Surface\\n  Brightness Galaxy UGC 628"]

    # not name and url
    with pytest.raises(NameOrUrlMissing):
        request, records = get_records(identifiers,metadata_prefix="oai_dc",url=None,name=None,encoding="utf-8")



# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_api.py::test_get_info_by_oai_name -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
# def get_info_by_oai_name(name):
def test_get_info_by_oai_name(app,db):
    index = Index()
    db.session.add(index)
    db.session.commit()
    harvest = OAIHarvestConfig(
        id=1,
        baseurl="http://test1.org/",
        metadataprefix="test_prefix",
        name="test_config",
        lastrun=datetime(2023,1,10),
        setspecs="test_spec"
    )
    with patch("invenio_oaiharvester.api.get_oaiharvest_object",return_value=harvest):
        url, prefix, lastrun, specs = get_info_by_oai_name("test_config")
        assert url == "http://test1.org/"
        assert prefix == "test_prefix"
        assert lastrun == "2023-01-10"
        assert specs == "test_spec"

# def send_run_status_mail(harvesting, harvest_log):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_api.py::test_send_run_status_mail -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_send_run_status_mail(app,db,users,mocker):
    index = Index()
    db.session.add(index)
    db.session.commit()
    difference_harvest = HarvestSettings(
        id=1,
        repository_name="test_repo1",
        base_url="http://test1.org/",
        metadata_prefix="test_prefix",
        index_id=index.id,
        update_style="0"
    )
    bulk_harvest = HarvestSettings(
        id=2,
        repository_name="test_repo2",
        base_url="http://test1.org/",
        metadata_prefix="test_prefix",
        index_id=index.id,
        update_style="1"
    )
    db.session.add_all([difference_harvest,bulk_harvest])
    lang_setting = AdminLangSettings(lang_code="en",lang_name="English",)
    db.session.add(lang_setting)

    db.session.commit()

    success_logs = HarvestLogs(
        id=1,harvest_setting_id=1,status="Successful"
    )
    suspended_logs = HarvestLogs(
        id=2,harvest_setting_id=1,status="Suspended"
    )
    cancel_logs = HarvestLogs(
        id=3,harvest_setting_id=1,status="Cancel"
    )
    failed_logs = HarvestLogs(
        id=4,harvest_setting_id=1,status="Failed"
    )
    running_logs = HarvestLogs(
        id=5,harvest_setting_id=1,status="Running"
    )
    db.session.add_all([success_logs,suspended_logs,cancel_logs,failed_logs,running_logs])
    db.session.commit()

    # status is Successful
    mock_send = mocker.patch("invenio_oaiharvester.api.send_mail")
    mock_render = mocker.patch("invenio_oaiharvester.api.render_template",return_value="test_data")
    send_run_status_mail(difference_harvest,success_logs)
    args,kwargs = mock_send.call_args
    assert args == ("[WEKO3] Hervesting Result",["repoadmin@test.org","originalroleuser2@test.org","comadmin@test.org"])
    args,kwargs = mock_render.call_args
    assert kwargs["result_text"] == "Successful"
    assert kwargs["update_style"] == "Difference"

    # status is Suspended
    mock_send = mocker.patch("invenio_oaiharvester.api.send_mail")
    mock_render = mocker.patch("invenio_oaiharvester.api.render_template",return_value="test_data")
    send_run_status_mail(difference_harvest,suspended_logs)
    args,kwargs = mock_send.call_args
    assert args == ("[WEKO3] Hervesting Result",["repoadmin@test.org","originalroleuser2@test.org","comadmin@test.org"])
    args,kwargs = mock_render.call_args
    assert kwargs["result_text"] == "Suspended"
    assert kwargs["update_style"] == "Difference"

    # status is Cancel
    mock_send = mocker.patch("invenio_oaiharvester.api.send_mail")
    mock_render = mocker.patch("invenio_oaiharvester.api.render_template",return_value="test_data")
    send_run_status_mail(difference_harvest,cancel_logs)
    args,kwargs = mock_send.call_args
    assert args == ("[WEKO3] Hervesting Result",["repoadmin@test.org","originalroleuser2@test.org","comadmin@test.org"])
    args,kwargs = mock_render.call_args
    assert kwargs["result_text"] == "Cancel"
    assert kwargs["update_style"] == "Difference"

    # status is Failed
    mock_send = mocker.patch("invenio_oaiharvester.api.send_mail")
    mock_render = mocker.patch("invenio_oaiharvester.api.render_template",return_value="test_data")
    send_run_status_mail(difference_harvest,failed_logs)
    args,kwargs = mock_send.call_args
    assert args == ("[WEKO3] Hervesting Result",["repoadmin@test.org","originalroleuser2@test.org","comadmin@test.org"])
    args,kwargs = mock_render.call_args
    assert kwargs["result_text"] == "Failed"
    assert kwargs["update_style"] == "Difference"

    # status is Running
    mock_send = mocker.patch("invenio_oaiharvester.api.send_mail")
    mock_render = mocker.patch("invenio_oaiharvester.api.render_template",return_value="test_data")
    send_run_status_mail(difference_harvest,running_logs)
    args,kwargs = mock_send.call_args
    assert args == ("[WEKO3] Hervesting Result",["repoadmin@test.org","originalroleuser2@test.org","comadmin@test.org"])
    args,kwargs = mock_render.call_args
    assert kwargs["result_text"] == "Running"
    assert kwargs["update_style"] == "Difference"

    # harvest is bulk
    mock_send = mocker.patch("invenio_oaiharvester.api.send_mail")
    mock_render = mocker.patch("invenio_oaiharvester.api.render_template",return_value="test_data")
    send_run_status_mail(bulk_harvest,running_logs)
    args,kwargs = mock_send.call_args
    assert args == ("[WEKO3] Hervesting Result",["repoadmin@test.org","originalroleuser2@test.org","comadmin@test.org"])
    args,kwargs = mock_render.call_args
    assert kwargs["result_text"] == "Running"
    assert kwargs["update_style"] == "Bulk"

    with patch("invenio_oaiharvester.api.send_mail",side_effect=Exception("test_error")):
        send_run_status_mail(bulk_harvest,running_logs)

