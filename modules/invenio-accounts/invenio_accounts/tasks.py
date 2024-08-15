# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Background tasks for accounts."""

from datetime import datetime

from celery import shared_task
from flask import current_app
from flask_mail import Message
from invenio_db import db
from sqlalchemy import func, or_

from .models import Domain, LoginInformation, SessionActivity, User
from .sessions import delete_session


@shared_task
def send_security_email(data):
    """Celery task to send security email.

    :param data: Contains the email data.
    """
    msg = Message()
    msg.__dict__.update(data)
    current_app.extensions["mail"].send(msg)


@shared_task
def clean_session_table():
    """Automatically clean session table.

    To enable a periodically clean of the session table, you should configure
    the task as a celery periodic task.

    .. code-block:: python

        from datetime import timedelta
        CELERYBEAT_SCHEDULE = {
            'session_cleaner': {
                'task': 'invenio_accounts.tasks.clean_session_table',
                'schedule': timedelta(days=1),
            },
        }

    See `Invenio-Celery <https://invenio-celery.readthedocs.io/>`_
    documentation for further details.
    """
    sessions = SessionActivity.query_by_expired().all()
    for session in sessions:
        delete_session(sid_s=session.sid_s)
    db.session.commit()


@shared_task
def delete_ips():
    """Automatically remove login_info.last_login_ip older than 30 days."""
    expiration_date = (
        datetime.utcnow() - current_app.config["ACCOUNTS_RETENTION_PERIOD"]
    )

    LoginInformation.query.filter(
        LoginInformation.last_login_ip.isnot(None),
        LoginInformation.last_login_at < expiration_date,
    ).update({LoginInformation.last_login_ip: None})

    LoginInformation.query.filter(
        LoginInformation.current_login_ip.isnot(None),
        LoginInformation.current_login_at < expiration_date,
    ).update({LoginInformation.current_login_ip: None})
    db.session.commit()


@shared_task
def update_domain_status():
    """Update domain statistics."""
    # This subquery calculate the number of users per domain from the users
    # table.
    subquery = (
        db.session.query(
            User.domain,
            func.count(User.id).label("num_users"),
            func.count(User.active).filter(User.active == True).label("num_active"),
            func.count(User.active).filter(User.active == False).label("num_inactive"),
            func.count(User.confirmed_at).label("num_confirmed"),
            func.count(User.verified_at).label("num_verified"),
            func.count(User.blocked_at).label("num_blocked"),
        )
        .group_by(User.domain)
        .subquery("n")
    )

    # Using above subquery, we find the domains that has changed.
    stmt = (
        db.session.query(
            Domain.domain,
            subquery.c.num_users,
            subquery.c.num_active,
            subquery.c.num_inactive,
            subquery.c.num_confirmed,
            subquery.c.num_verified,
            subquery.c.num_blocked,
        )
        .join(subquery, Domain.domain == subquery.c.domain)
        .filter(
            or_(
                Domain.num_users != subquery.c.num_users,
                Domain.num_active != subquery.c.num_active,
                Domain.num_inactive != subquery.c.num_inactive,
                Domain.num_confirmed != subquery.c.num_confirmed,
                Domain.num_verified != subquery.c.num_verified,
                Domain.num_blocked != subquery.c.num_blocked,
            )
        )
    )

    # If statistics are updated regularly, the number of updates is relatively
    # low and hence fit in memory. We read all data first, to avoid starting
    # to modify the same table we're reading from.
    domain_updates = list(stmt.all())

    # Commit batches of 500 updates
    batch_size = 500
    now = datetime.utcnow()

    # Process updates in batches
    for i in range(0, len(domain_updates), batch_size):
        with db.session.begin_nested():  # Use nested transactions for safety
            for (
                domain,
                users,
                active,
                inactive,
                confirmed,
                verified,
                blocked,
            ) in domain_updates[i : i + batch_size]:
                db.session.query(Domain).filter(Domain.domain == domain).update(
                    {
                        "num_users": users,
                        "num_active": active,
                        "num_inactive": inactive,
                        "num_confirmed": confirmed,
                        "num_verified": verified,
                        "num_blocked": blocked,
                        "updated": now,
                    }
                )
        db.session.commit()  # Commit after each batch
