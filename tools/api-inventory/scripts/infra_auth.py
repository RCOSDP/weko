# -*- coding: utf-8 -*-
"""アプリの外側で行われる認証を判定する。

台帳の auth_required / auth_mechanism はアプリのデコレータしか見ていない。
次の認証はデコレータに現れないため、それだけだと「無認証」に見える。

  OAuth2 クライアント認証
      @oauth2.token_handler / @oauth2.revoke_handler のビューは、oauthlib が
      client_id/secret・認可コード・リフレッシュトークンを検証する。
  nginx
      location に shib_request / deny all / auth_basic / auth_request、
      または `if ($var) { return 401|403; }` があるもの。
  Shibboleth SP
      shib_request は SP の RequestMap で requireSession が有効なパスでだけ
      セッションを要求する。無効なパスでは素通しになるので保護とみなさない。

nginx と SP の設定は **リポジトリ同梱のもの** を読む。サイトごとに設定を
変えている場合、その差は判定に入らない。

    WEKO_ROOT          リポジトリのルート(既定: このファイルから3階層上)
    WEKO_NGINX_CONF    nginx の設定(既定: <WEKO_ROOT>/nginx/weko.conf)
    WEKO_SHIB_CONF     SP の設定(既定: <WEKO_ROOT>/nginx/shibboleth2.xml)
"""
import ast
import functools
import os
import re
import warnings
import xml.etree.ElementTree as ET

# クライアント認証を伴う Flask-OAuthlib のハンドラ
CLIENT_AUTH_HANDLERS = ('token_handler', 'revoke_handler')

# 台帳の URI のパラメータ(<int:pid> 等)を置き換える値
_PARAM_RE = re.compile(r'<[^>]*>')
# 他の変数(接続元アドレス等)には「任意の値」としてこれを入れる
_ARBITRARY = '\x01'


def repo_root():
    return os.environ.get('WEKO_ROOT') or os.path.abspath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))


def _conf_path(env, rel):
    return os.environ.get(env) or os.path.join(repo_root(), rel)


# --- OAuth2 ------------------------------------------------------------------

@functools.lru_cache(maxsize=None)
def _functions(path):
    """ファイル内の関数を (開始行, 終了行, デコレータ名の一覧) で返す。"""
    try:
        with warnings.catch_warnings():
            # 解析対象のソースの不正なエスケープ等の警告は、ここでは関係ない
            warnings.simplefilter('ignore', SyntaxWarning)
            tree = ast.parse(open(path, encoding='utf-8', errors='replace').read())
    except (OSError, SyntaxError, ValueError):
        return ()
    out = []
    for n in ast.walk(tree):
        if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        names = []
        for d in n.decorator_list:
            f = d.func if isinstance(d, ast.Call) else d
            if isinstance(f, ast.Attribute):
                names.append(f.attr)
            elif isinstance(f, ast.Name):
                names.append(f.id)
        start = min([n.lineno] + [d.lineno for d in n.decorator_list])
        out.append((start, getattr(n, 'end_lineno', n.lineno), tuple(names)))
    return tuple(out)


def oauth2_client_auth(impl_file, impl_line):
    """実装関数が OAuth2 のクライアント認証を伴うハンドラなら説明を返す。"""
    try:
        line = int(impl_line)
    except (TypeError, ValueError):
        return ''
    if not impl_file or impl_file.startswith('('):
        return ''
    path = os.path.join(repo_root(), impl_file)
    best = None
    for start, end, names in _functions(path):
        if start <= line <= end and (best is None or end - start < best[1] - best[0]):
            best = (start, end, names)
    if not best:
        return ''
    hit = [n for n in best[2] if n in CLIENT_AUTH_HANDLERS]
    return f'oauth2-client(@{hit[0]})' if hit else ''


# --- nginx -------------------------------------------------------------------

