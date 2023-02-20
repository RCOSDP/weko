import pytest
import dateutil.tz
from copy import deepcopy
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


def isoformat():
        return "<xml>test</xml>"

def values():
    sample_obj = MagicMock()
    
    def extend_atom(item):
        return str(item)
    
    sample_obj.extend_atom
    return [{"atom": "test", "inst": sample_obj}]

data = MagicMock()
data.text = "text"
data.isoformat = isoformat
data.values = values

sample = WekoFeedEntry()
sample._WekoFeedEntry__atom_id = "test"
sample._WekoFeedEntry__atom_title = "test"
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
sample._WekoFeedEntry__extensions = data
sample._WekoFeedEntry__atom_published = data
sample._WekoFeedEntry__atom_rights = "<xml>test</xml>"


# def atom_entry(self, extensions=True):
def test_atom_entry(app):
    sample_copy = deepcopy(sample)

    sample_copy._WekoFeedEntry__atom_id = ""
    sample_copy._WekoFeedEntry__atom_title = ""

    # Exception coverage ~ 90 raise ValueError('Required fields not set') 
    try:
        sample_copy.atom_entry()
    except:
        pass
    
    sample_copy._WekoFeedEntry__atom_id = "test"
    sample_copy._WekoFeedEntry__atom_title = "test"

    sample_copy._WekoFeedEntry__atom_content = {}

    # Exception coverage ~ 103 raise ValueError('Entry must contain an alternate link or '
    try:
        sample_copy.atom_entry()
    except:
        pass

    data1 = MagicMock()
    data1.text = "text"
    data1.isoformat = isoformat
    data1.values = values

    sample_copy._WekoFeedEntry__atom_content = sample._WekoFeedEntry__atom_content
    sample_copy._WekoFeedEntry__extensions = data1
    sample_copy._WekoFeedEntry__atom_published = data1
    sample_copy._WekoFeedEntry__atom_rights = "<xml>test</xml>"

    with patch("lxml.etree.SubElement", return_value=data1):
        assert sample_copy.atom_entry() != None

    sample_copy._WekoFeedEntry__atom_author[0]["name"] = False
    sample_copy._WekoFeedEntry__atom_contributor[0]["name"] = False
    assert sample_copy.atom_entry() != None
    sample_copy._WekoFeedEntry__atom_author[0]["name"] = "name"
    sample_copy._WekoFeedEntry__atom_contributor[0]["name"] = "name"

    del sample_copy._WekoFeedEntry__atom_content["src"]
    assert sample_copy.atom_entry() != None
    
    sample_copy._WekoFeedEntry__atom_content["type"] = "CDATA"
    assert sample_copy.atom_entry() != None

    sample_copy._WekoFeedEntry__atom_content["type"] = "text"
    assert sample_copy.atom_entry() != None

    sample_copy._WekoFeedEntry__atom_content["type"] = "+xml"
    assert sample_copy.atom_entry() != None

    sample_copy._WekoFeedEntry__atom_content["type"] = "<xml>test</xml>"
    # Exception coverage ~ 148 raise ValueError('base64 encoded content is not '
    try:
        sample_copy.atom_entry()
    except:
        pass


# def rss_entry(self, extensions=True): 
def test_rss_entry(app):
    sample_copy = deepcopy(sample)

    # Exception coverage ~ 230 ValueError: Required fields not set
    try:
        sample_copy.rss_entry()
    except:
        pass

    sample_copy._WekoFeedEntry__rss_author = "test"
    sample_copy._WekoFeedEntry__rss_category = [{
        "value": "value",
        "domain": "domain"
    }]
    sample_copy._WekoFeedEntry__rss_comments = "test"
    sample_copy._WekoFeedEntry__rss_content = {
        "type": "CDATA",
        "content": "content",
    }
    sample_copy._WekoFeedEntry__rss_description = "test"
    sample_copy._WekoFeedEntry__rss_enclosure = {
        "url": "url",
        "length": "length",
        "type": "type",
    }
    sample_copy._WekoFeedEntry__rss_guid = {
        "guid": "guid",
        "permalink": "content",
    }
    sample_copy._WekoFeedEntry__rss_itemUrl = "test"
    sample_copy._WekoFeedEntry__rss_link = "test"
    sample_copy._WekoFeedEntry__rss_pubDate = datetime.now()
    sample_copy._WekoFeedEntry__rss_seeAlso = "test"
    sample_copy._WekoFeedEntry__rss_source = {
        "url": "url",
        "title": "title",
    }
    sample_copy._WekoFeedEntry__rss_title = "test"
    assert sample_copy.rss_entry() != None

    sample_copy._WekoFeedEntry__extensions = {
        "test": {
            "rss": "rss",
            "inst": MagicMock()
        }
    }
    sample_copy._WekoFeedEntry__rss_content = {"type": "NOTCDATA", "content": "content",}
    assert sample_copy.rss_entry() != None

    sample_copy._WekoFeedEntry__rss_description = "test"
    sample_copy._WekoFeedEntry__rss_content = False
    assert sample_copy.rss_entry() != None

    sample_copy._WekoFeedEntry__rss_description = False
    sample_copy._WekoFeedEntry__rss_content = {"type": "NOTCDATA", "content": "content",}
    assert sample_copy.rss_entry() != None


