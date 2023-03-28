
from __future__ import absolute_import, print_function

from flask import Flask, url_for,make_response

from weko_bulkupdate import WekoBulkupdate
from weko_bulkupdate.views import blueprint

# .tox/c1/bin/pytest --cov=weko_bulkupdate tests/test_views.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-bulkupdate/.tox/c1/tmp
def test_index(mocker):
    app = Flask("testapp")
    app.config.update(
        SECRET_KEY="SECRET_KEY",
        TESTING=True,
        SERVER_NAME="test_server",
    )
    WekoBulkupdate(app)
    app.register_blueprint(blueprint)
    with app.app_context():
        print(url_for("weko_bulkupdate.index"))
        with app.test_client() as client:
            mock_render = mocker.patch("weko_bulkupdate.views.render_template",return_value=make_response())
            res = client.get(url_for("weko_bulkupdate.index"))
            assert res.status_code == 200
            mock_render.assert_called_with("weko_bulkupdate/index.html",module_name="WEKO-Bulkupdate")