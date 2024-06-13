# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test admin interface."""

from flask import url_for
from flask_admin import Admin, menu
from invenio_db import db

from invenio_oaiserver.admin import set_adminview
from invenio_oaiserver.models import OAISet


def test_admin(app):
    """Test Flask-Admin interace."""
    admin = Admin(app, name="Test")

    assert "model" in set_adminview
    assert "modelview" in set_adminview

    # Register both models in admin
    model = set_adminview.pop("model")
    view = set_adminview.pop("modelview")
    admin.add_view(view(model, db.session, **set_adminview))

    # Check if generated admin menu contains the correct items
    menu_items = {str(item.name): item for item in admin.menu()}
    assert "OAI-PMH" in menu_items
    assert menu_items["OAI-PMH"].is_category()

    submenu_items = {
        str(item.name): item for item in menu_items["OAI-PMH"].get_children()
    }
    assert "Sets" in submenu_items
    assert isinstance(submenu_items["Sets"], menu.MenuView)

    # Create a test set.
    with app.app_context():
        test_set = OAISet(
            id=1,
            spec="test",
            name="test_name",
            description="some test description",
            search_pattern="title_statement.title:Test0",
            system_created=False,
        )
        db.session.add(test_set)
        db.session.commit()

    with app.test_request_context():
        index_view_url = url_for("oaiset.index_view")
        delete_view_url = url_for("oaiset.delete_view")
        detail_view_url = url_for("oaiset.details_view", id=1)

    with app.test_client() as client:
        # List index view and check record is there.
        res = client.get(index_view_url)
        assert res.status_code == 200

        # Deletion is forbiden.
        res = client.post(delete_view_url, data={"id": 1}, follow_redirects=True)
        assert res.status_code == 200

        # View the deleted record.
        res = client.get(detail_view_url)
        assert res.status_code == 200
        assert 1 == OAISet.query.count()
