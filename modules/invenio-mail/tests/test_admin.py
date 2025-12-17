
import json
from smtplib import SMTPServerDisconnected

from flask import url_for, make_response
import json

from mock import patch
from unittest.mock import MagicMock

from invenio_mail.admin import MailSettingView,_app, MailTemplatesView
from invenio_mail.config import INVENIO_MAIL_VARIABLE_HELP
from invenio_mail.models import MailTemplates

# .tox/c1/bin/pytest --cov=invenio_mail tests/test_admin.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-mail/.tox/c1/tmp

class TestMailSettingView:
# .tox/c1/bin/pytest --cov=invenio_mail tests/test_admin.py::TestMailSettingView::test_index -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-mail/.tox/c1/tmp
    def test_index(self,client,db,users,mail_configs,mocker):
        url = url_for("mail.index")
        
        # get
        res = client.get(url)
        assert res.status_code == 200
        assert "server=localhost" in str(res.data)
        assert "port=25" in str(res.data)
        assert "use_tls=False" in str(res.data)
        
        # post
        ## mail_server, mail_port, mail_default_sender not in post_data
        data = {
            'mail_use_tls': 'on',
            'mail_use_ssl': 'on',
            'mail_username': 'nobody',
            'mail_password': 'password',
        }
        res = client.post(url,data=data)
        assert res.status_code == 200
        assert "server=localhost" in str(res.data)
        assert "port=25" in str(res.data)
        assert "use_tls=False" in str(res.data)
        assert "Mail server can&#39;t be empty." in str(res.data)
        assert "Mail port can&#39;t be empty." in str(res.data)
        assert "Mail default sender can&#39;t be empty." in str(res.data)

        ## mail_server, mail_port, mail_default_sender not in post_data, mail_use_tls,mail_use_ssl not in post_data
        data = {
            'mail_server': 'mail1.nii.ac.jp',
            'mail_port': 65535,
            'mail_username': 'nobody1',
            'mail_password': 'password1',
            'mail_default_sender': 'admin1'
        }
        res = client.post(url,data=data)
        assert res.status_code == 200
        assert "server=mail1.nii.ac.jp" in str(res.data)
        assert "port=65535" in str(res.data)
        assert "use_tls=False" in str(res.data)
        assert "use_ssl=False" in str(res.data)
        assert "username=nobody1" in str(res.data)
        assert "password=password1" in str(res.data)
        assert "default_sender=admin1" in str(res.data)
        assert "Mail settings have been updated." in str(res.data)

        ## exist all_data
        data = {
            'mail_server': 'mail2.nii.ac.jp',
            'mail_port': 65535,
            'mail_use_tls': 'on',
            'mail_use_ssl': 'on',
            'mail_username': 'nobody2',
            'mail_password': 'password2',
            'mail_default_sender': 'admin2'
        }
        res = client.post(url,data=data)
        assert "server=mail2.nii.ac.jp" in str(res.data)
        assert "port=65535" in str(res.data)
        assert "use_tls=True" in str(res.data)
        assert "use_ssl=True" in str(res.data)
        assert "username=nobody2" in str(res.data)
        assert "password=password2" in str(res.data)
        assert "default_sender=admin2" in str(res.data)
        assert "Mail settings have been updated." in str(res.data)

        # raise BaseException
        with patch("invenio_mail.admin._load_mail_cfg_from_db",side_effect=BaseException("test_error")):
            res = client.post(url,data=data)
            assert res.status_code == 400