# def id(self, id=None):
def test_id(app):
    sample_copy = deepcopy(sample)
    assert sample_copy.id(sample_copy._WekoFeedEntry__atom_id) != None


# def updated(self, updated=None): 
def test_updated(app):
    sample_copy = deepcopy(sample)
    
    # Exception coverage 408 ~ ValueError: Invalid datetime format
    try:
        sample_copy.updated(updated=MagicMock())
    except:
        pass
    
     # Exception coverage 408 ~ ValueError: Invalid datetime format
    try:
        sample_copy.updated(updated=datetime.now())
    except:
        pass

    assert sample_copy.updated(updated=datetime.now(dateutil.tz.tzutc())) != None
    

# def author(self, author=None, replace=False, **kwargs):
def test_author(app):
    sample_copy = deepcopy(sample)

    assert sample_copy.author(author=None, name='John Doe', email='jdoe@example.com', replace=True) != None
    assert sample_copy.author(author=None, name='', email='jdoe@example.com', replace=True) != None


# def content(self, content=None, lang=None, src=None, type=None):
def test_content(app):
    sample_copy = deepcopy(sample)

    assert sample_copy.content(src=True) != None
    assert sample_copy.content(content=True, lang=True, type=True) != None


# def summary(self, summary=None): 
def test_summary(app):
    sample_copy = deepcopy(sample)

    assert sample_copy.summary(summary=True) != None


# def description(self, description=None, isSummary=False):
def test_description(app):
    sample_copy = deepcopy(sample)

    assert sample_copy.description(description=True, isSummary=True) != None
    assert sample_copy.description(description=True, isSummary=False) != None


# def category(self, category=None, replace=False, **kwargs): 
def test_category(app):
    sample_copy = deepcopy(sample)

    assert sample_copy.category(category=None, term="term") != None

    sample_copy._WekoFeedEntry__atom_category = None
    assert sample_copy.category(category={"term": "term", "scheme": "scheme", "label": "label"}, replace=True) != None


# def contributor(self, contributor=None, replace=False, **kwargs):
def test_contributor(app):
    sample_copy = deepcopy(sample)

    assert sample_copy.contributor(contributor=None, name="name") != None
    assert sample_copy.contributor(contributor={"name": "name", "email": "email", "uri": "uri"}, replace=True) != None


# def load_extension(self, name, atom=True, rss=True):
def test_load_extension(app):
    sample_copy = deepcopy(sample)

    # Exception coverage
    try:
        sample_copy._WekoFeedEntry__extensions = {'test': 'test'}
        sample_copy.load_extension(name="test")
    except:
        pass

    sample_copy._WekoFeedEntry__extensions = [{'test': 'test'}]
    sample_copy.load_extension(name="dc")

    
# def register_extension(self, namespace, extension_class_entry=None, atom=True, rss=True, jpcoar=True): 
def test_register_extension(app):
    sample_copy = deepcopy(sample)

    def extension_class_entry():
        return "test"

    sample_copy._WekoFeedEntry__extensions = {'test': 'test'}
    sample_copy.register_extension(namespace="sample", extension_class_entry=extension_class_entry)

    # Exception coverage
    try:
        sample_copy._WekoFeedEntry__extensions = {'test': 'test'}
        sample_copy.register_extension(namespace="test")
    except:
        pass

    # Exception coverage
    try:
        sample_copy._WekoFeedEntry__extensions = [{'test': 'test'}]
        sample_copy.register_extension(namespace="test")
    except:
        pass


