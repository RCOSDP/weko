import ast, os, json, sys
ROOT='/home/mhaya/wekov2'
targets=[]
for dp,dn,fn in os.walk(os.path.join(ROOT,'modules')):
    if any(s in dp+'/' for s in ('/tests','/examples','/.tox','/node_modules','/cookiecutter')): continue
    if 'config.py' in fn: targets.append(os.path.join(dp,'config.py'))
out={}
for fp in sorted(targets):
    rel=os.path.relpath(fp,ROOT)
    try: tree=ast.parse(open(fp,encoding='utf-8',errors='replace').read())
    except Exception: continue
    for n in tree.body:
        if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name):
            name=n.targets[0].id
            if 'REST_ENDPOINTS' not in name and 'ENDPOINTS' not in name: continue
            try: val=ast.literal_eval(n.value)
            except Exception:
                # dict(...) call
                val=None
                if isinstance(n.value,ast.Call) and getattr(n.value.func,'id','')=='dict':
                    val={}
                    for k in n.value.keywords:
                        try: val[k.arg]=ast.literal_eval(k.value)
                        except Exception: val[k.arg]='<dynamic>'
            if val is None: val='<dynamic>'
            out.setdefault(rel,{})[name]={'line':n.lineno,'value':val}
json.dump(out,open(sys.argv[1],'w',encoding='utf-8'),ensure_ascii=False,indent=1,default=str)
for f,d in out.items():
    for name,v in d.items():
        val=v['value']
        if isinstance(val,dict):
            for k,vv in val.items():
                r = vv.get('route') if isinstance(vv,dict) else None
                print(f"{f}:{v['line']}\t{name}\t{k}\t{r}")
        else:
            print(f"{f}:{v['line']}\t{name}\t<dynamic>")
