import pytest
from flask import request, url_for
from re import L
from elasticsearch_dsl.query import Match, Range, Terms, Bool
from mock import patch, MagicMock
from werkzeug import ImmutableMultiDict
from werkzeug.datastructures import CombinedMultiDict

from invenio_search import RecordsSearch

from weko_search_ui.query import (
    get_item_type_aggs,
    get_permission_filter,
    default_search_factory,
    item_path_search_factory,
    check_admin_user,
    opensearch_factory,
    item_search_factory,
    feedback_email_search_factory
)

# def get_item_type_aggs(search_index):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_query.py::test_get_item_type_aggs -vv -s --cov-branch --cov-report=xml --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_get_item_type_aggs(i18n_app, users, client_request_args, db_records2, records):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        assert not get_item_type_aggs("test-weko")


# def get_permission_filter(index_id: str = None):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_query.py::test_get_permission_filter -vv -s --cov-branch --cov-report=xml --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
class MockSearchPerm:
    def __init__(self):
        pass
    
    def can(self):
        return True

def test_get_permission_filter(i18n_app, users, client_request_args, indices):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        res = get_permission_filter(33)
        assert res==([Match(publish_status='0'), Range(publish_date={'lte': 'now/d'}), Terms(path=[]), Bool(must=[Match(publish_status='0'), Match(relation_version_is_last='true')])], ['1'])
        mock_searchperm = MagicMock(side_effect=MockSearchPerm)
        with patch('weko_search_ui.query.search_permission', mock_searchperm):
            res = get_permission_filter()
            assert res==([Bool(must=[Terms(path=['1'])], should=[Match(weko_creator_id='5'), Match(weko_shared_id='5'), Bool(must=[Match(publish_status='0'), Range(publish_date={'lte': 'now/d'})])]), Bool(must=[Match(relation_version_is_last='true')])], ['1'])


# def default_search_factory(self, search, query_parser=None, search_type=None):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_query.py::test_default_search_factory -vv -s --cov-branch --cov-report=xml --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_default_search_factory(i18n_app, users):
    search = RecordsSearch()
    i18n_app.config['WEKO_SEARCH_KEYWORDS_DICT'] = {
        "nested": {
            "id": (
                "",
                {
                    "id_attr": {
                        "identifier": ("relation.relatedIdentifier", "identifierType=*"),
                        "URI": ("identifier", "identifierType=*"),
                        "fullTextURL": ("file.URI", "objectType=*"),
                        "selfDOI": ("identifierRegistration", "identifierType=*"),
                        "ISBN": ("relation.relatedIdentifier", "identifierType=ISBN"),
                        "ISSN": ("sourceIdentifier", "identifierType=ISSN"),
                        "NCID": [
                            ("relation.relatedIdentifier", "identifierType=NCID"),
                            ("sourceIdentifier", "identifierType=NCID"),
                        ],
                        "pmid": ("relation.relatedIdentifier", "identifierType=PMID"),
                        "doi": ("relation.relatedIdentifier", "identifierType=DOI"),
                        "NAID": ("relation.relatedIdentifier", "identifierType=NAID"),
                        "ichushi": ("relation.relatedIdentifier", "identifierType=ICHUSHI"),
                    }
                },
            ),
            "license": ("content", {"license": ("content.licensetype.raw")}),
        },
        "string": {
            "title": ["search_title", "search_title.ja"],
            "creator": ["search_creator", "search_creator.ja"],
            "des": ["search_des", "search_des.ja"],
            "publisher": ["search_publisher", "search_publisher.ja"],
            "cname": ["search_contributor", "search_contributor.ja"],
            "itemtype": ("itemtype.keyword", str),
            "type": {
                "type.raw": [
                    "conference paper",
                    "data paper",
                    "departmental bulletin paper",
                    "editorial",
                    "journal article",
                    "newspaper",
                    "periodical",
                    "review article",
                    "software paper",
                    "article",
                    "book",
                    "book part",
                    "cartographic material",
                    "map",
                    "conference object",
                    "conference proceedings",
                    "conference poster",
                    "dataset",
                    "interview",
                    "image",
                    "still image",
                    "moving image",
                    "video",
                    "lecture",
                    "patent",
                    "internal report",
                    "report",
                    "research report",
                    "technical report",
                    "policy report",
                    "report part",
                    "working paper",
                    "data management plan",
                    "sound",
                    "thesis",
                    "bachelor thesis",
                    "master thesis",
                    "doctoral thesis",
                    "interactive resource",
                    "learning object",
                    "manuscript",
                    "musical notation",
                    "research proposal",
                    "software",
                    "technical documentation",
                    "workflow",
                    "other",
                ]
            },
            "mimetype": "file.mimeType",
            "language": {
                "language": [
                    "jpn",
                    "eng",
                    "fra",
                    "ita",
                    "deu",
                    "spa",
                    "zho",
                    "rus",
                    "lat",
                    "msa",
                    "epo",
                    "ara",
                    "ell",
                    "kor",
                    "-",
                ]
            },
            "srctitle": ["sourceTitle", "sourceTitle.ja"],
            "spatial": "geoLocation.geoLocationPlace",
            "temporal": "temporal",
            "version": "versionType",
            "dissno": "dissertationNumber",
            "degreename": ["degreeName", "degreeName.ja"],
            "dgname": ["dgName", "dgName.ja"],
            "wid": ("creator.nameIdentifier", str),
            "iid": ("path.tree", int),
        },
        "date": {
            "filedate": [
                ("from", "to"),
                (
                    "file.date",
                    {
                        "fd_attr": {
                            "file.date.dateType": [
                                "Accepted",
                                "Available",
                                "Collected",
                                "Copyrighted",
                                "Created",
                                "Issued",
                                "Submitted",
                                "Updated",
                                "Valid",
                            ]
                        }
                    },
                ),
            ],
            "dategranted": [("from", "to"), "dateGranted"],
            "date_range1": [("from", "to"), "date_range1"],
            "date_range2": [("from", "to"), "date_range2"],
            "date_range3": [("from", "to"), "date_range3"],
            "date_range4": [("from", "to"), "date_range4"],
            "date_range5": [("from", "to"), "date_range5"],
        },
        "object": {
            "subject": (
                "subject",
                {
                    "sbjscheme": {
                        "subject.subjectScheme": [
                            "BSH",
                            "DDC",
                            "LCC",
                            "LCSH",
                            "MeSH",
                            "NDC",
                            "NDLC",
                            "NDLSH",
                            "UDC",
                            "Other",
                            "SciVal",
                        ]
                    }
                },
            )
        },
        "text": {
            "text1": "text1",
            "text2": "text2",
            "text3": "text3",
            "text4": "text4",
            "text5": "text5",
            "text6": "text6",
            "text7": "text7",
            "text8": "text8",
            "text9": "text9",
            "text10": "text10",
            "text11": "text11",
            "text12": "text12",
            "text13": "text13",
            "text14": "text14",
            "text15": "text15",
            "text16": "text16",
            "text17": "text17",
            "text18": "text18",
            "text19": "text19",
            "text20": "text20",
            "text21": "text21",
            "text22": "text22",
            "text23": "text23",
            "text24": "text24",
            "text25": "text25",
            "text26": "text26",
            "text27": "text27",
            "text28": "text28",
            "text29": "text29",
            "text30": "text30",
        },
        "range": {
            "integer_range1": [("from", "to"), "integer_range1"],
            "integer_range2": [("from", "to"), "integer_range2"],
            "integer_range3": [("from", "to"), "integer_range3"],
            "integer_range4": [("from", "to"), "integer_range4"],
            "integer_range5": [("from", "to"), "integer_range5"],
            "float_range1": [("from", "to"), "float_range1"],
            "float_range2": [("from", "to"), "float_range2"],
            "float_range3": [("from", "to"), "float_range3"],
            "float_range4": [("from", "to"), "float_range4"],
            "float_range5": [("from", "to"), "float_range5"],
        },
        "geo_distance": {"geo_point1": [("lat", "lon", "distance"), "geo_point1"]},
        "geo_shape": {"geo_shape1": [("lat", "lon", "distance"), "geo_shape1"]},
    }
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        mock_searchperm = MagicMock(side_effect=MockSearchPerm)
        with patch('weko_search_ui.query.search_permission', mock_searchperm):
            res = default_search_factory(self=None, search=search)
            assert res


