

from invenio_mail.models import MailConfig

class TestMailConfig:
# .tox/c1/bin/pytest --cov=invenio_mail tests/test_models.py::TestMailConfig::test_get_config -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-mail/.tox/c1/tmp
    def test_get_config(app,db):
        # len MailConfig < 1
        assert len(MailConfig.query.all()) == 0
        result = MailConfig.get_config()
        assert len(MailConfig.query.all()) == 1
        assert result["mail_port"] == 25
        assert result["mail_server"] == "localhost"
        assert result["mail_use_tls"] == False
        assert result["mail_password"] == ""
        
        # len MailConfig >= 1
        result = MailConfig.get_config()
        assert len(MailConfig.query.all()) == 1
        assert result["mail_port"] == 25
        assert result["mail_server"] == "localhost"
        assert result["mail_use_tls"] == False
        assert result["mail_password"] == ""