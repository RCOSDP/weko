# .tox/c1/bin/pytest --cov=weko_sitemap tests/test_signals.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-sitemap/.tox/c1/tmp

from weko_sitemap.signals import sitemap_finished
from blinker.base import NamedSignal

def test_signals():
    assert isinstance(sitemap_finished,NamedSignal)