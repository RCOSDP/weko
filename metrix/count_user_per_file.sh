#!/bin/bash

git ls-files |
while read file ; do
  user=`git log --oneline --pretty=format:"%an" -- $file |sort| uniq| wc -l`;
  echo "$user - $file";
done | sort -n

