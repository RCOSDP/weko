# -*- coding: utf-8 -*-
"""認証デコレータの機械的な不整合検出 (AST)."""
import ast, os, json, sys, collections

ROOT='/home/mhaya/wekov2'
SKIP=('/tests','/examples','/.tox','/node_modules','/cookiecutter')

AUTH = {'login_required','login_required_customize','roles_required','require_api_auth',
        'require_oauth_scopes','need_record_permission','need_permissions','check_authority',
        'stats_api_access_required','check_index_access_permissions','check_on_behalf_of',
        'require_oauth','pass_record'}
PERM_SUFFIX = ('_permission.require','permission.require')

def dname(d):
    c=d.func if isinstance(d,ast.Call) else d
    p=[]
    while isinstance(c,ast.Attribute):
        p.append(c.attr); c=c.value
    if isinstance(c,ast.Name): p.append(c.id)
    return '.'.join(reversed(p))

def is_auth(n):
    return n.split('.')[-1] in AUTH or n.endswith('permission.require') or 'require' in n.split('.')[-1]

findings=collections.defaultdict(list)
handlers=[]   # (file, line, kind, name, decorators, cls)

for dp,dn,fn in os.walk(os.path.join(ROOT,'modules')):
    if any(s in dp+'/' for s in SKIP): continue
    for f in sorted(fn):
        if not f.endswith('.py'): continue
        fp=os.path.join(dp,f); rel=os.path.relpath(fp,ROOT)
        try:
            text=open(fp,encoding='utf-8',errors='replace').read(); tree=ast.parse(text)
        except Exception: continue
        lines=text.splitlines()

        # --- 1. コメントアウトされた認証デコレータ ---
        for i,l in enumerate(lines,1):
            s=l.strip()
            if s.startswith('#') and '@' in s:
                body=s.lstrip('#').strip()
                if body.startswith('@'):
                    nm=body[1:].split('(')[0]
                    if is_auth(nm) or 'permission' in nm:
                        findings['commented_auth'].append((rel,i,body[:90]))

        # --- ハンドラ収集 ---
        for node in ast.walk(tree):
            if isinstance(node,ast.ClassDef):
                for b in node.body:
                    if isinstance(b,(ast.FunctionDef,ast.AsyncFunctionDef)):
                        decs=[dname(d) for d in b.decorator_list]
                        if b.name in ('get','post','put','delete','patch','head') or any(d.endswith('.route') or d=='expose' for d in decs):
                            handlers.append((rel,b.lineno,'method',b.name,decs,node.name))
            if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
                decs=[dname(d) for d in node.decorator_list]
                if any(d.endswith('.route') for d in decs):
                    handlers.append((rel,node.lineno,'route',node.name,decs,None))
                if any(d=='expose' or d.endswith('.expose') for d in decs):
                    handlers.append((rel,node.lineno,'expose',node.name,decs,None))

# --- 2. require_oauth_scopes が require_api_auth 無しで使われている ---
for rel,ln,kind,name,decs,cls in handlers:
    short=[d.split('.')[-1] for d in decs]
    if 'require_oauth_scopes' in short and not ('require_api_auth' in short or 'require_oauth' in short):
        findings['scope_without_auth'].append((rel,ln,f"{cls+'.' if cls else ''}{name}",decs))

# --- 3. roles_required が実質無効 (引数空 / allow_anonymous=True) ---
for dp,dn,fn in os.walk(os.path.join(ROOT,'modules')):
    if any(s in dp+'/' for s in SKIP): continue
    for f in fn:
        if not f.endswith('.py'): continue
        fp=os.path.join(dp,f); rel=os.path.relpath(fp,ROOT)
        try: tree=ast.parse(open(fp,encoding='utf-8',errors='replace').read())
        except Exception: continue
        for node in ast.walk(tree):
            if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
                for d in node.decorator_list:
                    if not isinstance(d,ast.Call): continue
                    if dname(d).split('.')[-1]!='roles_required': continue
                    empty = bool(d.args) and isinstance(d.args[0],ast.List) and len(d.args[0].elts)==0
                    anon  = any(k.arg=='allow_anonymous' and getattr(k.value,'value',None) is True for k in d.keywords)
                    if empty or anon:
                        findings['roles_required_noop'].append(
                            (rel,node.lineno,node.name,f"empty_list={empty} allow_anonymous={anon}"))

# --- 4. 同一クラス内でデコレータが不揃いなハンドラ ---
byclass=collections.defaultdict(list)
for rel,ln,kind,name,decs,cls in handlers:
    if cls: byclass[(rel,cls)].append((ln,name,decs))
for (rel,cls),ms in byclass.items():
    if len(ms)<2: continue
    authed=[m for m in ms if any(is_auth(d.split('.')[-1]) or 'permission' in d for d in m[2])]
    bare  =[m for m in ms if not any(is_auth(d.split('.')[-1]) or 'permission' in d for d in m[2])]
    if authed and bare:
        findings['inconsistent_in_class'].append(
            (rel,cls,[f"{m[1]}@{m[0]}" for m in bare],[f"{m[1]}@{m[0]}" for m in authed]))

# --- 5. 同一 admin.py 内で @expose に権限デコレータの有無が混在 ---
bymod=collections.defaultdict(list)
for rel,ln,kind,name,decs,cls in handlers:
    if kind=='expose': bymod[rel].append((ln,name,decs))
for rel,ms in bymod.items():
    if len(ms)<2: continue
    permed=[m for m in ms if any('permission' in d for d in m[2])]
    bare  =[m for m in ms if not any('permission' in d for d in m[2])]
    if permed and bare:
        findings['inconsistent_expose'].append(
            (rel,len(permed),[f"{m[1]}@{m[0]}" for m in bare]))

json.dump({k:v for k,v in findings.items()}, open(sys.argv[1],'w',encoding='utf-8'),
          ensure_ascii=False, indent=1, default=str)
for k,v in findings.items(): print(f"{k}: {len(v)}")
