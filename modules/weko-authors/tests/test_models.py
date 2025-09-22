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
import pytest
from mock import patch
import json

from weko_authors.models import (
    Authors,
    AuthorsPrefixSettings,
    AuthorsAffiliationSettings
)
# .tox/c1/bin/pytest --cov=weko_authors tests/test_models.py -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp


# .tox/c1/bin/pytest --cov=weko_authors tests/test_models.py::TestAuthors -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
class TestAuthors:
    def test_none_data(self, db):
        author = Authors()
        db.session.add(author)
        db.session.commit()

        result = Authors.query.first()
        assert result.id == 1
        assert result.json == {}

# .tox/c1/bin/pytest --cov=weko_authors tests/test_models.py::TestAuthors::test_get_sequence -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_get_sequence(self, db, mocker):
        class MockSession:
            def __init__(self):
                self.id = {"authors_id_seq":1}
            def execute(self, sequence):
                name = sequence.name
                self.id[name] += 1
                return self.id[name]
        session = MockSession()
        # session is not None
        result = Authors.get_sequence(session)
        assert result == 2

        # session is None
        with patch("weko_authors.models.db.session.execute", side_effect=session.execute):
            result = Authors.get_sequence(None)
            assert result == 3
# .tox/c1/bin/pytest --cov=weko_authors tests/test_models.py::TestAuthors::test_get_first_email_by_id -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_get_first_email_by_id(self, authors):
        # not find author
        result = Authors.get_first_email_by_id(1000)
        assert result == None

        # find author
        result = Authors.get_first_email_by_id(1)
        assert result == "test.taro@test.org"

        # raise Exception
        with patch("flask_sqlalchemy._QueryProperty.__get__") as mock_query:
            mock_query.return_value.filter_by.return_value.one_or_none.side_effect=Exception("test_error")
            result = Authors.get_first_email_by_id(1)
            assert result == None

# .tox/c1/bin/pytest --cov=weko_authors tests/test_models.py::TestAuthors::test_get_author_by_id -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_get_author_by_id(self, db):
        author = Authors(
            json={"test_data":"value"}
        )
        db.session.add(author)
        db.session.commit()

        # not find author
        result = Authors.get_author_by_id(1000)
        assert result == None

        # find author
        result = Authors.get_author_by_id(1)
        assert result == {"test_data":"value"}

        # raise Exception
        with patch("flask_sqlalchemy._QueryProperty.__get__") as mock_query:
            mock_query.return_value.filter_by.return_value.one_or_none.side_effect=Exception("test_error")
            result = Authors.get_author_by_id(1)
            assert result == None

# .tox/c1/bin/pytest --cov=weko_authors tests/test_models.py::TestAuthors::test_get_authorIdInfo -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_get_authorIdInfo(self, authors, authors_prefix_settings, db):

        result = Authors.get_authorIdInfo('WEKO',[1000,2000])
        assert result == []

        result = Authors.get_authorIdInfo('WEKO',[1])
        assert result == ["1"]

        result = Authors.get_authorIdInfo('WEKO',[3])
        assert result == []

# .tox/c1/bin/pytest --cov=weko_authors tests/test_models.py::TestAuthors::test_add_communities_single -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_add_communities_single(self, authors, community, db):
        author = authors[0]
        author.add_communities([community[0].id])
        db.session.commit()
        assert author.communities == [community[0]]

# .tox/c1/bin/pytest --cov=weko_authors tests/test_models.py::TestAuthors::test_add_communities_multi -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_add_communities_multi(self, authors, community, db):
        author = authors[0]
        author.add_communities([community[0].id, community[1].id, community[2].id])
        db.session.commit()
        assert author.communities == [community[0], community[1], community[2]]

# .tox/c1/bin/pytest --cov=weko_authors tests/test_models.py::TestAuthors::test_add_communities_none -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_add_communities_none(self, authors, db):
        author = authors[0]
        author.add_communities([])
        db.session.commit()
        assert author.communities == []

