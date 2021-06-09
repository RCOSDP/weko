#!/bin/bash

if [ $# -ne 2 ]; then
  echo "import.zip generator"
  echo "USAGE: $0 NUMBER_OF_ITEMS FILE_SIZE_MB" 1>&2
  exit 1
fi

N=$1
MB=$2
mkdir data
cp header.tsv data/items.tsv
for i in `seq -f '%08g' 1 $N`; do
/bin/mkdir  -p data/file$i
FILENAME=$MB"MB.pdf"
/bin/dd if=/dev/zero of=data/file$i/$FILENAME bs=1048576 count=$MB
TITLE="ITEM$i"
PATH="file$i/$FILENAME"
echo "\t\t\tIndex A\tpublic\t\t\t\t\t\t2021-05-17\t$TITLE\tja\t$TITLE\ten\t\t\t\t\t\t\t\t\t\t\t著者A\tja\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\tdataset\thttp://purl.org/coar/resource_type/c_ddb1\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t$PATH\topen_access\t\t\tpreview\t\t\t$FILENAME\t\t\t\t\tlicense_0\t$FILENAME\t\t\t\t\t\t" >> data/items.tsv;
done
/usr/bin/zip -r import.zip data/
