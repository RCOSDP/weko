#!/bin/sh

# SRP＝R＋U＋((L/100)－5)
# R：修正リビジョンのユニーク数
# U：修正ユーザのユニーク数
# L：モジュールのライン数
# https://gihyo.jp/dev/serial/01/perl-hackers-hub/000803

# sh getdata.sh > output.txt
# awk '{print $1,$2,$3}' output.txt|sort|uniq -c > output2.txt
# awk '{print $3}' output2.txt | awk -F'/' '{print $2}'>output3.txt
# paste output2.txt output3.txt > output4.txt

PRE_IFS=$IFS
IFS=$'\n'

for f in `git ls-files`; do
git --no-pager blame -w -f -l $f
done
IFS=$PRE_IFS