# .tox/c1/bin/pytest --cov=weko_authors tests/test_models.py::TestAuthors::test_add_communities_exception -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_add_communities_exception(self, authors, community, db):
        author = authors[0]
        with patch("weko_authors.models.db.session.add", side_effect=Exception("test_error")):
            with pytest.raises(Exception):
                author.add_communities([community[0].id])
            assert author.communities == []

# .tox/c1/bin/pytest --cov=weko_authors tests/test_models.py::TestAuthors::test_update_communities_add -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_update_communities_add(self, authors, community, db):
        author = authors[0]
        author.update_communities([community[0].id])
        db.session.commit()
        assert author.communities == [community[0]]

# .tox/c1/bin/pytest --cov=weko_authors tests/test_models.py::TestAuthors::test_update_communities_keep -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_update_communities_keep(self, authors, community, db):
        author  = authors[0]
        author.communities = [community[0]]
        db.session.commit()

        author.update_communities([community[0].id])
        db.session.commit()
        assert author.communities == [community[0]]

# .tox/c1/bin/pytest --cov=weko_authors tests/test_models.py::TestAuthors::test_update_communities_delete -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_update_communities_delete(self, authors, community, db):
        author  = authors[0]
        author.communities = [community[0], community[1]]
        db.session.commit()

        author.update_communities([community[1].id])
        db.session.commit()
        assert author.communities == [community[1]]

# .tox/c1/bin/pytest --cov=weko_authors tests/test_models.py::TestAuthors::test_update_communities_add_delete -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_update_communities_add_delete(self, authors, community, db):
        author  = authors[0]
        author.communities = [community[0], community[1]]
        db.session.commit()

        author.update_communities([community[2].id])
        db.session.commit()
        assert author.communities == [community[2]]

# .tox/c1/bin/pytest --cov=weko_authors tests/test_models.py::TestAuthors::test_update_communities_none -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_update_communities_none(self, authors, community, db):
        author  = authors[0]
        author.communities = [community[0], community[1]]
        db.session.commit()

        author.update_communities([])
        db.session.commit()
        assert author.communities == []

# .tox/c1/bin/pytest --cov=weko_authors tests/test_models.py::TestAuthors::test_update_communities_exception -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_update_communities_exception(self, authors, community, db):
        author  = authors[0]
        author.communities = [community[0]]
        db.session.commit()

        with patch("weko_authors.models.db.session.add", side_effect=Exception("test_error")):
            with pytest.raises(Exception):
                author.update_communities([community[1].id])
            assert author.communities == [community[0]]


# .tox/c1/bin/pytest --cov=weko_authors tests/test_models.py::TestAuthorsPrefixSettings -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
class TestAuthorsPrefixSettings:
# .tox/c1/bin/pytest --cov=weko_authors tests/test_models.py::TestAuthorsPrefixSettings::test_create -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_create(self, db, community):
        AuthorsPrefixSettings.create(
            name="ORCID",
            scheme="ORCID  ",
            url="https://orcid.org/##"
        )
        result = AuthorsPrefixSettings.query.filter_by(name="ORCID").one()
        assert result
        assert result.scheme == "ORCID"

        # scheme is none
        AuthorsPrefixSettings.create(
            name="CiNii",
            scheme="",
            url="https://ci.nii.ac.jp/author/##"
        )
        result = AuthorsPrefixSettings.query.filter_by(name="CiNii").one()
        assert result
        assert result.scheme == None

        # with community_id
        AuthorsPrefixSettings.create(
            name="ISNI",
            scheme="ISNI",
            url="https://isni.org/##",
            community_ids=[community[0].id, community[1].id]
        )
        result = AuthorsPrefixSettings.query.filter_by(name="ISNI").one()
        assert result
        assert result.scheme == "ISNI"
        assert result.communities == [community[0], community[1]]

        # raise Exception
        with patch("weko_authors.models.db.session.commit", side_effect=BaseException("test_error")):
            with pytest.raises(BaseException):
                AuthorsPrefixSettings.create(
                    name="WEKO",
                    scheme="WEKO",
                    url=""
                )
            result = AuthorsPrefixSettings.query.filter_by(name="WEKO").one_or_none()
            assert result is None