# .tox/c1/bin/pytest --cov=invenio_mail tests/test_admin.py::TestMailSettingView::test_send_test_mail -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-mail/.tox/c1/tmp
    def test_send_test_mail(self,client, mail_configs,mocker):
        url = url_for("mail.send_test_mail")
        post_data = {
            'recipient': 'test@mail.nii.ac.jp',
            'subject': 'test mail',
            'body': 'test body'}
        # success mail sending
        mock_send = mocker.patch('flask_mail._Mail.send')
        res = client.post(url,data=post_data)
        assert res.status_code == 200
        mock_send.assert_called()
        assert 'recipient=test@mail.nii.ac.jp' in str(res.data)
        assert 'body=test body' in str(res.data)
        assert "Test mail sent." in str(res.data)
        
        # failed mail sending
        mock_send = mocker.patch('flask_mail._Mail.send', side_effect=SMTPServerDisconnected())
        res = client.post(url,data=post_data)
        assert res.status_code == 200
        mock_send.assert_called()
        assert 'recipient=test@mail.nii.ac.jp' in str(res.data)
        assert 'body=test body' in str(res.data)
        assert "Failed to send mail." in str(res.data)

# .tox/c1/bin/pytest --cov=invenio_mail tests/test_admin.py::TestMailSettingView::test_send_statistic_mail -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-mail/.tox/c1/tmp
    def test_send_statistic_mail(self,app,client,mail_configs,mocker,caplog):
        rf = {
            'subject': 'Test Subject',
            'body': 'Test Body',
            'recipients': ['recipient1@example.org', 'recipient2@example.org'],
            'cc': ['cc1@example.org', 'cc2@example.org'],
            'bcc': ['bcc1@example.org', 'bcc2@example.org']
        }
        # Success tests
        mock_send = mocker.patch('flask_mail._Mail.send')
        result = MailSettingView.send_statistic_mail(rf)
        assert result is True
        mock_send.assert_called_once()
        sent_msg = mock_send.call_args[0][0]
        assert sent_msg.subject    == rf['subject']
        assert sent_msg.body       == rf['body']
        assert sent_msg.recipients == rf['recipients']
        assert sent_msg.cc         == rf['cc']
        assert sent_msg.bcc        == rf['bcc']
        mock_send.reset_mock()

        # Failure tests
        with caplog.at_level('ERROR'):
            result = MailSettingView.send_statistic_mail({})
            mock_send.assert_not_called()
            assert result is False
            assert 'Cannot send email' in caplog.text
        with caplog.at_level('ERROR'):
            mock_send.side_effect = SMTPServerDisconnected()
            result = MailSettingView.send_statistic_mail(rf)
            mock_send.assert_called()
            assert result is False
            assert 'Cannot send email' in caplog.text


