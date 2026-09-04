#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""実測レポートを毎回同じ書式で書き出す。"""
import json, sys, collections, re
full, probej, recon, out, rev, head, stamp, writes, phash = sys.argv[1:10]
L=[l.rstrip('\n').split('\t') for l in open(full,encoding='utf-8')]
H={n:i for i,n in enumerate(L[0])}
d=json.load(open(probej,encoding='utf-8'))
ID=['anon','general','contributor','comadmin','repoadmin','sysadmin']
v=collections.Counter(); tot=allblk=sysok=0
for x in d['results']:
    if x.get('status')!='measured': continue
    tot+=1; o=x['observed']
    for k in ID:
        if k in o: v[o[k]['verdict']]+=1
    if all((o.get(k) or {}).get('verdict')=='遮断' for k in ID): allblk+=1
    if (o.get('sysadmin') or {}).get('verdict','').startswith('到達'): sysok+=1
skip=len(d['results'])-tot
pri=collections.Counter(r[H['priority']] for r in L[1:])
app=collections.Counter(r[H['app']] for r in L[1:])
anon=[r[0] for r in L[1:] if re.search(r'anon=(?:\d{3}→)?\d{3}\(到達\)', r[H['dynamic_verified']].split(' ‖ 旧: ')[0])]
low =[r[0] for r in L[1:] if re.search(r'(general|contributor)=(?:\d{3}→)?\d{3}\(到達\)', r[H['dynamic_verified']].split(' ‖ 旧: ')[0])]
gate = open(recon,encoding='utf-8').read()
m=re.search(r'## 判定: (.+)', gate)
lines=[]
A=lines.append
A(f'# 実測レポート {rev}')
A('')
A(f'- 対象リビジョン: `{rev}` (HEAD `{head}`)')
A(f'- 測定日: {stamp}')
A(f'- 書き込み: {"あり(--allow-writes)" if writes!="none" else "なし(読み取り専用)"}')
A(f'- 測定条件: `measure_profile.json` sha256:{phash} ← 前回と同じ値なら同一条件')
A(f'- 台帳: {len(L)-1} 行 × {len(L[0])} 列')
A('')
A('## 経路の整合')
A('')
A(f'- {m.group(1) if m else "(判定行なし)"}')
for key in ('A. インベントリ未収載','B. 実機に無い(未説明)','C. メソッド不一致',
            'D. app列の不一致','E. endpoint 未収載'):
    mm=re.search(r'\| '+re.escape(key)+r'[^|]*\| *(\d+) *\|', gate)
    if mm: A(f'- {key}: {mm.group(1)}')
A('')
A('## 実測')
A('')
A(f'- 測定 {tot} / スキップ {skip}')
A(f'- 全識別子が遮断: {allblk} ({allblk*100//tot if tot else 0}%)')
A(f'- sysadmin が到達: {sysok} ({sysok*100//tot if tot else 0}%)')
A('')
A('> この2つは健全性の目安。管理系が多い母集団で「全遮断が8割超」や')
A('> 「sysadmin 到達が1割未満」なら、セッション切れかフィクスチャ破損を疑うこと。')
A('')
A('| 判定 | 件数 |')
A('|---|---:|')
for k in ('到達','到達(転送)','遮断','判定不能'):
    A(f'| {k} | {v.get(k,0)} |')
A('')
A('## 到達している行')
A('')
A(f'- anon が到達: {len(anon)} 行')
A(f'- general/contributor が到達: {len(low)} 行')
A('')
A('## 台帳の分布')
A('')
A('| 区分 | 行数 |')
A('|---|---:|')
for k in ('P1','P2','P3','P4','P5','整理対象','環境依存','対象外'):
    A(f'| {k} | {pri.get(k,0)} |')
A('')
A('| app | 行数 |')
A('|---|---:|')
for k in sorted(app): A(f'| {k} | {app[k]} |')
A('')
todo=sum(1 for r in L[1:] for c in r if c=='TODO')
empty=sum(1 for r in L[1:] if r[H['dynamic_verified']].strip() in ('','-'))
A(f'- TODO セル: {todo}')
A(f'- dynamic_verified 未記入: {empty}')
open(out,'w',encoding='utf-8').write('\n'.join(lines)+'\n')
print(f'  {out} を書き出した')
