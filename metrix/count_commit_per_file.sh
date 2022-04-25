#!/bin/bash

git ls-files |
while read file ; do
  commits=`git log --oneline -- $file | wc -l`;
  echo "$commits - $file";
done | sort -n

