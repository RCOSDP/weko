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
from weko_index_tree.api import Indexes
from weko_index_tree.models import Index

from invenio_oaiharvester.admin import harvest_admin_view
from invenio_oaiharvester.models import HarvestSettings


def test_admin(app, db):
    """Test Flask-Admin interace."""
    admin = Admin(app, name='Test')

    assert 'model' in harvest_admin_view
    assert 'modelview' in harvest_admin_view

    # Register both models in admin
    model = harvest_admin_view.pop('model')
    view = harvest_admin_view.pop('modelview')
    admin.add_view(view(model, db.session, **harvest_admin_view))

    # Check if generated admin menu contains the correct items
    menu_items = {str(item.name): item for item in admin.menu()}
    assert 'OAI-PMH' in menu_items
    assert menu_items['OAI-PMH'].is_category()

    submenu_items = {
        str(item.name): item for item in menu_items['OAI-PMH'].get_children()
    }
    assert 'Harvesting' in submenu_items
    assert isinstance(submenu_items['Harvesting'], menu.MenuView)

    # Create a test set.
    with app.app_context():
        index = Index()
        db.session.add(index)
        db.session.commit()
        test_set = HarvestSettings(
            id=1,
            repository_name='test_name',
            base_url='test_url',
            metadata_prefix='test_metadata',
            index_id=index.id,
            update_style='0',
            auto_distribution='0')
        db.session.add(test_set)
        db.session.commit()

    with app.test_request_context():
        index_view_url = url_for('harvestsettings.index_view')
        delete_view_url = url_for('harvestsettings.delete_view')
        edit_view_url = url_for('harvestsettings.edit_view', id=1)
        detail_view_url = url_for('harvestsettings.details_view', id=1)

        run_api_url = url_for('harvestsettings.run', id=1)
        pause_api_url = url_for('harvestsettings.pause', id=1)
        clear_api_url = url_for('harvestsettings.clear', id=1)
        get_logs_api_url = url_for('harvestsettings.get_log_detail', id=1)
        get_log_detail_api_url = url_for('harvestsettings.get_log_detail',
                                         id=1)

    with app.test_client() as client:
        # List index view and check record is there.
        res = client.get(index_view_url)
        assert res.status_code == 200

        # List index view and check record is there.
        res = client.get(edit_view_url)
        assert res.status_code == 200

        # API
        # res = client.get(run_api_url)
        # assert res.status_code == 200

        # res = client.get(pause_api_url)
        # assert res.status_code == 200

        # res = client.get(clear_api_url)
        # assert res.status_code == 200

        # res = client.get(get_logs_api_url)
        # assert res.status_code == 200

        # res = client.get(get_log_detail_api_url)
        # assert res.status_code == 200

        # Deletion is forbiden.
        res = client.post(
            delete_view_url, data={'id': 1}, follow_redirects=True)
        assert res.status_code == 200

        # View the deleted record.
        res = client.get(detail_view_url)
        assert res.status_code == 302
        assert 0 == HarvestSettings.query.count()
