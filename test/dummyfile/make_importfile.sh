#!/bin/bash

if [ $# -ne 3 ]; then
  echo "import.zip generator"
  echo "USAGE: $0 NUMBER_OF_ITEMS FILE_SIZE_KB .POS_INDEX[0](NAME OR AUTO)" 1>&2
  echo "EXAMPLE: $0 100 1000 AUTO" 1>&2
  
  exit 1
fi

N=$1
KB=$2
INDEX_NAME=$3

mkdir data
cp header.tsv data/items.tsv

declare -a array=()
declare -a mimetype=("text/plain" "text/html" "application/pdf" "image/jpeg" "application/json" "image/png" "video/ogg" "audio/ogg" "application/msword" "application/zip")
declare -a indexname=("Index A" "Index A/Index A-1" "Index A/Index A-1/Index A-1-1" "Index A/Index A-1/Index A-1-2(Private)" "Index A/Index A-1/Index A-1-3(Embargo)" "Index A/Index A-2(Private)" "Index A/Index A-2(Private)/Index A-2-1" "Index A/Index A-2(Private)/Index A-2-2(Private)" "Index A/Index A-2(Private)/Index A-2-3(Embargo)" "Index A/Index A-3(Embargo)" "Index A/Index A-3(Embargo)/Index A-3-1" "Index A/Index A-3(Embargo)/Index A-3-2(Private)" "Index A/Index A-3(Embargo)/Index A-3-3(Embargo)" "Index B(Private)" "Index B(Private)/Index B-1" "Index B(Private)/Index B-1/Index B-1-1" "Index B(Private)/Index B-1/Index B-1-2(Private)" "Index B(Private)/Index B-1/Index B-1-3(Embargo)" "Index B(Private)/Index B-2(Private)" "Index B(Private)/Index B-2(Private)/Index B-2-1" "Index B(Private)/Index B-2(Private)/Index B-2-2(Private)" "Index B(Private)/Index B-2(Private)/Index B-2-3(Embargo)" "Index B(Private)/Index B-3(Embargo)" "Index B(Private)/Index B-3(Embargo)/Index B-3-1" "Index B(Private)/Index B-3(Embargo)/Index B-3-2(Private)" "Index B(Private)/Index B-3(Embargo)/Index B-3-3(Embargo)" "Index C" "Index C/Index C-1" "Index C/Index C-1/Index C-1-1" "Index C/Index C-1/Index C-1-2(Private)" "Index C/Index C-1/Index C-1-3(Embargo)" "Index C/Index C-2(Private)" "Index C/Index C-2(Private)/Index C-2-1" "Index C/Index C-2(Private)/Index C-2-2(Private)" "Index C/Index C-2(Private)/Index C-2-3(Embargo)" "Index C/Index C-3(Embargo)" "Index C/Index C-3(Embargo)/Index C-3-1" "Index C/Index C-3(Embargo)/Index C-3-2(Private)" "Index C/Index C-3(Embargo)/Index C-3-3(Embargo)" "Index D(Private)" "Index D(Private)/Index D-1" "Index D(Private)/Index D-1/Index D-1-1" "Index D(Private)/Index D-1/Index D-1-2(Private)" "Index D(Private)/Index D-1/Index D-1-3(Embargo)" "Index D(Private)/Index D-2(Private)" "Index D(Private)/Index D-2(Private)/Index D-2-1" "Index D(Private)/Index D-2(Private)/Index D-2-2(Private)" "Index D(Private)/Index D-2(Private)/Index D-2-3(Embargo)" "Index D(Private)/Index D-3(Embargo)" "Index D(Private)/Index D-3(Embargo)/Index D-3-1" "Index D(Private)/Index D-3(Embargo)/Index D-3-2(Private)" "Index D(Private)/Index D-3(Embargo)/Index D-3-3(Embargo)" "Index E(Embargo)" "Index E(Embargo)/Index E-1" "Index E(Embargo)/Index E-1/Index E-1-1" "Index E(Embargo)/Index E-1/Index E-1-2(Private)" "Index E(Embargo)/Index E-1/Index E-1-3(Embargo)" "Index E(Embargo)/Index E-2(Private)" "Index E(Embargo)/Index E-2(Private)/Index E-2-1" "Index E(Embargo)/Index E-2(Private)/Index E-2-2(Private)" "Index E(Embargo)/Index E-2(Private)/Index E-2-3(Embargo)" "Index E(Embargo)/Index E-3(Embargo)" "Index E(Embargo)/Index E-3(Embargo)/Index E-3-1" "Index E(Embargo)/Index E-3(Embargo)/Index E-3-2(Private)" "Index E(Embargo)/Index E-3(Embargo)/Index E-3-3(Embargo)" "Index F(Embargo)" "Index F(Embargo)/Index F-1" "Index F(Embargo)/Index F-1/Index F-1-1" "Index F(Embargo)/Index F-1/Index F-1-2(Private)" "Index F(Embargo)/Index F-1/Index F-1-3(Embargo)" "Index F(Embargo)/Index F-2(Private)" "Index F(Embargo)/Index F-2(Private)/Index F-2-1" "Index F(Embargo)/Index F-2(Private)/Index F-2-2(Private)" "Index F(Embargo)/Index F-2(Private)/Index F-2-3(Embargo)" "Index F(Embargo)/Index F-3(Embargo)" "Index F(Embargo)/Index F-3(Embargo)/Index F-3-1" "Index F(Embargo)/Index F-3(Embargo)/Index F-3-2(Private)" "Index F(Embargo)/Index F-3(Embargo)/Index F-3-3(Embargo)")

for i in `seq -f '%08g' 1 $N`; do
/bin/mkdir  -p data/file$i
FILENAME=$KB"KB.pdf"
/bin/dd if=/dev/zero of=data/file$i/$FILENAME bs=1024 count=$KB
TITLE="ITEM$i"
PATH="file$i/$FILENAME"
FORMAT="${mimetype[$(($RANDOM % 10))]}"
if [ "$INDEX_NAME" = "AUTO" ] ; then
  INDEX_NAME="${indexname[$(($RANDOM % 78))]}"
fi
echo "\t\t\t$INDEX_NAME\tpublic\t\t\t\t\t\t2021-05-17\t$TITLE\tja\t$TITLE\ten\t\t\t\t\t\t\t\t\t\t\t著者A\tja\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\tdataset\thttp://purl.org/coar/resource_type/c_ddb1\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t$PATH\topen_access\t\t\tpreview\t\t\t$FILENAME\t\t$FORMAT\t\t\tlicense_0\t$FILENAME\t\t\t\t\t\t" >> data/items.tsv;
done
/usr/bin/zip -r import.zip data/
