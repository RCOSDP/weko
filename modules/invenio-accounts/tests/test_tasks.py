# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.


"""Module tests."""

from datetime import datetime, timedelta
from time import sleep
from mock import patch

from flask import url_for
from flask_login import login_required
from flask_mail import Message
from flask_security import url_for_security

from invenio_accounts.models import SessionActivity, User
from invenio_accounts.tasks import clean_session_table, delete_ips, send_security_email
from invenio_accounts.testutils import create_test_user


def test_send_message_outbox(task_app):
    """Test sending a security message using Task module."""
    with task_app.app_context():
        with task_app.extensions["mail"].record_messages() as outbox:
            msg = Message(
                "Test1", sender="test1@test1.test1", recipients=["test1@test1.test1"]
            )

            send_security_email(msg.__dict__)

            assert len(outbox) == 1
            sent_msg = outbox[0]
            assert sent_msg.subject == "Test1"
            assert sent_msg.sender == "test1@test1.test1"
            assert sent_msg.recipients == ["test1@test1.test1"]


def test_send_message_through_security(task_app):
    """Test sending a message through security extension."""
    with task_app.app_context():
        with task_app.extensions["mail"].record_messages() as outbox:
            msg = Message(
                "Test1", sender="test1@test1.test1", recipients=["test1@test1.test1"]
            )

            task_app.extensions["security"]._send_mail_task(msg)

            assert len(outbox) == 1
            sent_msg = outbox[0]
            assert sent_msg.subject == "Test1"
            assert sent_msg.sender == "test1@test1.test1"
            assert sent_msg.recipients == ["test1@test1.test1"]


def test_clean_session_table(task_app):
    """Test clean session table."""
    # set session lifetime
    task_app.permanent_session_lifetime = timedelta(seconds=20)

    # protected page
    @task_app.route("/test", methods=["GET"])
    @login_required
    def test():
        return "test"

    with task_app.test_request_context():
        user1 = create_test_user(email="user1@invenio-software.org")
        user2 = create_test_user(email="user2@invenio-software.org")

        with task_app.test_client() as client:
            client.post(
                url_for_security("login"),
                data=dict(
                    email=user1.email,
                    password=user1.password_plaintext,
                ),
            )
        assert len(SessionActivity.query.all()) == 1
        sleep(15)

        with task_app.test_client() as client:
            client.post(
                url_for_security("login"),
                data=dict(
                    email=user2.email,
                    password=user2.password_plaintext,
                ),
            )
            assert len(SessionActivity.query.all()) == 2
            sleep(10)

            clean_session_table.s().apply()
            assert len(SessionActivity.query.all()) == 1

            protected_url = url_for("test")

            res = client.get(protected_url)
            assert res.status_code == 200

            sleep(15)
            clean_session_table.s().apply()
            assert len(SessionActivity.query.all()) == 0

            res = client.get(protected_url)
            # check if the user is really logout
            assert res.status_code == 302

        with task_app.test_client() as client:
            client.post(url_for_security('login'), data=dict(
                email=user2.email,
                password=user2.password_plaintext,
            ))
            assert len(SessionActivity.query.all()) == 1
            sleep(10)

            with patch('invenio_accounts.tasks.db.session.commit', side_effect=Exception('')):
                clean_session_table.s().apply()
                assert len(SessionActivity.query.all()) == 1

def test_delete_ips(task_app):
    """Test if ips are deleted after 30 days."""
    last_login_at1 = (
        datetime.utcnow()
        - task_app.config["ACCOUNTS_RETENTION_PERIOD"]
        - timedelta(days=1)
    )
    last_login_at2 = datetime.utcnow()

    with task_app.app_context():
        user1 = create_test_user(
            email="user1@invenio-software.org",
            last_login_ip="127.0.0.1",
            current_login_ip="127.0.0.1",
            last_login_at=last_login_at1,
            current_login_at=last_login_at1,
        )

        user2 = create_test_user(
            email="user2@invenio-software.org",
            last_login_ip="127.0.0.1",
            current_login_ip="127.0.0.1",
            last_login_at=last_login_at2,
            current_login_at=last_login_at2,
        )

        user3 = create_test_user(
            email="user3@invenio-software.org",
            last_login_ip="127.0.0.1",
            current_login_ip="127.0.0.1",
            last_login_at=last_login_at1,
            current_login_at=last_login_at2,
        )

        delete_ips()

        user = User.query.filter(User.id == user1.id).one()
        assert user.last_login_ip is None
        assert user.current_login_ip is None

        user = User.query.filter(User.id == user2.id).one()
        assert user.last_login_ip is not None
        assert user.current_login_ip is not None

        user = User.query.filter(User.id == user3.id).one()
        assert user.last_login_ip is None
        assert user.current_login_ip is not None
