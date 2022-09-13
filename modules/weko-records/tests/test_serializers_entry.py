import pytest

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