_TOKEN_RE = re.compile(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|[{};]|[^\s{};]+')


def _tokens(text):
    for line in text.splitlines():
        # 引用符の外の # 以降はコメント
        out, quote = [], None
        for ch in line:
            if quote:
                quote = None if ch == quote else quote
            elif ch in '"\'':
                quote = ch
            elif ch == '#':
                break
            out.append(ch)
        for t in _TOKEN_RE.findall(''.join(out)):
            yield t


def parse_nginx(text):
    """nginx の設定を [(名前, 引数, 子 or None), ...] の木にする。"""
    stack = [[]]
    words = []
    for t in _tokens(text):
        if t == ';':
            if words:
                stack[-1].append((words[0], words[1:], None))
            words = []
        elif t == '{':
            node = (words[0] if words else '', words[1:], [])
            stack[-1].append(node)
            stack.append(node[2])
            words = []
        elif t == '}':
            if len(stack) > 1:
                stack.pop()
            words = []
        else:
            words.append(t[1:-1] if t[:1] in '"\'' and t[-1:] == t[:1] else t)
    return stack[0]


@functools.lru_cache(maxsize=None)
def _nginx(path):
    try:
        return parse_nginx(open(path, encoding='utf-8').read())
    except OSError:
        return None


def _servers(tree):
    servers = [n for n in tree if n[0] == 'server' and n[2] is not None]
    tls = [s for s in servers
           if any(d[0] == 'listen' and ('443' in ' '.join(d[1]) or 'ssl' in d[1])
                  for d in s[2])]
    return tls or servers


def _maps(tree):
    """map ブロックを {変数名: (元の文字列, 既定値, [(キー, 値), ...])} にする。"""
    maps = {}
    for name, args, children in tree:
        if name != 'map' or children is None or len(args) != 2:
            continue
        default, entries = '', []
        for k, v, _ in children:
            val = v[0] if v else ''
            if k == 'default':
                default = val
            elif k not in ('hostnames', 'volatile', 'include'):
                entries.append((k, val))
        maps[args[1]] = (args[0], default, entries)
    return maps


def _eval_map(m, method):
    """map の値を、$request_method=method・他の変数=任意の値として求める。"""
    source, default, entries = m
    s = source.replace('$request_method', method)
    s = re.sub(r'\$\{?\w+\}?', _ARBITRARY, s)
    for k, v in entries:
        if not k.startswith('~') and k == s:
            return v
    for k, v in entries:
        if k.startswith('~*'):
            if re.search(k[2:], s, re.I):
                return v
        elif k.startswith('~'):
            if re.search(k[1:], s):
                return v
    return default


def match_location(server, path):
    """nginx と同じ規則で path に一致する location ブロックを返す。"""
    locs = [(a[0], a[1], c) if a and a[0] in ('=', '^~', '~', '~*') else ('', a[0] if a else '', c)
            for n, a, c in server[2] if n == 'location' and c is not None]
    for mod, pat, c in locs:
        if mod == '=' and pat == path:
            return f'= {pat}', c
    prefix = None
    for mod, pat, c in locs:
        if mod in ('', '^~') and path.startswith(pat) and (prefix is None or len(pat) > len(prefix[1])):
            prefix = (mod, pat, c)
    if prefix and prefix[0] == '^~':
        return prefix[1], prefix[2]
    for mod, pat, c in locs:
        if mod in ('~', '~*') and re.search(pat, path, re.I if mod == '~*' else 0):
            return f'{mod} {pat}', c
    return (prefix[1], prefix[2]) if prefix else (None, None)


def _requires_shib_session(path):
    """SP の RequestMap で path に requireSession が効いているか。"""
    p = _conf_path('WEKO_SHIB_CONF', 'nginx/shibboleth2.xml')
    try:
        root = ET.parse(p).getroot()
    except (OSError, ET.ParseError):
        return False
    on = lambda e, inherited: (e.get('requireSession', inherited).lower()
                               in ('true', '1'))
    for host in root.iter():
        if not host.tag.endswith('}Host') and host.tag != 'Host':
            continue
        req = on(host, 'false')
        best = None
        for sub in host.iter():
            if (sub.tag.endswith('}Path') or sub.tag == 'Path') and sub.get('name'):
                prefix = '/' + sub.get('name').strip('/')
                if (path == prefix or path.startswith(prefix + '/')) and (
                        best is None or len(prefix) > len(best[0])):
                    best = (prefix, on(sub, 'true' if req else 'false'))
        if (best[1] if best else req):
            return True
    return False


def _protection(block, maps, method, path):
    """location ブロックの中で、method のリクエストを拒否/認証する仕組みを返す。"""
    found = []
    for name, args, children in block:
        if name == 'shib_request' and args and args[0] != 'off':
            if _requires_shib_session(path):
                found.append('shibboleth(shib_request+requireSession)')
        elif name == 'deny' and args == ['all']:
            found.append('nginx(allow/deny)')
        elif name == 'auth_basic' and args and args[0] != 'off':
            found.append('nginx(auth_basic)')
        elif name == 'auth_request' and args and args[0] != 'off':
            found.append('nginx(auth_request)')
        elif name == 'limit_except' and children is not None \
                and method not in args \
                and not (method == 'HEAD' and 'GET' in args):
            found += [p for p in _protection(children, maps, method, path)]
        elif name == 'if' and children is not None:
            denies = any(n == 'return' and a and a[0] in ('401', '403')
                         for n, a, _ in children)
            cond = ' '.join(args).strip('()').strip()
            if denies and re.fullmatch(r'\$\w+', cond) and cond in maps \
                    and _eval_map(maps[cond], method) not in ('', '0'):
                found.append(f'nginx(if {cond} → 403)')
    return found


def nginx_auth(uri, methods):
    """uri へのリクエストを nginx が(全 methods について)守っていれば説明を返す。"""
    tree = _nginx(_conf_path('WEKO_NGINX_CONF', 'nginx/weko.conf'))
    if not tree or not uri:
        return ''
    path = _PARAM_RE.sub('x', uri.strip())
    maps = _maps(tree)
    labels = []
    for server in _servers(tree):
        loc, block = match_location(server, path)
        if block is None:
            return ''
        found = set()
        for m in methods or ['GET']:
            hit = _protection(block, maps, m, path)
            if not hit:
                return ''
            found.update(hit)
        labels += [f'{label} @location {loc}' for label in sorted(found)]
    return '; '.join(labels)


def detect(uris, methods, impl_file, impl_line):
    """アプリの外側の認証を説明する文字列を返す。無ければ ''。"""
    found = oauth2_client_auth(impl_file, impl_line)
    if found:
        return found
    hits = [nginx_auth(u, methods) for u in uris if u]
    return hits[0] if hits and all(hits) else ''
