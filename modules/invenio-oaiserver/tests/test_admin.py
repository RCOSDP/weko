# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test admin interface."""

from __future__ import absolute_import, print_function
import copy
from flask import url_for
from flask_admin import Admin, menu
from mock import patch

from invenio_oaiserver.admin import set_adminview, set_OAIPMHview
from invenio_oaiserver.models import OAISet, Identify

# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_admin.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp

# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_admin.py::test_admin -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
def test_admin(es_app, db,without_oaiset_signals):
    """Test Flask-Admin interace."""
    admin = Admin(es_app, name='Test')

    assert 'model' in set_adminview
    assert 'modelview' in set_adminview

    # Register both models in admin
    copy_modelview = copy.deepcopy(set_adminview)
    model = copy_modelview.pop('model')
    view = copy_modelview.pop('modelview')
    admin.add_view(view(model, db.session, **copy_modelview))

    # Check if generated admin menu contains the correct items
    menu_items = {str(item.name): item for item in admin.menu()}
    assert 'OAI-PMH' in menu_items
    assert menu_items['OAI-PMH'].is_category()

    submenu_items = {
        str(item.name): item for item in menu_items['OAI-PMH'].get_children()
    }
    assert 'Sets' in submenu_items
    assert isinstance(submenu_items['Sets'], menu.MenuView)

    # Create a test set.
    with es_app.app_context():
        test_set = OAISet(id=1,
                          spec='test',
                          name='test_name',
                          description='some test description',
                          search_pattern='test search')
        db.session.add(test_set)
        db.session.commit()

    with es_app.test_request_context():
        index_view_url = url_for('oaiset.index_view')
        delete_view_url = url_for('oaiset.delete_view')
        detail_view_url = url_for('oaiset.details_view', id=1)

    with es_app.test_client() as client:
        # List index view and check record is there.
        res = client.get(index_view_url)
        assert res.status_code == 200

        # Deletion is forbiden.
        res = client.post(
            delete_view_url, data={'id': 1}, follow_redirects=True)
        assert res.status_code == 200

        # View the deleted record.
        res = client.get(detail_view_url)
        assert res.status_code == 200
        assert 1 == OAISet.query.count()

# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_admin.py::test_OAISetModelView -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
def test_OAISetModelView(es_app, db,without_oaiset_signals):
    
    admin = Admin(es_app, name='Test')
    
    copy_modelview = copy.deepcopy(set_adminview)
    model = copy_modelview.pop('model')
    view = copy_modelview.pop('modelview')
    admin.add_view(view(model, db.session, **copy_modelview))
    
    test_set = OAISet(id=1,
                          spec='test',
                          name='test_name',
                          description='some test description',
                          search_pattern='test search')
    db.session.add(test_set)
    db.session.commit()
    url = url_for("oaiset.edit_view",id=1)
    data = {
        "name":"new_test_name",
        "description":"sone new test description",
        "search_pattern":"new test search"
    }
    with es_app.test_client() as client:
        res = client.post(url,data=data)
        result = OAISet.query.filter_by(id=1).one()
        assert result.name == "new_test_name"

# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_admin.py::test_IdentifyModelView -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
def test_IdentifyModelView(app, db,without_oaiset_signals):
    admin = Admin(app, name='Test')
    model = set_OAIPMHview.pop('model')
    view = set_OAIPMHview.pop('modelview')
    admin.add_view(view(model, db.session, **set_OAIPMHview))
    
    # first create
    url = url_for("identify.create_view")
    data = {
        "outPutSetting":"y",
        "emails":"test@test.org",
        "repositoryName":"test_repository"
    }
    with app.test_client() as client:
        res = client.post(url, data=data)
        result = Identify.query.filter_by(id=1).one_or_none()
        assert result

    # second create
    data = {
        "outPutSetting":"y",
        "emails":"test@test.org",
        "repositoryName":"test_repository"
    }
    with app.test_client() as client:
        res = client.post(url, data=data)
        result = Identify.query.filter_by(id=2).one_or_none()
        assert result is None
    
    # edit
    url = url_for("identify.edit_view",id=1)
    data = {
        "outPutSetting":"y",
        "emails":"new.test@test.org",
        "repositoryName":"test_new_repository"
    }
    with app.test_client() as client:
        res = client.post(url, data=data)
        result = Identify.query.filter_by(id=1).one_or_none()
        assert result.emails == "new.test@test.org"