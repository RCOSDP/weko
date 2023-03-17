#!/bin/bash

git ls-files modules/ |
while read file ; do
  output=`git blame -e "$file" |awk '{print $2" FILE"}'`;
  f=`echo $file|awk -F'/' '{print $2}'`
  echo "${output//FILE/$f}"
done

