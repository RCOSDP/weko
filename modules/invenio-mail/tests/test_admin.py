
from smtplib import SMTPServerDisconnected

import flask
import flask_mail
import pytest
from flask_admin import Admin
from invenio_db import InvenioDB, db
from pytest_mock import mocker

from invenio_mail import InvenioMail


def test_mail_index_get(email_admin_app):
    with email_admin_app.test_request_context():
        client = email_admin_app.test_client()
        res = client.get(flask.url_for('mail.index'))
    assert res.status_code == 200
    assert 'server=localhost' in str(res.data)
    assert 'port=25' in str(res.data)
    assert 'use_tls=False' in str(res.data)


def test_mail_index_post(email_admin_app):
    post_data = {
        'mail_server': 'mail.nii.ac.jp',
        'mail_port': 65535,
        'mail_use_tls': 'on',
        'mail_use_ssl': 'on',
        'mail_username': 'nobody',
        'mail_password': 'password',
        'mail_default_sender': 'admin'}
    with email_admin_app.test_request_context():
        client = email_admin_app.test_client()
        res = client.post(flask.url_for('mail.index'), data=post_data)
    assert res.status_code == 200
    assert 'server=mail.nii.ac.jp' in str(res.data)
    assert 'port=65535' in str(res.data)
    assert 'use_tls=True' in str(res.data)
    assert 'use_ssl=True' in str(res.data)
    assert 'username=nobody' in str(res.data)
    assert 'password=password' in str(res.data)
    assert 'default_sender=admin\\n' in str(res.data)
    assert 'Mail settings have been updated.' in str(res.data)


def test_mail_index_post_failed(email_admin_app, mocker):
    mocker.patch(
        'invenio_mail.admin._save_mail_cfg_to_db',
        side_effect=Exception())
    post_data = {
        'mail_server': 'mail.nii.ac.jp',
        'mail_port': 65535,
        'mail_use_tls': 'on',
        'mail_use_ssl': 'on',
        'mail_username': 'nobody',
        'mail_password': 'password',
        'mail_default_sender': 'admin'}
    with email_admin_app.test_request_context():
        client = email_admin_app.test_client()
        res = client.post(flask.url_for('mail.index'), data=post_data)
    assert res.status_code == 400


def test_send_mail(email_admin_app, mocker):
    mocker.patch('flask_mail._Mail.send')
    post_data = {
        'recipient': 'test@mail.nii.ac.jp',
        'subject': 'test mail',
        'body': 'test body'}
    with email_admin_app.test_request_context():
        client = email_admin_app.test_client()
        res = client.post(flask.url_for('mail.send_test_mail'), data=post_data)
    assert flask_mail._Mail.send.called
    assert res.status_code == 200
    assert 'recipient=test@mail.nii.ac.jp' in str(res.data)
    assert 'body=test body' in str(res.data)


def test_send_mail_failed(email_admin_app, mocker):
    mocker.patch('flask_mail._Mail.send', side_effect=SMTPServerDisconnected())
    post_data = {
        'recipient': 'test@mail.nii.ac.jp',
        'subject': 'test mail',
        'body': 'test body'}
    with email_admin_app.test_request_context():
        client = email_admin_app.test_client()
        res = client.post(flask.url_for('mail.send_test_mail'), data=post_data)
    assert flask_mail._Mail.send.called
    assert res.status_code == 200
    assert 'Failed to send mail.' in str(res.data)
