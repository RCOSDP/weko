# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 National Institute of Informatics.
#
# WEKO-Notifications is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Pytest configuration.

See https://pytest-invenio.readthedocs.io/ for documentation on which test
fixtures are available.
"""

from __future__ import absolute_import, print_function

import shutil
import tempfile

import pytest
from flask import Flask
from flask_babelex import Babel

from weko_notifications import WekoNotifications
from weko_notifications.views import blueprint


@pytest.fixture(scope='module')
def celery_config():
    """Override pytest-invenio fixture.

    TODO: Remove this fixture if you add Celery support.
    """
    return {}


@pytest.fixture(scope='module')
def create_app(instance_path):
    """Application factory fixture."""
    def factory(**config):
        app = Flask('testapp', instance_path=instance_path)
        app.config.update(**config)
        Babel(app)
        WekoNotifications(app)
        app.register_blueprint(blueprint)
        return app
    return factory


@pytest.fixture()
def json_notifications():
    """Return a notifications instance."""

    after_approval = {
        "id": "urn:uuid:d90c0ed0-b2bc-44aa-bc80-642e7426d90d",
        "@context": [
            "https://www.w3.org/ns/activitystreams",
            "https://coar-notify.net"
        ],
        "type": [
            "Announce",
            "coar-notify:EndorsementAction"
        ],
        "origin": {
            "id": "https://example.repo.nii.ac.jp/",
            "inbox": "https://example.repo.nii.ac.jp/inbox",
            "type": "Service"
        },
        "target": {
            "id": "https://example.repo.nii.ac.jp/user/3",
            "inbox": "https://example.repo.nii.ac.jp/inbox",
            "type": "Person"
        },
        "object": {
            "id": "https://example.repo.nii.ac.jp/records/2000001",
            "ietf:cite-as": "https://example.repo.nii.ac.jp/records/2000001",
            "type": [
            "Page",
            "sorg:WebPage"
            ]
        },
        "actor": {
            "id": "https://example.repo.nii.ac.jp/user/1",
            "type": "Person",
            "name": "ADMIN"
        },
        "context": {
            "id": "https://example.repo.nii.ac.jp/workflow/activity/detail/A-20250306-00001",
            "ietf:cite-as": "https://doi.org/10.1101/2000001",
            "type": "sorg:ScholarlyArticle"
        },
        "inReplyTo": "urn:uuid:7c74da60-3455-485a-9068-83ece6920529"
    }

    after_registration = {
        "id": "urn:uuid:d90c0ed0-b2bc-44aa-bc80-642e7426d90d",
        "@context": [
            "https://www.w3.org/ns/activitystreams",
            "https://coar-notify.net"
        ],
        "type": [
            "Announce",
            "coar-notify:IngestAction"
        ],
        "origin": {
            "id": "https://example.repo.nii.ac.jp/",
            "inbox": "https://example.repo.nii.ac.jp/inbox",
            "type": "Service"
        },
        "target": {
            "id": "https://example.repo.nii.ac.jp/user/3",
            "inbox": "https://example.repo.nii.ac.jp/inbox",
            "type": "Person"
        },
        "object": {
            "id": "https://example.repo.nii.ac.jp/records/2000001",
            "ietf:cite-as": "https://example.repo.nii.ac.jp/records/2000001",
            "type": [
            "Page",
            "sorg:WebPage"
            ]
        }
    }

    after_registration_obo = {
        "id": "urn:uuid:d90c0ed0-b2bc-44aa-bc80-642e7426d90d",
        "@context": [
            "https://www.w3.org/ns/activitystreams",
            "https://coar-notify.net"
        ],
        "type": [
            "Announce",
            "coar-notify:IngestAction"
        ],
        "origin": {
            "id": "https://example.repo.nii.ac.jp/",
            "inbox": "https://example.repo.nii.ac.jp/inbox",
            "type": "Service"
        },
        "target": {
            "id": "https://example.repo.nii.ac.jp/user/3",
            "inbox": "https://example.repo.nii.ac.jp/inbox",
            "type": "Person"
        },
        "object": {
            "id": "https://example.repo.nii.ac.jp/records/2000001",
            "ietf:cite-as": "https://example.repo.nii.ac.jp/records/2000001",
            "type": [
            "Page",
            "sorg:WebPage"
            ]
        },
        "actor": {
            "id": "https://example.repo.nii.ac.jp/user/4",
            "type": "Person",
            "name": "ADMIN"
        }
    }

    return {
        "after_approval": after_approval,
        "after_registration": after_registration,
        "after_registration_obo": after_registration_obo
    }
