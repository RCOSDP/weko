# -*- coding: utf-8 -*-
"""out/*.tsv をマージ・整形・採番して 1本の TSV にする。"""
import glob, os, sys

NCOL = 41
HEADER = ['no','module','api_type','app','method','uri','path_params','query_params',
          'body_params','request_content_type','blueprint','endpoint','impl_func',
          'impl_file','impl_line','summary','response','response_content_type',
          'status_codes','exceptions','auth_required','auth_method','oauth_scope','roles',
          'auth_response_variance','restricted_content','data_op','data_target','data_store',
          'side_effects','cache_ratelimit','config_deps','api_version','deprecated','test_file',
          'last_commit','last_commit_date','last_commit_subject','release_tag',
          'category_tags','notes']
assert len(HEADER) == NCOL

def main(outdir, dst):
    rows, seen, dup = [], set(), 0
    for fp in sorted(glob.glob(os.path.join(outdir, '*.tsv'))):
        for i, raw in enumerate(open(fp, encoding='utf-8'), 1):
            raw = raw.rstrip('\n')
            if not raw.strip():
                continue
            c = raw.split('\t')
            if c[0].strip() in ('no', 'No', '#'):     # 誤って書かれたヘッダ行を除去
                continue
            if len(c) < NCOL:
                c += [''] * (NCOL - len(c))
            elif len(c) > NCOL:
                c = c[:NCOL - 1] + [' | '.join(c[NCOL - 1:])]
            c = [x.replace('\t', ' ').replace('\r', '').strip() for x in c]
            key = (c[5], c[4], c[13], c[14])          # uri, method, file, line
            if key in seen:
                dup += 1
                continue
            seen.add(key)
            rows.append(c)
    rows.sort(key=lambda c: (c[1], c[13], int(c[14]) if c[14].isdigit() else 0, c[5], c[4]))
    for n, c in enumerate(rows, 1):
        c[0] = str(n)
    with open(dst, 'w', encoding='utf-8') as f:
        f.write('\t'.join(HEADER) + '\n')
        for c in rows:
            f.write('\t'.join(c) + '\n')
    print(f'merged rows={len(rows)} dropped_dup={dup} -> {dst}')

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
