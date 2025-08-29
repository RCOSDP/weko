

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch
from invenio_accounts.models import User
from invenio_mail.models import (
    Timestamp, MailConfig, MailTemplates, MailTemplateUsers, MailType
)

# .tox/c1/bin/pytest --cov=invenio_mail tests/test_models.py::test_updated_timestamp_on_update -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-mail/.tox/c1/tmp
@patch('invenio_mail.models.datetime')
def test_updated_timestamp_on_update(
    mock_datetime, db, mail_template_fixture, mail_template_users_fixture
):
    mock_time = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    mock_datetime.now.return_value = mock_time
    user3 = User(id=3, email='user3@example.org')
    template = mail_template_fixture
    record = MailTemplateUsers(template=template, user=user3, mail_type=MailType.CC)
    db.session.add(record)
    db.session.commit()
    record = MailTemplateUsers.query.filter_by(user=user3).first()
    record.mail_type = MailType.BCC
    db.session.commit()
    mock_datetime.now.assert_called()
    assert record.updated == datetime(2024, 1, 1, 0, 0)


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
    def test_toDict(self, mail_template_fixture, mail_template_users_fixture):
        mail_template = mail_template_fixture
        result = mail_template.toDict()

        expected_result = {
            'key': str(1),
            'flag': True,
            'content': {
                'subject': 'Test Subject',
                'body': 'Test Body',
                'recipients': 'user1@example.com, user2@example.com',
                'cc': 'user1@example.com, user2@example.com',
                'bcc': 'user1@example.com, user2@example.com'
            },
            'genre_order': 1,
            'genre_key': 'Test Genre1',
            'genre_name': 'Test Genre1'
        }

        assert result == expected_result

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
                    'body': 'test body',
                    "recipients": '',
                    "cc": '',
                    "bcc": ''
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
    def test_save_and_update(self, mail_template_fixture):
        mt = MailTemplates()

        # update test
        with patch(
            'invenio_mail.models.MailTemplates.get_by_id',
            return_value=mail_template_fixture    
        ):
            existing_record_id = 1
            update_data = {
                'key': 1,
                'content': {
                    'subject': 'Updated Subject',
                    'body': 'Updated Body'
                }
            }
            result = mt.save_and_update(update_data)
            assert result == True
            updated_record = MailTemplates.query.get(existing_record_id)
            assert updated_record.mail_subject == 'Updated Subject'
            assert updated_record.mail_body == 'Updated Body'

        # add test
        new_record_id = 2
        new_data = {
            'key': None,
            'content': {
                'subject': 'New Subject',
                'body': 'New Body'
            }
        }
        result = mt.save_and_update(new_data)
        assert result == True
        added_record = MailTemplates.query.get(new_record_id)
        assert added_record.mail_subject == 'New Subject'
        assert added_record.mail_body == 'New Body'

        # failure test
        with patch(
            'invenio_mail.models.db.session.add',
            side_effect=Exception('DB Error Test')
        ):
            result = mt.save_and_update(new_data)
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


class TestMailType:
# .tox/c1/bin/pytest --cov=invenio_mail tests/test_models.py::TestMailType::test_enum -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-mail/.tox/c1/tmp
    def test_enum(self):
        assert MailType.RECIPIENT > MailType.CC
        assert MailType.CC > MailType.BCC
        assert MailType.RECIPIENT > MailType.BCC
        assert MailType.RECIPIENT.__lt__('recipient') == NotImplemented
        assert MailType.CC.__lt__(123) == NotImplemented


class TestMailTemplateUsers:
# .tox/c1/bin/pytest --cov=invenio_mail tests/test_models.py::TestMailTemplateUsers::test_save_and_update -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-mail/.tox/c1/tmp
    def test_save_and_update(self, mail_template_users_fixture):
        sut = MailTemplateUsers()

        # no key test
        new_data = {
            'key': None,
            'content': {
                'subject': 'New Subject',
                'body': 'New Body'
            }
        }
        assert sut.save_and_update(new_data) == False

        # delete all users test
        empty_data = {
            'key': 1,
            'content': {
                'recipients': '',
                'cc': '',
                'bcc': ''
            }
        }
        assert sut.save_and_update(empty_data) == True
        assert sut.query.count() == 0

        # add users test
        data = {
            'key': 1,
            'content': {
                'recipients': 'user1@example.com, user2@example.com',
                'cc': 'user1@example.com, user2@example.com',
                'bcc': 'user1@example.com, user2@example.com'
            }
        }
        assert sut.save_and_update(data) == True
        assert sut.query.count() == 6

        assert sut.save_and_update(data) == True
        assert sut.query.count() == 6

        # delete users failure test
        with patch(
            'invenio_mail.models.db.session.delete',
            side_effect=Exception('Delete Error Test')
        ):
            assert sut.save_and_update(empty_data) == False

        # clear data for next test
        sut.save_and_update(empty_data)

        # add users failure test
        with patch(
            'invenio_mail.models.db.session.add',
            side_effect=Exception('Add Error Test')
        ):
            assert sut.save_and_update(data) == False

        # commit failure test
        with patch(
            'invenio_mail.models.db.session.commit',
            side_effect=Exception('Commit Error Test')
        ):
            assert sut.save_and_update(data) == False

# .tox/c1/bin/pytest --cov=invenio_mail tests/test_models.py::TestMailTemplateUsers::test_delete_by_user_id -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-mail/.tox/c1/tmp
    def test_delete_by_user_id(self, mail_template_users_fixture):
        sut = MailTemplateUsers()

        # successfull delete test
        assert sut.query.filter_by(user_id=1).count() == 3
        sut.delete_by_user_id(1)
        assert sut.query.filter_by(user_id=1).count() == 0

        # failure test
        with patch(
            'invenio_mail.models.db.session.commit',
            side_effect=Exception('Commit Error Test')
        ):
            assert sut.delete_by_user_id(1) == False
