# -*- coding: utf-8 -*-
"""infra_auth のテスト。

    python3 -m pytest tools/api-inventory/tests
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                '..', 'scripts'))
import infra_auth  # noqa: E402

NGINX = r'''
map "$request_method:$realip_remote_addr" $sp_denied {
	default          1;
	"~^(GET|HEAD):"  0;
	"POST:127.0.0.1" 0;
}

server {
	listen 80;
	return 301 https://$host$request_uri;
}

server {
	listen 443 ssl;
	server_name weko3.example.org;

	location = /weko/shib/login {
		if ($sp_denied) {
			return 403;
		}
		uwsgi_pass app_server;
	}
	location /weko/shib {
		uwsgi_pass app_server;
		#deny all;
	}
	location ~ /secure/ {
		shib_request /shibauthorizer;
	}
	location /nosession/ {
		shib_request /shibauthorizer;
	}
	location /internal {
		allow 127.0.0.1;
		deny all;
	}
	location /basic {
		auth_basic "restricted";
	}
	location /readonly {
		limit_except GET {
			deny all;
		}
	}
	location ^~ /static/secure {
		root /var/www;
	}
	location / {
		uwsgi_pass app_server;
	}
}
'''

SHIB = '''<SPConfig xmlns="urn:mace:shibboleth:3.0:native:sp:config">
  <RequestMapper type="XML">
    <RequestMap>
      <Host name="weko3.example.org" authType="shibboleth" requireSession="true">
        <Path name="/secure" />
        <Path name="/nosession" requireSession="false" />
      </Host>
    </RequestMap>
  </RequestMapper>
</SPConfig>
'''

VIEWS = '''
@blueprint.route('/token', methods=['POST', ])
@oauth2.token_handler
def access_token():
    return None


@blueprint.route('/authorize', methods=['GET', 'POST'])
@login_required
@oauth2.authorize_handler
def authorize(*args, **kwargs):
    return True
'''


@pytest.fixture(autouse=True)
def confs(tmp_path, monkeypatch):
    (tmp_path / 'nginx').mkdir()
    (tmp_path / 'nginx' / 'weko.conf').write_text(NGINX, encoding='utf-8')
    (tmp_path / 'nginx' / 'shibboleth2.xml').write_text(SHIB, encoding='utf-8')
    (tmp_path / 'views.py').write_text(VIEWS, encoding='utf-8')
    monkeypatch.setenv('WEKO_ROOT', str(tmp_path))
    monkeypatch.delenv('WEKO_NGINX_CONF', raising=False)
    monkeypatch.delenv('WEKO_SHIB_CONF', raising=False)
    infra_auth._nginx.cache_clear()
    infra_auth._functions.cache_clear()
    return tmp_path


def test_oauth2_token_handler():
    assert infra_auth.oauth2_client_auth('views.py', 4) \
        == 'oauth2-client(@token_handler)'
    # デコレータの行を指していても同じ関数とみなす
    assert infra_auth.oauth2_client_auth('views.py', 3) \
        == 'oauth2-client(@token_handler)'


def test_oauth2_authorize_handler_is_not_client_auth():
    assert infra_auth.oauth2_client_auth('views.py', 12) == ''


@pytest.mark.parametrize('impl_file, impl_line', [
    ('(framework/自動生成)', '0'),
    ('views.py', '-'),
    ('missing.py', '1'),
    ('', ''),
])
def test_oauth2_unknown_source(impl_file, impl_line):
    assert infra_auth.oauth2_client_auth(impl_file, impl_line) == ''


def test_map_if_403_depends_on_method():
    # POST は 127.0.0.1 以外から 403 になるので守られている
    assert infra_auth.nginx_auth('/weko/shib/login', ['POST']) \
        == 'nginx(if $sp_denied → 403) @location = /weko/shib/login'
    # GET は map で 0 になるので素通し
    assert infra_auth.nginx_auth('/weko/shib/login', ['GET']) == ''
    # 1つでも素通しのメソッドがあれば守られていないとみなす
    assert infra_auth.nginx_auth('/weko/shib/login', ['GET', 'POST']) == ''


def test_prefix_location_without_protection():
    assert infra_auth.nginx_auth('/weko/shib/logout', ['GET']) == ''


def test_shib_request_needs_require_session():
    assert infra_auth.nginx_auth('/secure/login.py', ['GET']) \
        == 'shibboleth(shib_request+requireSession) @location ~ /secure/'
    # requireSession が無効なパスでは shib_request は素通し
    assert infra_auth.nginx_auth('/nosession/x', ['GET']) == ''


def test_deny_all_and_auth_basic():
    assert infra_auth.nginx_auth('/internal/api', ['POST']) \
        == 'nginx(allow/deny) @location /internal'
    assert infra_auth.nginx_auth('/basic/x', ['GET']) \
        == 'nginx(auth_basic) @location /basic'


def test_limit_except():
    assert infra_auth.nginx_auth('/readonly/x', ['GET']) == ''
    assert infra_auth.nginx_auth('/readonly/x', ['POST']) \
        == 'nginx(allow/deny) @location /readonly'


def test_caret_tilde_prefix_wins_over_regex():
    # ^~ の前方一致は正規表現の location より優先される
    assert infra_auth.nginx_auth('/static/secure/a.js', ['GET']) == ''


def test_uri_parameters_are_replaced():
    assert infra_auth.nginx_auth('/internal/<int:pid_value>', ['GET']) \
        == 'nginx(allow/deny) @location /internal'


def test_missing_nginx_conf(monkeypatch, tmp_path):
    monkeypatch.setenv('WEKO_NGINX_CONF', str(tmp_path / 'none.conf'))
    assert infra_auth.nginx_auth('/internal/api', ['POST']) == ''


def test_detect():
    assert infra_auth.detect(['/token'], ['POST'], 'views.py', '4') \
        == 'oauth2-client(@token_handler)'
    assert infra_auth.detect(['/internal/a', '/internal/b'], ['GET'], '', '') \
        == 'nginx(allow/deny) @location /internal'
    # 複数の URI のどれかが守られていなければ守られていないとみなす
    assert infra_auth.detect(['/internal/a', '/weko/shib/x'], ['GET'], '', '') == ''
