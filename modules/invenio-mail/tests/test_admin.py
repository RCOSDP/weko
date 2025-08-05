
from smtplib import SMTPServerDisconnected

from flask import url_for, make_response
import json

from mock import patch

from invenio_mail.admin import MailSettingView,_app
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
    def test_send_statistic_mail(self,client,mail_configs,mocker):
        rf = {
            'recipient': 'test@mail.nii.ac.jp',
            'subject': 'test mail',
            'body': 'test body'
        }
        # success mail sending
        mock_send = mocker.patch('flask_mail._Mail.send')
        result = MailSettingView.send_statistic_mail(rf)
        assert result == True
        mock_send.assert_called()
        
        # failed mail sending
        mock_send = mocker.patch('flask_mail._Mail.send', side_effect=SMTPServerDisconnected())
        rf = {
            'recipient': 'test@mail.nii.ac.jp',
            'subject': 'test mail',
            'body': 'test body'
        }
        result = MailSettingView.send_statistic_mail(rf)
        assert result == False
        mock_send.assert_called()

class TestMailTemplatesView:
    # .tox/c1/bin/pytest --cov=invenio_mail tests/test_admin.py::TestMailTemplatesView::test_index -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-mail/.tox/c1/tmp
    def test_index(self, client, mail_templates, mocker):
        url = url_for("mailtemplates.index")
        mock_render = mocker.patch('invenio_mail.admin.MailTemplatesView.render', return_value=make_response())
        client.get(url)
        mock_render.assert_called_with(
            'invenio_mail/mail_templates.html',
            data=json.dumps({"mail_templates": MailTemplates.get_templates()})
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
