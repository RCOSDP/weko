
from mock import patch

from invenio_mail.models import MailConfig
from invenio_mail.views import dbsession_clean, _app

# .tox/c1/bin/pytest --cov=invenio_mail tests/test_views.py::test_dbsession_clean -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-mail/.tox/c1/tmp
def test_dbsession_clean(app, db):

    # exist exception
    config1 = MailConfig(id=1,mail_server="localhost1",mail_port=25)
    db.session.add(config1)
    dbsession_clean(None)
    assert MailConfig.query.filter_by(id=1).first().mail_server =="localhost1"

    # raise Exception
    config2 = MailConfig(id=2,mail_server="localhost2",mail_port=25,)
    db.session.add(config2)
    with patch("invenio_mail.views.db.session.commit",side_effect=Exception):
        dbsession_clean(None)
        assert MailConfig.query.filter_by(id=2).first() is None

    # not exist exception
    config3 = MailConfig(id=2,mail_server="localhost3",mail_port=25,)
    db.session.add(config3)
    dbsession_clean(Exception)
    assert MailConfig.query.filter_by(id=3).first() is None