# .tox/c1/bin/pytest --cov=weko_authors tests/test_models.py::TestAuthorsPrefixSettings::test_update -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_update(self,authors_prefix_settings, community):
        AuthorsPrefixSettings.update(
            id=1,
            name="WEKO3",
            scheme="WEKO3  ",
            url="https://new_weko3/##"
        )
        result = AuthorsPrefixSettings.query.filter_by(id=1).one()
        assert result.name == "WEKO3"
        assert result.scheme == "WEKO3"

        # scheme is none
        AuthorsPrefixSettings.update(
            id=1,
            name="WEKO2",
            scheme="",
            url="https://new_weko2/##"
        )
        result = AuthorsPrefixSettings.query.filter_by(id=1).one()
        assert result.name == "WEKO2"
        assert result.scheme == "WEKO3"

        # set community_ids
        AuthorsPrefixSettings.update(
            id=1,
            name="WEKO2",
            scheme="",
            url="https://new_weko2/##",
            community_ids=[community[0].id, community[1].id]
        )
        result = AuthorsPrefixSettings.query.filter_by(id=1).one()
        assert result.name == "WEKO2"
        assert result.scheme == "WEKO3"
        assert result.communities == [community[0], community[1]]

        # add and remove community_ids
        AuthorsPrefixSettings.update(
            id=1,
            name="WEKO2",
            scheme="",
            url="https://new_weko2/##",
            community_ids=[community[1].id, community[2].id]
        )
        result = AuthorsPrefixSettings.query.filter_by(id=1).one()
        assert result.name == "WEKO2"
        assert result.scheme == "WEKO3"
        assert result.communities == [community[1], community[2]]

        # raise Exception
        with patch("weko_authors.models.db.session.commit", side_effect=BaseException("test_error")):
            with pytest.raises(BaseException):
                AuthorsPrefixSettings.update(
                    id=1,
                    name="WEKO100",
                    scheme="WEKO100",
                    url="https://new_weko100/##"
                )
            result = AuthorsPrefixSettings.query.filter_by(id=1).one()
            assert result.name == "WEKO2"
            assert result.scheme == "WEKO3"

# .tox/c1/bin/pytest --cov=weko_authors tests/test_models.py::TestAuthorsPrefixSettings::test_delete -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_delete(self, authors_prefix_settings):
        AuthorsPrefixSettings.delete(1)
        result = AuthorsPrefixSettings.query.filter_by(id=1).one_or_none()
        assert result is None

        # raise Exception
        with patch("weko_authors.models.db.session.commit", side_effect=BaseException("test_error")):
            with pytest.raises(BaseException):
                AuthorsPrefixSettings.delete(2)
            result = AuthorsPrefixSettings.query.filter_by(id=2).one_or_none()
            assert result

# .tox/c1/bin/pytest --cov=weko_authors tests/test_models.py::TestAuthorsPrefixSettings::test_add_communities_single -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_add_communities_single(self, authors_prefix_settings, community, db):
        prefix = authors_prefix_settings[0]
        prefix.add_communities([community[0].id])
        db.session.commit()
        assert prefix.communities == [community[0]]

# .tox/c1/bin/pytest --cov=weko_authors tests/test_models.py::TestAuthorsPrefixSettings::test_add_communities_multi -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_add_communities_multi(self, authors_prefix_settings, community, db):
        prefix = authors_prefix_settings[0]
        prefix.add_communities([community[0].id, community[1].id, community[2].id])
        db.session.commit()
        assert prefix.communities == [community[0], community[1], community[2]]

# .tox/c1/bin/pytest --cov=weko_authors tests/test_models.py::TestAuthorsPrefixSettings::test_add_communities_none -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_add_communities_none(self, authors_prefix_settings, db):
        prefix = authors_prefix_settings[0]
        prefix.add_communities([])
        db.session.commit()
        assert prefix.communities == []

