import pytest

from weko_index_tree.api import Indexes


class IndexesTest:
    def test_is_index():
        assert Indexes.is_index('1') is True
        assert Indexes.is_index('1:345') is True
        assert Indexes.is_index('test') is False
        assert Indexes.is_index('user-test') is False
        assert Indexes.is_index('1:345:1024') is True
