
from smtplib import SMTPServerDisconnected

from flask import url_for

from unittest.mock import patch

from invenio_mail.admin import MailSettingView,_app

# .tox/c1/bin/pytest --cov=invenio_mail tests/test_admin.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-mail/.tox/c1/tmp

class TestMailSettingView:
# .tox/c1/bin/pytest --cov=invenio_mail tests/test_admin.py::TestMailSettingView::test_index -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-mail/.tox/c1/tmp
    def test_index(self,client,db,users,mail_configs):
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
    def test_send_test_mail(self,client, mail_configs):
        url = url_for("mail.send_test_mail")
        post_data = {
            'recipient': 'test@mail.nii.ac.jp',
            'subject': 'test mail',
            'body': 'test body'}
        # success mail sending
        mock_send = patch('flask_mail._Mail.send')
        res = client.post(url,data=post_data)
        assert res.status_code == 200
        mock_send.assert_called()
        assert 'recipient=test@mail.nii.ac.jp' in str(res.data)
        assert 'body=test body' in str(res.data)
        assert "Test mail sent." in str(res.data)

        # failed mail sending
        mock_send = patch('flask_mail._Mail.send', side_effect=SMTPServerDisconnected())
        res = client.post(url,data=post_data)
        assert res.status_code == 200
        mock_send.assert_called()
        assert 'recipient=test@mail.nii.ac.jp' in str(res.data)
        assert 'body=test body' in str(res.data)
        assert "Failed to send mail." in str(res.data)

# .tox/c1/bin/pytest --cov=invenio_mail tests/test_admin.py::TestMailSettingView::test_send_statistic_mail -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-mail/.tox/c1/tmp
    def test_send_statistic_mail(self,client,mail_configs):
        rf = {
            'recipient': 'test@mail.nii.ac.jp',
            'subject': 'test mail',
            'body': 'test body'
        }
        # success mail sending
        mock_send = patch('flask_mail._Mail.send')
        result = MailSettingView.send_statistic_mail(rf)
        assert result == True
        mock_send.assert_called()

        # failed mail sending
        mock_send = patch('flask_mail._Mail.send', side_effect=SMTPServerDisconnected())
        rf = {
            'recipient': 'test@mail.nii.ac.jp',
            'subject': 'test mail',
            'body': 'test body'
        }
        result = MailSettingView.send_statistic_mail(rf)
        assert result == False
        mock_send.assert_called()
