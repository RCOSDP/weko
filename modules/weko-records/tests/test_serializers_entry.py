import pytest
from mock import patch, MagicMock

from datetime import datetime, timezone
from weko_records.serializers.entry import WekoFeedEntry

# class WekoFeedEntry(FeedEntry):
#     def atom_entry(self, extensions=True):
#     def contributor(self, contributor=None, replace=False, **kwargs):
#     def pubDate(self, pubDate=None):
#     def pubdate(self, pubDate=None):
#     def rights(self, rights=None):
#     def comments(self, comments=None):
#     def source(self, url=None, title=None):
#     def enclosure(self, url=None, length=None, type=None):
#     def ttl(self, ttl=None):
# .tox/c1/bin/pytest --cov=weko_records tests/test_serializers_entry.py::test_weko_feed_entry -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_weko_feed_entry():
    feed_entry = WekoFeedEntry()
    # pubDate
    with pytest.raises(Exception) as e:
        feed_entry.pubDate(datetime(2021, 10, 1))
    assert e.type==ValueError
    assert str(e.value)=='Datetime object has no timezone info'
    # pubdate
    assert feed_entry.pubdate(datetime(2021, 10, 1, tzinfo=timezone.utc))==datetime(2021, 10, 1, tzinfo=timezone.utc)
    # rights
    assert feed_entry.rights('test rights')=='test rights'
    # comments
    assert feed_entry.comments('test comments')=='test comments'
    # source
    assert feed_entry.source('http://nii.co.jp', 'test title')=={'url': 'http://nii.co.jp', 'title': 'test title'}
    # enclosure
    assert feed_entry.enclosure('http://nii.co.jp', 100, 'pdf')=={'length': 100, 'type': 'pdf', 'url': 'http://nii.co.jp'}
    # ttl
    assert feed_entry.ttl(100)==100


sample = WekoFeedEntry()


# def atom_entry(self, extensions=True):
def test_atom_entry(app):
    # Exception coverage ~ 90 raise ValueError('Required fields not set') 
    try:
        sample.atom_entry()
    except:
        pass
    
    sample._WekoFeedEntry__atom_id = "test"
    sample._WekoFeedEntry__atom_title = "test"

    # Exception coverage ~ 103 raise ValueError('Entry must contain an alternate link or '
    try:
        sample.atom_entry()
    except:
        pass

    def isoformat():
        return "<xml>test</xml>"

    def values():
        sample_obj = MagicMock()
        
        def extend_atom(item):
            return str(item)
        
        sample_obj.extend_atom
        return [{"atom": "test", "inst": sample_obj}]

    data1 = MagicMock()
    data1.text = "text"
    data1.isoformat = isoformat
    data1.values = values

    sample._WekoFeedEntry__atom_content = {
        "content": "<xml>test</xml>",
        "src": "src",
        "type": "xhtml",
        "lang": "en",
    }

    sample._WekoFeedEntry__atom_link = [{
        "href": "href",
        "rel": "test",
        "type": "test",
        "hreflang": "test",
        "title": "test",
        "length": "test",
    }]

    sample._WekoFeedEntry__atom_category = [{
        "scheme": "scheme",
        "label": "label",
        "term": "term"
    }]

    sample._WekoFeedEntry__atom_summary = "<xml>test</xml>"

    sample._WekoFeedEntry__atom_author = [{
        "name": "name",
        "author": "author",
        "email": "email",
        "uri": "uri",
        "lang": "en",
    }]

    sample._WekoFeedEntry__atom_contributor = [{
        "name": "name",
        "author": "author",
        "email": "email",
        "uri": "uri",
        "lang": "en",
    }]

    sample._WekoFeedEntry__atom_source = {
        "title": "title",
        "link": "link"
    }

    sample._WekoFeedEntry__extensions = data1

    sample._WekoFeedEntry__atom_published = data1

    sample._WekoFeedEntry__atom_rights = "<xml>test</xml>"


    with patch("lxml.etree.SubElement", return_value=data1):
        assert sample.atom_entry() != None

    sample._WekoFeedEntry__atom_author[0]["name"] = False
    sample._WekoFeedEntry__atom_contributor[0]["name"] = False
    assert sample.atom_entry() != None
    sample._WekoFeedEntry__atom_author[0]["name"] = "name"
    sample._WekoFeedEntry__atom_contributor[0]["name"] = "name"

    del sample._WekoFeedEntry__atom_content["src"]
    assert sample.atom_entry() != None
    
    sample._WekoFeedEntry__atom_content["type"] = "CDATA"
    assert sample.atom_entry() != None

    sample._WekoFeedEntry__atom_content["type"] = "text"
    assert sample.atom_entry() != None

    sample._WekoFeedEntry__atom_content["type"] = "+xml"
    assert sample.atom_entry() != None

    sample._WekoFeedEntry__atom_content["type"] = "<xml>test</xml>"
    # Exception coverage ~ 148 raise ValueError('base64 encoded content is not '
    try:
        sample.atom_entry()
    except:
        pass
