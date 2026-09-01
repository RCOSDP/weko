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

"""未認証時に JSON を返すかどうかの判定。

wants_json() は request しか見ないので、weko のフィクスチャは使わず
素の Flask で確かめる。

.tox/c1/bin/pytest tests/test_unauthorized.py -v
"""
import json

import pytest
from flask import Flask

from weko_accounts.unauthorized import NAVIGATION_DESTS, wants_json


@pytest.fixture()
def app():
    return Flask(__name__)


def _wants(app, path='/records/1', **kwargs):
    with app.test_request_context(path, **kwargs):
        return wants_json()


# .tox/c1/bin/pytest tests/test_unauthorized.py::test_api_app_is_always_json -v
def test_api_app_is_always_json(app):
    """APIアプリにはログイン画面が無いので常に JSON。"""
    assert _wants(app, '/api/schemas/') is True


# .tox/c1/bin/pytest tests/test_unauthorized.py::test_explicit_json_callers -v
@pytest.mark.parametrize('kwargs', [
    {'headers': {'X-Requested-With': 'XMLHttpRequest'}},          # jQuery
    {'data': json.dumps({}), 'content_type': 'application/json'},  # JSON本文
    {'headers': {'Sec-Fetch-Dest': 'empty'}},                      # fetch/XHR
    {'headers': {'Accept': 'application/json'}},                   # Accept
])
def test_explicit_json_callers(app, kwargs):
    assert _wants(app, **kwargs) is True


# .tox/c1/bin/pytest tests/test_unauthorized.py::test_navigation_gets_login_screen -v
@pytest.mark.parametrize('dest', sorted(NAVIGATION_DESTS))
def test_navigation_gets_login_screen(app, dest):
    """ブラウザが HTML を描画する遷移はログイン画面へ送る。

    'document' 以外を一律 JSON 扱いにしていたため、@login_required の
    ページを <iframe> に読み込むと枠の中に生の JSON が表示され、
    ログイン導線が消えていた(invenio-previewer が制限付きファイルを
    そうやって埋め込む)。
    """
    assert _wants(app, headers={'Sec-Fetch-Dest': dest}) is False


# .tox/c1/bin/pytest tests/test_unauthorized.py::test_subresource_gets_json -v
@pytest.mark.parametrize('dest', ['empty', 'script', 'image', 'style'])
def test_subresource_gets_json(app, dest):
    """描画されない読み込みは JSON でよい。"""
    assert _wants(app, headers={'Sec-Fetch-Dest': dest}) is True


# .tox/c1/bin/pytest tests/test_unauthorized.py::test_plain_page_request -v
def test_plain_page_request(app):
    """Sec-Fetch-Dest を送らない素の画面要求はログイン画面へ。"""
    assert _wants(app, headers={'Accept': 'text/html'}) is False


# .tox/c1/bin/pytest tests/test_unauthorized.py::test_html_form_post -v
def test_html_form_post(app):
    """通常の HTML フォーム POST もログイン画面へ。

    「非GETなら JSON」という規則を置くとここが壊れる。
    """
    assert _wants(app, method='POST', headers={'Accept': 'text/html'}) is False
