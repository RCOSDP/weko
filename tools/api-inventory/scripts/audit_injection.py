# -*- coding: utf-8 -*-
"""注入・パストラバーサル系の機械検出 (AST + 正規表現)."""
import ast, os, re, json, sys, collections
ROOT='/home/mhaya/wekov2'
SKIP=('/tests','/examples','/.tox','/node_modules','/cookiecutter','/docs/')
F=collections.defaultdict(list)

# ユーザ入力を表す式
USER_SRC = re.compile(r"request\.(args|form|values|json|view_args|data|files|headers|cookies)"
                      r"|get_json\(|request\.stream|kwargs\.get\(")

def dname(d):
    c=d.func if isinstance(d,ast.Call) else d
    p=[]
    while isinstance(c,ast.Attribute): p.append(c.attr); c=c.value
    if isinstance(c,ast.Name): p.append(c.id)
    return '.'.join(reversed(p))

for dp,dn,fn in os.walk(os.path.join(ROOT,'modules')):
    if any(s in dp+'/' for s in SKIP): continue
    for f in sorted(fn):
        if not f.endswith('.py'): continue
        fp=os.path.join(dp,f); rel=os.path.relpath(fp,ROOT)
        try:
            text=open(fp,encoding='utf-8',errors='replace').read(); tree=ast.parse(text)
        except Exception: continue
        lines=text.splitlines()

        for node in ast.walk(tree):
            # 1. eval / exec
            if isinstance(node,ast.Call) and dname(node.func) in ('eval','exec'):
                seg='\n'.join(lines[max(0,node.lineno-3):node.lineno+1])
                F['eval_exec'].append((rel,node.lineno,lines[node.lineno-1].strip()[:100],
                                       'USER_INPUT' if USER_SRC.search(seg) else ''))
            # 2. pickle.loads / yaml.load
            if isinstance(node,ast.Call) and dname(node.func) in ('pickle.loads','yaml.load','marshal.loads'):
                F['deserialize'].append((rel,node.lineno,lines[node.lineno-1].strip()[:100]))
            # 3. subprocess with shell=True
            if isinstance(node,ast.Call) and dname(node.func).startswith(('subprocess.','os.system','os.popen')):
                sh=any(k.arg=='shell' and getattr(k.value,'value',None) is True for k in node.keywords)
                if sh or dname(node.func) in ('os.system','os.popen'):
                    F['shell'].append((rel,node.lineno,lines[node.lineno-1].strip()[:100]))

        # 4. ファイル保存/パス組み立てに secure_filename を使っていない
        for i,l in enumerate(lines,1):
            if re.search(r"\.save\(|PyFSFileStorage\(|open\(\s*[a-z_]*(path|url|dir|file)", l, re.I):
                ctx='\n'.join(lines[max(0,i-12):i+2])
                if USER_SRC.search(ctx) and 'secure_filename' not in ctx:
                    F['path_unsafe'].append((rel,i,l.strip()[:110]))
        # 5. ES painless / クエリへの文字列連結
        for i,l in enumerate(lines,1):
            if re.search(r"(source|script|inline)\s*[:=].*(\+|format\(|f['\"])", l) and 'painless' in '\n'.join(lines[max(0,i-6):i+6]):
                F['es_script_concat'].append((rel,i,l.strip()[:110]))
        # 6. 生SQLへの文字列連結
        for i,l in enumerate(lines,1):
            if re.search(r"(execute|text)\s*\(\s*(f['\"]|['\"].*['\"]\s*\+|['\"].*%s)", l):
                F['sql_concat'].append((rel,i,l.strip()[:110]))
        # 7. except で return が無い (None返却 → 500)
        for node in ast.walk(tree):
            if isinstance(node,ast.FunctionDef):
                has_ret=any(isinstance(x,ast.Return) and x.value is not None for x in ast.walk(node))
                if not has_ret: continue
                for h in [x for x in ast.walk(node) if isinstance(x,ast.ExceptHandler)]:
                    if not any(isinstance(s,(ast.Return,ast.Raise)) for s in ast.walk(h)):
                        # 最後の except で return が無く、関数末尾にも return が無い
                        last=node.body[-1]
                        if not isinstance(last,(ast.Return,ast.Raise)):
                            F['except_no_return'].append((rel,h.lineno,node.name))
                            break
        # 8. ミュータブルなデフォルト引数
        for node in ast.walk(tree):
            if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
                for d in node.args.defaults+node.args.kw_defaults:
                    if isinstance(d,(ast.List,ast.Dict,ast.Set)):
                        F['mutable_default'].append((rel,node.lineno,node.name)); break

json.dump(F,open(sys.argv[1],'w',encoding='utf-8'),ensure_ascii=False,indent=1,default=str)
for k,v in sorted(F.items(),key=lambda x:-len(x[1])): print(f"{k}: {len(v)}")