class TestMailTemplatesView:
    # .tox/c1/bin/pytest --cov=invenio_mail tests/test_admin.py::TestMailTemplatesView::test_index -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-mail/.tox/c1/tmp
    def test_index(self, client, mail_templates, mocker):
        url = url_for("mailtemplates.index")
        mock_render = mocker.patch('invenio_mail.admin.MailTemplatesView.render', return_value=make_response())
        client.get(url)
        mock_render.assert_called_with(
            'invenio_mail/mail_templates.html',
            data=json.dumps(
                {
                    "mail_templates": MailTemplates.get_templates(),
                    "additional_display": False
                }
            )
        )

    # .tox/c1/bin/pytest --cov=invenio_mail tests/test_admin.py::TestMailTemplatesView::test_help -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-mail/.tox/c1/tmp
    def test_help(self, client, mocker):
        url = url_for("mailtemplates.help")
        mock_render = mocker.patch('invenio_mail.admin.MailTemplatesView.render', return_value=make_response())
        client.get(url)
        mock_render.assert_called_with(
            'invenio_mail/mail_help.html',
            data=INVENIO_MAIL_VARIABLE_HELP
        )

    # .tox/c1/bin/pytest --cov=invenio_mail tests/test_admin.py::TestMailTemplatesView::test_save_mail_template -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-mail/.tox/c1/tmp
    def test_save_mail_template(self, client, mail_templates, mocker):
        url = url_for("mailtemplates.save_mail_template")
        post_data = {
            'mail_templates': [
                {
                    'key': 1,
                    'content': {
                        'subject': 'test subject1',
                        'body': 'test body1'
                    },
                },
                {
                    'key': '',
                    'content': {
                        'subject': 'test subject2',
                        'body': 'test body2'
                    },
                }
            ]
        }
        # success save mail template
        with patch('invenio_mail.admin.MailTemplates.save_and_update') as mock_save:
            mock_save.return_value = True
            res = client.post(url, data=json.dumps(post_data), content_type='application/json')
            assert res.status_code == 200
            assert True == json.loads(res.data)['status']
            assert 'Mail template was successfully updated.' == json.loads(res.data)['msg']
            assert MailTemplates.get_templates() == json.loads(res.data)['data']
            mock_save.assert_called()

        # failed to save mail template
        with patch('invenio_mail.admin.MailTemplates.save_and_update') as mock_save:
            mock_save.return_value = False
            res = client.post(url, data=json.dumps(post_data), content_type='application/json')
            assert res.status_code == 200
            assert False == json.loads(res.data)['status']
            assert 'Mail template update failed.' == json.loads(res.data)['msg']
            assert MailTemplates.get_templates() == json.loads(res.data)['data']
            mock_save.assert_called()

    # .tox/c1/bin/pytest --cov=invenio_mail tests/test_admin.py::TestMailTemplatesView::test_delete_mail_template -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-mail/.tox/c1/tmp
    def test_delete_mail_template(self, client, mail_templates, mocker):
        url = url_for("mailtemplates.delete_mail_template")
        post_data = {
            'template_id': 1
        }
        # success delete mail template
        with patch('invenio_mail.admin.MailTemplates.delete_by_id') as mock_delete:
            mock_delete.return_value = True
            res = client.delete(url, data=json.dumps(post_data), content_type='application/json')
            assert res.status_code == 200
            assert True == json.loads(res.data)['status']
            assert 'Mail template was successfully deleted.' == json.loads(res.data)['msg']
            assert MailTemplates.get_templates() == json.loads(res.data)['data']
            mock_delete.assert_called()

        # failed to delete mail template
        with patch('invenio_mail.admin.MailTemplates.delete_by_id') as mock_delete:
            mock_delete.return_value = False
            res = client.delete(url, data=json.dumps(post_data), content_type='application/json')
            assert res.status_code == 200
            assert False == json.loads(res.data)['status']
            assert 'Mail template delete failed.' == json.loads(res.data)['msg']
            assert MailTemplates.get_templates() == json.loads(res.data)['data']
            mock_delete.assert_called()


# .tox/c1/bin/pytest --cov=invenio_mail tests/test_admin.py::TestMailTemplatesView::test_save_mail_template -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-mail/.tox/c1/tmp
    @patch('invenio_mail.admin.MailTemplatesView.get_invalid_emails')
    @patch('invenio_mail.admin.MailTemplates.save_and_update')
    @patch('invenio_mail.admin.MailTemplateUsers.save_and_update')
    @patch('invenio_mail.admin.MailTemplates.get_templates')
    def test_save_mail_template(
        self,
        mock_get_templates,
        mock_save_and_update_users,
        mock_save_and_update,
        mock_get_invalid_emails,
        client
    ):
        # when all emails are valid
        mock_get_templates.return_value = []
        mock_save_and_update_users.return_value = True
        mock_save_and_update.return_value = True
        mock_get_invalid_emails.return_value = []
        valid_tpl = [{
            'key': 'mail_templates',
            'content': {
                'subject': 'valid_subject',
                'body': 'valid_body',
                'recipients': 'valid_mail',
                'cc': 'valid_mail',
                'bcc': 'valid_mail'
            }
        }]
        url = url_for("mailtemplates.save_mail_template")
        post_data = {'mail_templates': valid_tpl}
        response = client.post(
            url,
            data=json.dumps(post_data),
            content_type='application/json'
        )
        assert response.status_code == 200
        assert 'Mail template was successfully updated.' in str(response.data)

        # when recipients email is invalid
        mock_get_invalid_emails.return_value = ['invalid_mail']
        invalid_re_tpl = [{
            'key': 'mail_templates',
            'content': {
                'subject': 'valid_subject',
                'body': 'valid_body',
                'recipients': 'invalid_mail',
                'cc': 'valid_mail',
                'bcc': 'valid_mail'
            }
        }]
        post_data = {'mail_templates': invalid_re_tpl}
        response = client.post(
            url,
            data=json.dumps(post_data),
            content_type='application/json'
        )
        assert response.status_code == 200
        assert ('Invalid email addresses (invalid_mail) detected.'
                in str(response.data))

        # when cc email is invalid
        invalid_cc_tpl = [{
            'key': 'mail_templates',
            'content': {
                'subject': 'valid_subject',
                'body': 'valid_body',
                'recipients': 'valid_mail',
                'cc': 'invalid_mail',
                'bcc': 'valid_mail'
            }
        }]
        post_data = {'mail_templates': invalid_cc_tpl}
        response = client.post(
            url,
            data=json.dumps(post_data),
            content_type='application/json'
        )
        assert response.status_code == 200
        assert ('Invalid email addresses (invalid_mail) detected.'
                in str(response.data))
        
        # when bcc email is invalid
        invalid_bcc_tpl = [{
            'key': 'mail_templates',
            'content': {
                'subject': 'valid_subject',
                'body': 'valid_body',
                'recipients': 'valid_mail',
                'cc': 'valid_mail',
                'bcc': 'invalid_mail'
            }
        }]
        post_data = {'mail_templates': invalid_bcc_tpl}
        response = client.post(
            url,
            data=json.dumps(post_data),
            content_type='application/json'
        )
        assert response.status_code == 200
        assert ('Invalid email addresses (invalid_mail) detected.'
                in str(response.data))
        
        # when mail template update failed
        mock_save_and_update.return_value = False
        mock_get_invalid_emails.return_value = []
        post_data = {'mail_templates': valid_tpl}
        response = client.post(
            url,
            data=json.dumps(post_data),
            content_type='application/json'
        )
        assert response.status_code == 200
        assert 'Mail template update failed.' in str(response.data)


