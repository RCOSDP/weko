#!/bin/bash

git ls-files |
while read file ; do
  user=`git blame "$file" |awk '{print $2}'|sort|uniq|wc -l`;
  echo "$user - $file";
done | sort -n

