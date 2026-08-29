# -*- coding: utf-8 -*-
"""TSV の 36-39列 (last_commit / date / subject / release_tag) を git から埋める。

使い方: python3 enrich_git.py <in.tsv> <out.tsv>
- 14列目 impl_file (repo相対), 15列目 impl_line を見て、その行を含む
  def/class の行範囲を AST で特定し `git log -1 -L a,b:file` で最終コミットを取る。
- release_tag は `git tag --sort=creatordate --contains <sha>` の先頭 (最初に入ったリリース)。
"""
import ast, os, subprocess, sys, functools

ROOT = '/home/mhaya/wekov2'
NCOL = 41

@functools.lru_cache(maxsize=None)
def def_ranges(path):
    """ファイル内の全 def/class の (start, end) をリストで返す。"""
    fp = os.path.join(ROOT, path)
    if not os.path.isfile(fp):
        return ()
    try:
        tree = ast.parse(open(fp, encoding='utf-8', errors='replace').read())
    except Exception:
        return ()
    out = []
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            s = min([n.lineno] + [d.lineno for d in n.decorator_list])
            out.append((s, getattr(n, 'end_lineno', n.lineno)))
    return tuple(out)

def enclosing(path, line):
    """line を含む最小の def/class 範囲。無ければ (line, line)。"""
    best = None
    for s, e in def_ranges(path):
        if s <= line <= e:
            if best is None or (e - s) < (best[1] - best[0]):
                best = (s, e)
    return best or (line, line)

@functools.lru_cache(maxsize=None)
def git_last(path, start, end):
    try:
        r = subprocess.run(
            ['git', '-C', ROOT, 'log', '-1', '--format=%h\x1f%ad\x1f%s', '--date=short',
             '-L', f'{start},{end}:{path}'],
            capture_output=True, text=True, timeout=60)
    except Exception:
        return ('', '', '')
    line = r.stdout.split('\n', 1)[0] if r.stdout else ''
    parts = line.split('\x1f')
    if len(parts) != 3:
        return ('', '', '')
    subj = parts[2].replace('\t', ' ').strip()
    return (parts[0], parts[1], subj[:120])

@functools.lru_cache(maxsize=None)
def git_tag(sha):
    if not sha:
        return ''
    r = subprocess.run(['git', '-C', ROOT, 'tag', '--sort=creatordate', '--contains', sha],
                       capture_output=True, text=True, timeout=60)
    tags = [t for t in r.stdout.split('\n') if t.strip()]
    return tags[0] if tags else '(未リリース)'

def main(src, dst):
    out = []
    bad = 0
    for i, raw in enumerate(open(src, encoding='utf-8'), 1):
        raw = raw.rstrip('\n')
        if not raw.strip():
            continue
        c = raw.split('\t')
        if len(c) < NCOL:
            c += [''] * (NCOL - len(c))
        elif len(c) > NCOL:
            sys.stderr.write(f'WARN line {i}: {len(c)} cols (>41), truncating tail into notes\n')
            c = c[:NCOL - 1] + [' | '.join(c[NCOL - 1:])]
            bad += 1
        path, ln = c[13].strip(), c[14].strip()
        sha = date = subj = tag = ''
        try:
            line = int(ln)
        except ValueError:
            line = None
        if path and line and os.path.isfile(os.path.join(ROOT, path)):
            s, e = enclosing(path, line)
            sha, date, subj = git_last(path, s, e)
            tag = git_tag(sha)
        c[35], c[36], c[37], c[38] = sha or '-', date or '-', subj or '-', tag or '-'
        out.append('\t'.join(x.replace('\t', ' ') for x in c))
    with open(dst, 'w', encoding='utf-8') as f:
        f.write('\n'.join(out) + '\n')
    print(f'rows={len(out)} col_fixups={bad}')

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