# .tox/c1/bin/pytest --cov=invenio_mail tests/test_admin.py::TestMailTemplatesView::test_get_invalid_emails -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-mail/.tox/c1/tmp
    @patch('invenio_accounts.models.User.query')
    def test_get_invalid_emails(self, mock_query, client):
        # test email addresses list
        registered_emails = ['valid@example.com', 'valid2@example.com']
        unregistered_emails = ['invalid@example.com', 'invalid2@example.com']
        mixed_emails = ['valid@example.com', 'invalid@example.com']
        empty_emails = []
        # test objects
        mail_templates_view = MailTemplatesView()
        mock_user_instance = MagicMock()

        # Test when both emails are valid
        mock_query.filter_by.return_value.first.side_effect = [
            mock_user_instance, mock_user_instance
        ]
        result = mail_templates_view.get_invalid_emails(registered_emails)
        assert result == []
        mock_query.filter_by.assert_any_call(
            email=registered_emails[0],
            active=True
        )
        mock_query.filter_by.assert_any_call(
            email=registered_emails[1],
            active=True
        )
        assert mock_query.filter_by.call_count == 2

        # Test when both emails are invalid
        mock_query.filter_by.return_value.first.side_effect = [None, None]
        result = mail_templates_view.get_invalid_emails(
            unregistered_emails
        )
        assert result == unregistered_emails
        mock_query.filter_by.assert_any_call(
            email=unregistered_emails[0],
            active=True
        )
        mock_query.filter_by.assert_any_call(
            email=unregistered_emails[1],
            active=True
        )
        assert mock_query.filter_by.call_count == 4

        # Test when one email is valid and the other is invalid
        mock_query.filter_by.return_value.first.side_effect = [
            mock_user_instance,
            None
        ]
        result = mail_templates_view.get_invalid_emails(mixed_emails)
        assert result == ['invalid@example.com']
        mock_query.filter_by.assert_any_call(
            email=mixed_emails[0],
            active=True
        )
        mock_query.filter_by.assert_any_call(
            email=mixed_emails[1],
            active=True
        )
        assert mock_query.filter_by.call_count == 6

        # Test when the email list is empty
        result = mail_templates_view.get_invalid_emails(empty_emails)
        assert result == []