# .tox/c1/bin/pytest --cov=weko_authors tests/test_models.py::TestAuthorsPrefixSettings::test_add_communities_exception -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_add_communities_exception(self, authors_prefix_settings, community, db):
        prefix = authors_prefix_settings[0]
        with patch("weko_authors.models.db.session.add", side_effect=Exception("test_error")):
            with pytest.raises(Exception):
                prefix.add_communities([community[0].id])
            assert prefix.communities == []

# .tox/c1/bin/pytest --cov=weko_authors tests/test_models.py::TestAuthorsPrefixSettings::test_update_communities_add -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_update_communities_add(self, authors_prefix_settings, community, db):
        prefix = authors_prefix_settings[0]
        prefix.update_communities([community[0].id])
        db.session.commit()
        assert prefix.communities == [community[0]]

# .tox/c1/bin/pytest --cov=weko_authors tests/test_models.py::TestAuthorsPrefixSettings::test_update_communities_keep -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_update_communities_keep(self, authors_prefix_settings, community, db):
        prefix = authors_prefix_settings[0]
        prefix.communities = [community[0]]
        db.session.commit()

        prefix.update_communities([community[0].id])
        db.session.commit()
        assert prefix.communities == [community[0]]

# .tox/c1/bin/pytest --cov=weko_authors tests/test_models.py::TestAuthorsPrefixSettings::test_update_communities_delete -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_update_communities_delete(self, authors_prefix_settings, community, db):
        prefix = authors_prefix_settings[0]
        prefix.communities = [community[0], community[1]]
        db.session.commit()

        prefix.update_communities([community[1].id])
        db.session.commit()
        assert prefix.communities == [community[1]]

# .tox/c1/bin/pytest --cov=weko_authors tests/test_models.py::TestAuthorsPrefixSettings::test_update_communities_add_delete -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_update_communities_add_delete(self, authors_prefix_settings, community, db):
        prefix = authors_prefix_settings[0]
        prefix.communities = [community[0], community[1]]
        db.session.commit()

        prefix.update_communities([community[2].id])
        db.session.commit()
        assert prefix.communities == [community[2]]

# .tox/c1/bin/pytest --cov=weko_authors tests/test_models.py::TestAuthorsPrefixSettings::test_update_communities_none -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_update_communities_none(self, authors_prefix_settings, community, db):
        prefix = authors_prefix_settings[0]
        prefix.communities = [community[0], community[1]]
        db.session.commit()

        prefix.update_communities([])
        db.session.commit()
        assert prefix.communities == []

# .tox/c1/bin/pytest --cov=weko_authors tests/test_models.py::TestAuthorsPrefixSettings::test_update_communities_exception -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_update_communities_exception(self, authors_prefix_settings, community, db):
        prefix = authors_prefix_settings[0]
        prefix.communities = [community[0]]
        db.session.commit()

        with patch("weko_authors.models.db.session.add", side_effect=Exception("test_error")):
            with pytest.raises(Exception):
                prefix.update_communities([community[1].id])
            assert prefix.communities == [community[0]]


# .tox/c1/bin/pytest --cov=weko_authors tests/test_models.py::TestAuthorsAffiliationSettings -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
class TestAuthorsAffiliationSettings:
# .tox/c1/bin/pytest --cov=weko_authors tests/test_models.py::TestAuthorsAffiliationSettings::test_create -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_create(self, db, community):
        AuthorsAffiliationSettings.create(
            name="ORCID",
            scheme="ORCID  ",
            url="https://orcid.org/##"
        )
        result = AuthorsAffiliationSettings.query.filter_by(name="ORCID").one()
        assert result
        assert result.scheme == "ORCID"

        # scheme is none
        AuthorsAffiliationSettings.create(
            name="CiNii",
            scheme="",
            url="https://ci.nii.ac.jp/author/##"
        )
        result = AuthorsAffiliationSettings.query.filter_by(name="CiNii").one()
        assert result
        assert result.scheme == None

        # with community_id
        AuthorsAffiliationSettings.create(
            name="ISNI",
            scheme="ISNI",
            url="https://isni.org/##",
            community_ids=[community[0].id, community[1].id]
        )
        result = AuthorsAffiliationSettings.query.filter_by(name="ISNI").one()
        assert result
        assert result.scheme == "ISNI"
        assert result.communities == [community[0], community[1]]

        # raise Exception
        with patch("weko_authors.models.db.session.commit", side_effect=BaseException("test_error")):
            with pytest.raises(BaseException):
                AuthorsAffiliationSettings.create(
                    name="WEKO",
                    scheme="WEKO",
                    url=""
                )
            result = AuthorsAffiliationSettings.query.filter_by(name="WEKO").one_or_none()
            assert result is None

