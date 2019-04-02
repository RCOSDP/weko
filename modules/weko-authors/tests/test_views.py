# -*- coding: utf-8 -*-
#
# This file is part of WEKO3.
# Copyright (C) 2017 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# WEKO3 is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with WEKO3; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.

"""Module tests."""
import json

from flask import Flask, url_for
from flask_security import url_for_security
from flask_security.utils import hash_password
from helpers import create_admin, insert_author, login, test_author_dict
from invenio_access.models import ActionRoles, ActionUsers
from invenio_access.permissions import superuser_access
from invenio_accounts.models import Role, User
from invenio_db import db

from weko_authors import WekoAuthors
from weko_authors.models import Authors
from weko_authors.permissions import action_author_access
from weko_authors.views import blueprint, blueprint_api, create, \
    delete_author, index, update_author


def test_index(base_app):
    """Test index."""
    WekoAuthors(base_app)
    base_app.register_blueprint(blueprint)
    app = base_app

    with app.test_request_context():
        index_url = url_for('weko_authors.index')

    with app.test_client() as client:
        create_admin(app, client)
        login(app, client)
        res = client.get(index_url, follow_redirects=True)
        assert res.status_code == 200


def test_create(base_app):
    """Test add."""
    WekoAuthors(base_app)  # TODO: Refactor me.
    base_app.register_blueprint(blueprint_api)
    app = base_app

    with app.test_request_context():
        add_url = url_for('weko_authors.create')

    with app.test_client() as client:
        create_admin(app, client)
        login(app, client)
        res = client.post(add_url, data=json.dumps(test_author_dict),
                          content_type='application/json',
                          follow_redirects=False)
        res_data = json.loads(res.data.decode())
        added_author = db.session.query(Authors). \
            filter_by(id=test_author_dict['pk_id']). \
            first()

        assert 'Success' in res.get_data(as_text=True)
        assert added_author is not None


def test_delete_author(base_app):
    """Test delete."""
    WekoAuthors(base_app)  # TODO: Refactor me.
    base_app.register_blueprint(blueprint_api)
    app = base_app
    test_author = dict(id=test_author_dict['pk_id'],
                       json=json.dumps(test_author_dict))

    with app.app_context():
        author = Authors(**test_author)
        db.session.add(author)
        db.session.commit()

    with app.test_request_context():
        delete_url = url_for('weko_authors.delete_author')

    with app.test_client() as client:
        create_admin(app, client)
        login(app, client)
        res = client.post(delete_url, data=json.dumps(test_author_dict),
                          content_type='application/json',
                          follow_redirects=False)
        deleted_author = db.session.query(Authors). \
            filter_by(id=test_author_dict['pk_id']). \
            first()

        assert 'Success' in res.get_data(as_text=True)
        assert deleted_author is None


def test_update_author(base_app):
    """Test edit/update."""
    WekoAuthors(base_app)  # TODO: Refactor me.
    base_app.register_blueprint(blueprint_api)
    app = base_app
    test_author_data = test_author_dict
    insert_author(app, db, test_author_data)

    # Change value for testing update
    test_author_data['emailInfo'] = [dict(email='NEW@NEW.com')]

    with app.test_request_context():
        update_url = url_for('weko_authors.update_author')

    with app.test_client() as client:
        create_admin(app, client)
        login(app, client)
        res = client.post(update_url, data=json.dumps(test_author_data),
                          content_type='application/json',
                          follow_redirects=False)

        edited_author = db.session.query(Authors). \
            filter_by(id=test_author_data['pk_id']). \
            first()
        print(edited_author.json)
        # assert 'Success' in res.get_data(as_text=True)
        assert 'NEW@NEW.com' in edited_author.json
