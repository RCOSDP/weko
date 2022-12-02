
from flask import url_for,json
from invenio_accounts.testutils import login_user_via_session
from werkzeug.datastructures import FileStorage
from invenio_pidstore.models import PersistentIdentifier
from invenio_files_rest.models import Location
from invenio_records.models import RecordMetadata

# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_views.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp

# def post_service_document():
# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_views.py::test_function_issue34504 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp
def test_function_issue34504(client,db,users,esindex,location,index,make_zip,tokens,item_type,doi_identifier,mocker):
    login_user_via_session(client=client,email=users[0]["email"])
    token=tokens["token"].access_token
    url = url_for("weko_swordserver.post_service_document")
    headers = {
        "Authorization":"Bearer {}".format(token),
        "Content-Disposition":"attachment; filename=payload.zip",
        "Packaging":"http://purl.org/net/sword/3.0/package/SimpleZip"
    }
    def update_location_size():
        from decimal import Decimal
        loc = db.session.query(Location).filter(
                    Location.id == 1).one()
        loc.size = 1547
    mocker.patch("weko_swordserver.views._get_status_document",side_effect=lambda x:{"recid":x})
    mocker.patch("weko_search_ui.utils.find_and_update_location_size",side_effect=update_location_size)
    storage = FileStorage(filename="payload.zip",stream=make_zip)
    res = client.post(url, data=dict(file=storage),content_type="multipart/form-data",headers=headers)
    assert res.status_code == 200

    recid = PersistentIdentifier.get("recid","1").object_uuid
    record = RecordMetadata.query.filter_by(id=recid).one_or_none()
    assert record is not None
    record = record.json
    file_metadata = record["item_1617605131499"]["attribute_value_mlt"][0]
    assert file_metadata.get("url") is not None
    assert file_metadata.get("url").get("url") == "https://localhost/record/1/files/sample.html"
    assert json.loads(res.data) == {"recid":"1"}