# .tox/c1/bin/pytest --cov=weko_authors tests/test_models.py::TestAuthorsAffiliationSettings::test_update -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_update(self,authors_affiliation_settings, community):
        AuthorsAffiliationSettings.update(
            id=1,
            name="WEKO3",
            scheme="WEKO3  ",
            url="https://new_weko3/##"
        )
        result = AuthorsAffiliationSettings.query.filter_by(id=1).one()
        assert result.name == "WEKO3"
        assert result.scheme == "WEKO3"

        # scheme is none
        AuthorsAffiliationSettings.update(
            id=1,
            name="WEKO2",
            scheme="",
            url="https://new_weko2/##"
        )
        result = AuthorsAffiliationSettings.query.filter_by(id=1).one()
        assert result.name == "WEKO2"
        assert result.scheme == "WEKO3"

        # set community_ids
        AuthorsAffiliationSettings.update(
            id=1,
            name="WEKO2",
            scheme="",
            url="https://new_weko2/##",
            community_ids=[community[0].id, community[1].id]
        )
        result = AuthorsAffiliationSettings.query.filter_by(id=1).one()
        assert result.name == "WEKO2"
        assert result.scheme == "WEKO3"
        assert result.communities == [community[0], community[1]]

        # add and remove community_ids
        AuthorsAffiliationSettings.update(
            id=1,
            name="WEKO2",
            scheme="",
            url="https://new_weko2/##",
            community_ids=[community[1].id, community[2].id]
        )
        result = AuthorsAffiliationSettings.query.filter_by(id=1).one()
        assert result.name == "WEKO2"
        assert result.scheme == "WEKO3"
        assert result.communities == [community[1], community[2]]

        # raise Exception
        with patch("weko_authors.models.db.session.commit", side_effect=BaseException("test_error")):
            with pytest.raises(BaseException):
                AuthorsAffiliationSettings.update(
                    id=1,
                    name="WEKO100",
                    scheme="WEKO100",
                    url="https://new_weko100/##"
                )
            result = AuthorsAffiliationSettings.query.filter_by(id=1).one()
            assert result.name == "WEKO2"
            assert result.scheme == "WEKO3"

# .tox/c1/bin/pytest --cov=weko_authors tests/test_models.py::TestAuthorsAffiliationSettings::test_delete -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_delete(self, authors_affiliation_settings):
        AuthorsAffiliationSettings.delete(1)
        result = AuthorsAffiliationSettings.query.filter_by(id=1).one_or_none()
        assert result is None

        # raise Exception
        with patch("weko_authors.models.db.session.commit", side_effect=BaseException("test_error")):
            with pytest.raises(BaseException):
                AuthorsAffiliationSettings.delete(2)
            result = AuthorsAffiliationSettings.query.filter_by(id=2).one_or_none()
            assert result

# .tox/c1/bin/pytest --cov=weko_authors tests/test_models.py::TestAuthorsAffiliationSettings::test_add_communities_single -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_add_communities_single(self, authors_affiliation_settings, community, db):
        affiliation = authors_affiliation_settings[0]
        affiliation.add_communities([community[0].id])
        db.session.commit()
        assert affiliation.communities == [community[0]]

