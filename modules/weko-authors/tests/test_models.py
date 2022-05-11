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

"""Test weko-authors models."""

from weko_authors.models import Authors, AuthorsAffiliationSettings


def test_authors_affiliation_settings_create(app):
    """
    Test of authors affiliation settings create.
    :param app: The flask application.
    """
    with app.app_context():
        AuthorsAffiliationSettings.create(
            name='testName1', scheme='testScheme1',
            url='http://www.test1.org/##')

        affiliation = AuthorsAffiliationSettings.query.filter_by(
            id=1).one_or_none()
        assert affiliation.name == 'testName1'
        assert affiliation.scheme == 'testScheme1'
        assert affiliation.url == 'http://www.test1.org/##'
        assert affiliation.created
        assert affiliation.updated


def test_authors_affiliation_settings_update(app):
    """
    Test of authors affiliation settings update.
    :param app: The flask application.
    """
    with app.app_context():
        a = AuthorsAffiliationSettings.create(
            name='testName2', scheme='testScheme2',
            url='http://www.test2.org/##')
        u = a.updated
        AuthorsAffiliationSettings.update(
            id=1,
            name='testChangedName',
            scheme='testChangedScheme',
            url='http://www.testchanged.org/##'
        )

        affiliation = AuthorsAffiliationSettings.query.filter_by(
            id=1).one_or_none()
        assert affiliation.name == 'testChangedName'
        assert affiliation.scheme == 'testChangedScheme'
        assert affiliation.url == 'http://www.testchanged.org/##'
        assert affiliation.created
        assert u is not affiliation.updated


def test_authors_affiliation_settings_delete(app):
    """
    Test of authors affiliation settings delete.
    :param app: The flask application.
    """
    with app.app_context():
        a = AuthorsAffiliationSettings.create(
            name='testName3', scheme='testScheme3',
            url='http://www.test3.org/test/##')
        a.delete(id=a.id)

        affiliation = AuthorsAffiliationSettings.query.filter_by(
            id=a.id).one_or_none()
        assert affiliation is None
