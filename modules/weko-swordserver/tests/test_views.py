

from flask import url_for,json
from invenio_accounts.testutils import login_user_via_session
from werkzeug.datastructures import FileStorage
# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_views.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp

# def post_service_document():
# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_views.py::test_post_service_document -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp
def test_post_service_document(client,users,make_zip,tokens,mocker):
    print("start_test")
    login_user_via_session(client=client,email=users[0]["email"])
    token=tokens["token"].access_token
    url = url_for("weko_swordserver.post_service_document")
    headers = {
        "Authorization":"Bearer {}".format(token),
        "Content-Disposition":"attachment; filename=payload.zip",
        "Packaging":"http://purl.org/net/sword/3.0/package/SimpleZip"
    }
    from zipfile import ZipFile
    with ZipFile(make_zip)as z:
        print(z.infolist())
    #data = {"file":(make_zip,"payload.zip")}
    data = {"file":FileStorage(filename="payload.zip",stream=make_zip)}

    print("token:{}".format(token))
    print("zip:{}".format(make_zip))
    print("url:{}".format(url))
    mocker.patch("weko_swordserver.views._get_status_document",side_effect=lambda x:{"recid":x})
    res = client.post(url,data=data,headers=headers)
    #res = client.post(url,headers=headers)
    assert json.loads(res.data) == {"recid":"x"}
