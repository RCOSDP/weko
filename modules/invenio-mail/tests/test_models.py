from mock import patch

from invenio_mail.models import MailConfig, MailTemplates

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

class TestMailTemplates:
    # .tox/c1/bin/pytest --cov=invenio_mail tests/test_models.py::TestMailTemplates::test_toDict -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-mail/.tox/c1/tmp
    def test_toDict(self, app, mail_templates):
        expect = {
            'key': '1',
            'flag': True,
            'content': {
                'subject': 'test subject',
                'body': 'test body'
            },
            'genre_order': 1,
            'genre_key': 'Notification of secret URL provision',
            'genre_name': 'Notification of secret URL provision'
        }
        result = mail_templates.toDict()
        assert result == expect

    # .tox/c1/bin/pytest --cov=invenio_mail tests/test_models.py::TestMailTemplates::test_get_templates -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-mail/.tox/c1/tmp
    def test_get_templates(self, app, mail_templates, admin_settings, mocker):
        # secret_enabled is False and secret_genre_id is 1
        result = MailTemplates.get_templates()
        assert result == []

        # secret_enabled is True
        app.config['WEKO_ADMIN_RESTRICTED_ACCESS_SETTINGS'] = {
            'secret_URL_file_download': {
                'secret_enable': True
            }
        }
        expect = [
            {
                'key': '1',
                'flag': True,
                'content': {
                    'subject': 'test subject',
                    'body': 'test body'
                },
                'genre_order': 1,
                'genre_key': 'Notification of secret URL provision',
                'genre_name': 'Notification of secret URL provision'
            }
        ]
        with mocker.patch('weko_admin.models.AdminSettings.get', return_value=None):
            result = MailTemplates.get_templates()
            assert result == expect

        # Exception in toDict
        with mocker.patch('invenio_mail.models.MailTemplates.toDict', side_effect=Exception):
            result = MailTemplates.get_templates()
            assert result == []
    
    # .tox/c1/bin/pytest --cov=invenio_mail tests/test_models.py::TestMailTemplates::test_get_by_id -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-mail/.tox/c1/tmp
    def test_get_by_id(self, app, mail_templates):
        result = MailTemplates.get_by_id(1)
        assert result == mail_templates
    
    # .tox/c1/bin/pytest --cov=invenio_mail tests/test_models.py::TestMailTemplates::test_save_and_update -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-mail/.tox/c1/tmp
    def test_save_and_update(self, app, mail_templates):
        # test save_and_update
        data = {
            'key': '1',
            'content': {
                'subject': 'test subject',
                'body': 'test body'
            }
        }
        result = MailTemplates.save_and_update(data)
        assert result == True

        # test save_and_update with empty key
        data = {
            'key': '',
            'content': {
                'subject': 'test subject',
                'body': 'test body'
            }
        }
        result = MailTemplates.save_and_update(data)
        assert result == True

        # test save_and_update with exception
        with patch('invenio_db.db.session.commit', side_effect=Exception):
            result = MailTemplates.save_and_update(data)
            assert result == False

    # .tox/c1/bin/pytest --cov=invenio_mail tests/test_models.py::TestMailTemplates::test_delete_by_id -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-mail/.tox/c1/tmp
    def test_delete_by_id(self, app, mail_templates):
        # test delete_by_id
        result = MailTemplates.delete_by_id(1)
        assert result == True

        # test delete_by_id with exception
        with patch('invenio_db.db.session.commit', side_effect=Exception):
            result = MailTemplates.delete_by_id(1)
            assert result == False