# .tox/c1/bin/pytest --cov=weko_authors tests/test_models.py::TestAuthorsAffiliationSettings::test_add_communities_multi -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_add_communities_multi(self, authors_affiliation_settings, community, db):
        affiliation = authors_affiliation_settings[0]
        affiliation.add_communities([community[0].id, community[1].id, community[2].id])
        db.session.commit()
        assert affiliation.communities == [community[0], community[1], community[2]]

# .tox/c1/bin/pytest --cov=weko_authors tests/test_models.py::TestAuthorsAffiliationSettings::test_add_communities_none -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_add_communities_none(self, authors_affiliation_settings, db):
        affiliation = authors_affiliation_settings[0]
        affiliation.add_communities([])
        db.session.commit()
        assert affiliation.communities == []

# .tox/c1/bin/pytest --cov=weko_authors tests/test_models.py::TestAuthorsAffiliationSettings::test_add_communities_exception -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_add_communities_exception(self, authors_affiliation_settings, community, db):
        affiliation = authors_affiliation_settings[0]
        with patch("weko_authors.models.db.session.add", side_effect=Exception("test_error")):
            with pytest.raises(Exception):
                affiliation.add_communities([community[0].id])
            assert affiliation.communities == []

# .tox/c1/bin/pytest --cov=weko_authors tests/test_models.py::TestAuthorsAffiliationSettings::test_update_communities_add -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_update_communities_add(self, authors_affiliation_settings, community, db):
        affiliation = authors_affiliation_settings[0]
        affiliation.update_communities([community[0].id])
        db.session.commit()
        assert affiliation.communities == [community[0]]

# .tox/c1/bin/pytest --cov=weko_authors tests/test_models.py::TestAuthorsAffiliationSettings::test_update_communities_keep -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_update_communities_keep(self, authors_affiliation_settings, community, db):
        affiliation = authors_affiliation_settings[0]
        affiliation.communities = [community[0]]
        db.session.commit()

        affiliation.update_communities([community[0].id])
        db.session.commit()
        assert affiliation.communities == [community[0]]

# .tox/c1/bin/pytest --cov=weko_authors tests/test_models.py::TestAuthorsAffiliationSettings::test_update_communities_delete -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_update_communities_delete(self, authors_affiliation_settings, community, db):
        affiliation = authors_affiliation_settings[0]
        affiliation.communities = [community[0], community[1]]
        db.session.commit()

        affiliation.update_communities([community[1].id])
        db.session.commit()
        assert affiliation.communities == [community[1]]

# .tox/c1/bin/pytest --cov=weko_authors tests/test_models.py::TestAuthorsAffiliationSettings::test_update_communities_add_delete -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_update_communities_add_delete(self, authors_affiliation_settings, community, db):
        affiliation = authors_affiliation_settings[0]
        affiliation.communities = [community[0], community[1]]
        db.session.commit()

        affiliation.update_communities([community[2].id])
        db.session.commit()
        assert affiliation.communities == [community[2]]

# .tox/c1/bin/pytest --cov=weko_authors tests/test_models.py::TestAuthorsAffiliationSettings::test_update_communities_none -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_update_communities_none(self, authors_affiliation_settings, community, db):
        affiliation = authors_affiliation_settings[0]
        affiliation.communities = [community[0], community[1]]
        db.session.commit()

        affiliation.update_communities([])
        db.session.commit()
        assert affiliation.communities == []

# .tox/c1/bin/pytest --cov=weko_authors tests/test_models.py::TestAuthorsAffiliationSettings::test_update_communities_exception -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_update_communities_exception(self, authors_affiliation_settings, community, db):
        affiliation = authors_affiliation_settings[0]
        affiliation.communities = [community[0]]
        db.session.commit()

        with patch("weko_authors.models.db.session.add", side_effect=Exception("test_error")):
            with pytest.raises(Exception):
                affiliation.update_communities([community[1].id])
            assert affiliation.communities == [community[0]]

