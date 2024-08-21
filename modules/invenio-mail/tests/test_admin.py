
import json
from smtplib import SMTPServerDisconnected

from flask import url_for

from mock import patch
from unittest.mock import MagicMock

from invenio_mail.admin import MailSettingView,_app, MailTemplatesView


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
    def test_send_statistic_mail(self,client,mail_configs,mocker):
        rf = {
            'recipients': 'recipient@example.com',
            'subject': 'Test Subject',
            'cc': 'cc@example.com',
            'bcc': 'bcc@example.com',
            'body': 'Test Body'
        }
        # success mail sending
        mock_send = mocker.patch('flask_mail._Mail.send')
        result = MailSettingView.send_statistic_mail(rf)
        assert result == True
        mock_send.assert_called()
        
        # failed mail sending
        mock_send = mocker.patch('flask_mail._Mail.send', side_effect=SMTPServerDisconnected())
        rf = {
            'recipients': 'recipient@example.com',
            'subject': 'Test Subject',
            'cc': 'cc@example.com',
            'bcc': 'bcc@example.com',
            'body': 'Test Body'
        }
        result = MailSettingView.send_statistic_mail(rf)
        assert result == False
        mock_send.assert_called()

class TestMailTemplatesView:
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
    def test_get_invalid_emails(self, app):
        # test email addresses list
        registered_emails = ['valid@example.com', 'valid2@example.com']
        unregistered_emails = ['invalid@example.com', 'invalid2@example.com']
        mixed_emails = ['valid@example.com', 'invalid@example.com']
        empty_emails = []
        # test objects
        mail_templates_view = MailTemplatesView()
        mock_user_instance = MagicMock()

        with app.app_context():

            # Test when both emails are valid
            with patch('invenio_mail.admin.User.query') as mock_query:
                mock_query.filter_by.return_value.first.side_effect = [mock_user_instance, mock_user_instance]
                result = mail_templates_view.get_invalid_emails(registered_emails)
                assert result == []
                mock_query.filter_by.assert_any_call(email=registered_emails[0], active=True)
                mock_query.filter_by.assert_any_call(email=registered_emails[1], active=True)
                assert mock_query.filter_by.call_count == 2

            # Test when both emails are invalid
            with patch('invenio_mail.admin.User.query') as mock_query:
                mock_query.filter_by.return_value.first.side_effect = [None, None]
                result = mail_templates_view.get_invalid_emails(unregistered_emails)
                assert result == unregistered_emails
                mock_query.filter_by.assert_any_call(email=unregistered_emails[0], active=True)
                mock_query.filter_by.assert_any_call(email=unregistered_emails[1], active=True)
                assert mock_query.filter_by.call_count == 2

            # Test when one email is valid and the other is invalid
            with patch('invenio_mail.admin.User.query') as mock_query:
                mock_query.filter_by.return_value.first.side_effect = [mock_user_instance, None]
                result = mail_templates_view.get_invalid_emails(mixed_emails)
                assert result == ['invalid@example.com']
                mock_query.filter_by.assert_any_call(email=mixed_emails[0], active=True)
                mock_query.filter_by.assert_any_call(email=mixed_emails[1], active=True)
                assert mock_query.filter_by.call_count == 2

            # Test when the email list is empty
            with patch('invenio_mail.admin.User.query') as mock_query:
                result = mail_templates_view.get_invalid_emails(empty_emails)
                assert result == []