# def item_path_search_factory(self, search, index_id=None):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_query.py::test_item_path_search_factory -vv -s --cov-branch --cov-report=xml --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_item_path_search_factory(i18n_app, users, indices):
    search = RecordsSearch()
    i18n_app.config['WEKO_SEARCH_TYPE_INDEX'] = 'index'
    i18n_app.config['OAISERVER_ES_MAX_CLAUSE_COUNT'] = 1
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        with patch("weko_search_ui.query.get_item_type_aggs", return_value={}):
            mock_searchperm = MagicMock(side_effect=MockSearchPerm)
            with patch('weko_search_ui.query.search_permission', mock_searchperm):
                res = item_path_search_factory(self=None, search=search, index_id=33)
                assert res
                _rv = ([Bool(must=[Terms(path=[])], should=[Match(weko_creator_id='5'), Match(weko_shared_id='5'), Bool(must=[Match(publish_status='0'), Range(publish_date={'lte': 'now/d'})])]), Bool(must=[Match(relation_version_is_last='true')])], ['3', '4', '5'])
                with patch('weko_search_ui.query.get_permission_filter', return_value=_rv):
                    res = item_path_search_factory(self=None, search=search, index_id=None)
                    assert res


# def check_admin_user():
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_query.py::test_check_admin_user -vv -s --cov-branch --cov-report=xml --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_check_admin_user(i18n_app, users):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        res = check_admin_user()
        assert res==('5', True)


# def opensearch_factory(self, search, query_parser=None):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_query.py::test_opensearch_factory -vv -s --cov-branch --cov-report=xml --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_opensearch_factory(i18n_app, users, indices):
    search = RecordsSearch()
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        res = opensearch_factory(self=None, search=search)
        assert res


# def item_search_factory(self, search, start_date, end_date, list_index_id=None, ignore_publish_status=False, ranking=False):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_query.py::test_item_search_factory -vv -s --cov-branch --cov-report=xml --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_item_search_factory(i18n_app, users, indices):
    search = RecordsSearch()
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        res = item_search_factory(
            self=None,
            search=search,
            start_date='2022-09-01',
            end_date='2022-09-30',
            list_index_id=[33])
        assert res


# def feedback_email_search_factory(self, search):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_query.py::test_feedback_email_search_factory -vv -s --cov-branch --cov-report=xml --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_feedback_email_search_factory(i18n_app, users, indices):
    search = RecordsSearch()
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        res = feedback_email_search_factory(self=None, search=search)
        assert res
