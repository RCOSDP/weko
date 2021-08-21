#!/bin/bash


# head -n 5 item_type.tsv > header.tsv
# head -n 6 item.tsv |tail -n1|gsed 's/\t/\\t/g'|pbcopy


if [ $# -ne 3 ]; then
  echo "import.zip generator"
  echo "USAGE: $0 NUMBER_OF_ITEMS FILE_SIZE_KB .POS_INDEX[0](NAME OR RND OR SEQ)" 1>&2
  echo "EXAMPLE: $0 100 1000 RND" 1>&2

  exit 1
fi

N=$1
KB=$2
WAY=$3

MAX_IDX_INDEX_NAME=78
MAX_IDX_MIMETYPE=10
MAX_IDX_RESOURCE_TYPE=47

mkdir data
cp header.tsv data/items.tsv

declare -a array=()
declare -a mimetype=("text/plain" "text/html" "application/pdf" "image/jpeg" "application/json" "image/png" "video/ogg" "audio/ogg" "application/msword" "application/zip")
declare -a indexname=("Index A" "Index A/Index A-1" "Index A/Index A-1/Index A-1-1" "Index A/Index A-1/Index A-1-2(Private)" "Index A/Index A-1/Index A-1-3(Embargo)" "Index A/Index A-2(Private)" "Index A/Index A-2(Private)/Index A-2-1" "Index A/Index A-2(Private)/Index A-2-2(Private)" "Index A/Index A-2(Private)/Index A-2-3(Embargo)" "Index A/Index A-3(Embargo)" "Index A/Index A-3(Embargo)/Index A-3-1" "Index A/Index A-3(Embargo)/Index A-3-2(Private)" "Index A/Index A-3(Embargo)/Index A-3-3(Embargo)" "Index B(Private)" "Index B(Private)/Index B-1" "Index B(Private)/Index B-1/Index B-1-1" "Index B(Private)/Index B-1/Index B-1-2(Private)" "Index B(Private)/Index B-1/Index B-1-3(Embargo)" "Index B(Private)/Index B-2(Private)" "Index B(Private)/Index B-2(Private)/Index B-2-1" "Index B(Private)/Index B-2(Private)/Index B-2-2(Private)" "Index B(Private)/Index B-2(Private)/Index B-2-3(Embargo)" "Index B(Private)/Index B-3(Embargo)" "Index B(Private)/Index B-3(Embargo)/Index B-3-1" "Index B(Private)/Index B-3(Embargo)/Index B-3-2(Private)" "Index B(Private)/Index B-3(Embargo)/Index B-3-3(Embargo)" "Index C" "Index C/Index C-1" "Index C/Index C-1/Index C-1-1" "Index C/Index C-1/Index C-1-2(Private)" "Index C/Index C-1/Index C-1-3(Embargo)" "Index C/Index C-2(Private)" "Index C/Index C-2(Private)/Index C-2-1" "Index C/Index C-2(Private)/Index C-2-2(Private)" "Index C/Index C-2(Private)/Index C-2-3(Embargo)" "Index C/Index C-3(Embargo)" "Index C/Index C-3(Embargo)/Index C-3-1" "Index C/Index C-3(Embargo)/Index C-3-2(Private)" "Index C/Index C-3(Embargo)/Index C-3-3(Embargo)" "Index D(Private)" "Index D(Private)/Index D-1" "Index D(Private)/Index D-1/Index D-1-1" "Index D(Private)/Index D-1/Index D-1-2(Private)" "Index D(Private)/Index D-1/Index D-1-3(Embargo)" "Index D(Private)/Index D-2(Private)" "Index D(Private)/Index D-2(Private)/Index D-2-1" "Index D(Private)/Index D-2(Private)/Index D-2-2(Private)" "Index D(Private)/Index D-2(Private)/Index D-2-3(Embargo)" "Index D(Private)/Index D-3(Embargo)" "Index D(Private)/Index D-3(Embargo)/Index D-3-1" "Index D(Private)/Index D-3(Embargo)/Index D-3-2(Private)" "Index D(Private)/Index D-3(Embargo)/Index D-3-3(Embargo)" "Index E(Embargo)" "Index E(Embargo)/Index E-1" "Index E(Embargo)/Index E-1/Index E-1-1" "Index E(Embargo)/Index E-1/Index E-1-2(Private)" "Index E(Embargo)/Index E-1/Index E-1-3(Embargo)" "Index E(Embargo)/Index E-2(Private)" "Index E(Embargo)/Index E-2(Private)/Index E-2-1" "Index E(Embargo)/Index E-2(Private)/Index E-2-2(Private)" "Index E(Embargo)/Index E-2(Private)/Index E-2-3(Embargo)" "Index E(Embargo)/Index E-3(Embargo)" "Index E(Embargo)/Index E-3(Embargo)/Index E-3-1" "Index E(Embargo)/Index E-3(Embargo)/Index E-3-2(Private)" "Index E(Embargo)/Index E-3(Embargo)/Index E-3-3(Embargo)" "Index F(Embargo)" "Index F(Embargo)/Index F-1" "Index F(Embargo)/Index F-1/Index F-1-1" "Index F(Embargo)/Index F-1/Index F-1-2(Private)" "Index F(Embargo)/Index F-1/Index F-1-3(Embargo)" "Index F(Embargo)/Index F-2(Private)" "Index F(Embargo)/Index F-2(Private)/Index F-2-1" "Index F(Embargo)/Index F-2(Private)/Index F-2-2(Private)" "Index F(Embargo)/Index F-2(Private)/Index F-2-3(Embargo)" "Index F(Embargo)/Index F-3(Embargo)" "Index F(Embargo)/Index F-3(Embargo)/Index F-3-1" "Index F(Embargo)/Index F-3(Embargo)/Index F-3-2(Private)" "Index F(Embargo)/Index F-3(Embargo)/Index F-3-3(Embargo)")
declare -a resourcetype=("conference paper" "data paper" "departmental bulletin paper" "editorial" "journal article" "newspaper" "periodical" "review article" "software paper" "article" "book" "book part" "cartographic material" "map" "conference object" "conference proceedings" "conference poster" "dataset" "interview" "image" "still image" "moving image" "video" "lecture" "patent" "internal report" "report" "research report" "technical report" "policy report" "report part" "working paper" "data management plan" "sound" "thesis" "bachelor thesis" "master thesis" "doctoral thesis" "interactive resource" "learning object" "manuscript" "musical notation" "research proposal" "software" "technical documentation" "workflow" "other")
declare -a resourcetypeidentifier=("c_5794" "c_beb9" "c_6501" "c_b239" "c_6501" "c_2fe3" "c_2659" "c_dcae04bc" "c_7bab" "c_6501" "c_2f33" "c_3248" "c_12cc" "c_12cd" "c_c94f" "c_f744" "c_6670" "c_ddb1" "c_26e4" "c_c513" "c_ecc8" "c_8a7e" "c_12ce" "c_8544" "c_15cd" "c_18ww" "c_93fc" "c_18ws" "c_18gh" "c_186u" "c_ba1f" "c_8042" "c_ab20" "c_18cc" "c_46ec" "c_7a1f" "c_bdcc" "c_db06" "c_e9a0" "c_e059" "c_0040" "c_18cw" "c_baaf" "c_5ce6" "c_71bd" "c_393c" "c_1843")


IDX_MIMETYPE=0
IDX_INDEX_NAME=0
IDX_RESOURCE_TYPE=0

MAIL=wekosoftware@nii.ac.jp

for i in `seq -f '%08g' 1 $N`; do
  /bin/mkdir  -p data/file$i
  FILENAME=$KB"KB.pdf"
  /bin/dd if=/dev/zero of=data/file$i/$FILENAME bs=1024 count=$KB
  TITLE="ITEM$i"
  PATH="file$i/$FILENAME"

  if [ "$WAY" = "RND" -o "$WAY" = "SEQ" ]; then
    if [ "$WAY" = "RND" ] ; then
      IDX_MIMETYPE="$(($RANDOM % 10))"
      IDX_INDEX_NAME="$(($RANDOM % 78))"
      IDX_RESOURCE_TYPE="$(($RANDOM % 47))"
    elif [ "$WAY" = "SEQ" ] ; then
      IDX_MIMETYPE=$(($IDX_MIMETYPE+1))
      IDX_INDEX_NAME=$(($IDX_INDEX_NAME+1))
      IDX_RESOURCE_TYPE=$(($IDX_RESOURCE_TYPE+1))
      if [ $IDX_MIMETYPE -ge $MAX_IDX_MIMETYPE ]; then
        IDX_MIMETYPE=0
      fi
      if [ $IDX_INDEX_NAME -ge $MAX_IDX_INDEX_NAME ]; then
        IDX_INDEX_NAME=0
      fi
      if [ $IDX_RESOURCE_TYPE -ge $MAX_IDX_RESOURCE_TYPE ]; then
        IDX_RESOURCE_TYPE=0
      fi
    fi
    FORMAT="${mimetype[$IDX_MIMETYPE]}"
    INDEX_NAME="${indexname[$IDX_INDEX_NAME]}"
    RESOURCE_TYPE="${resourcetype[$IDX_RESOURCE_TYPE]}"
    RESOURCE_TYPE_SUFFIX=${resourcetypeidentifier[$IDX_RESOURCE_TYPE]}
    RESOURCE_TYPE_IDENTIFIER="http://purl.org/coar/resource_type/${RESOURCE_TYPE_SUFFIX}"
  else
    FORMAT="${mimetype[$((IDX_MIMETYPE))]}"
    INDEX_NAME=$WAY
    RESOURCE_TYPE="${resourcetype[$IDX_RESOURCE_TYPE]}"
    RESOURCE_TYPE_SUFFIX=${resourcetypeidentifier[$IDX_RESOURCE_TYPE]}
    RESOURCE_TYPE_IDENTIFIER="http://purl.org/coar/resource_type/${RESOURCE_TYPE_SUFFIX}"
  fi
  #

  # echo "\t\t\t$INDEX_NAME\tpublic\t$MAIL\t\t\t\t\t2021-04-29\t$TITLE\tja\t$TITLE\ten\tその他のタイトル\tja\tOther Title\ten\t000000012146438X\tISNI\thttp://isni.org/isni/000000012146438X\tえぬあいあい\tja\tNII\ten\t別名\tja\tAnother Name\ten\tmhaya@nii.ac.jp\tジョウホウ, タロウ\tja-Kana\t情報, 太郎\tja\tJoho, Taro\ten\tジョウホウ\tja-Kana\t情報\tja\tJoho\ten\tタロウ\tja-Kana\t太郎\tja\tTaro\ten\t0000-0002-1825-0097\tORCID\thttps://orcid.org/\t\t\t\t\t\t\t\t\t情報, 次郎\tja\tJoho, Jiro\ten\t情報\tja\tJoho\ten\t次郎\tja\tJiro\ten\t\t\t\t\t\t\t\t\t\t\t\t\t\tDataCollector\t\t\t\t\t0000-0001-2345-6789\tORCID\thttps://orcid.org/\topen access\thttp://purl.org/coar/access_right/c_abf2\tUnknown\tja\thttps://creativecommons.org/licenses/by/4.0/deed.en\tCreative Commons Attribution 4.0 International\t0000-0001-2345-6789\tORCID\thttps://orcid.org/\tja\tXXXX\tja\tOther\thttp://localhsot/\txxxx\tああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああ\tja\tOther\tja\t出版社\ten\tPublisher\tAccepted\t2021-04-28\tAvailable\t2021-05-11\tjpn\tdataset\thttp://purl.org/coar/resource_type/c_ddb1\t1.0\tAO\thttp://purl.org/coar/version/c_b1a7d7d4d402bcce\tDOI\txxx/yyy\t\t\thasVersion\tarXiv\txxx/yyy\tja\txxxx\tja\t時間的範囲\t111\t222\t222\t111\t日本\t111\t111\tCrossref Funder\txxxxx\tja\txxxx\thttp://localhost\txxxxx\tja\tyyyyy\tISSN\txxxxx\tja\t収録物名\t1\t2\t14\t1\t10\t2021-05-05\tIssued\t33\t34\t23\t1\t2\t雑誌名\tja\tZassi\ten\txxxxxx\t学位名\tja\t2021-04-27\txxxx\tkakenhi\t国立情報学研究所\tja\tNational Institute of Informatics\ten\t会議名\tja\tconference\ten\t1\t主催機関\tja\t3\t1\t1\t2021\t3\t2\t2021\ten\t開催会場\tja\t開催地\tja\tJPN\t$PATH\topen_access\t\t\tpreview\tAccepted\t2021-04-27\t$FILENAME\t975 Kb\t$FORAMT\t\t\tlicense_0\t$FILENAME\tother\thttps://localhost:8443/record/2/files/sample.pdf\t1.0\tja\t見出し１\t見出し２\ten\tHeadline1\tHeadline2" >> data/items.tsv;
  #index SEQ/RND
  # echo -e "\t\t\t$INDEX_NAME\tpublic\t$MAIL\t\t\t\tKeep\t2021-07-13\t$TITLE\tja\t$TITLE\ten\tAlternative Title\tja\tAlternative Title\tja\t\t\t\t\t\t\t\t$MAIL\t情報, 太郎\tja\tジョウホウ, タロウ\tja-Kana\tJoho, Taro\ten\t情報\tja\tジョウホウ\tja-Kana\tJoho\ten\t太郎\tja\tタロウ\tja-Kana\tTaro\ten\t4\tWEKO\t\txxxxxxx\tORCID\thttps://orcid.org/\txxxxxxx\tCiNii\thttps://ci.nii.ac.jp/\tzzzzzzz\tKAKEN2\thttps://kaken.nii.ac.jp/\t\t\t\t\t\t\t\t$MAIL\t情報, 太郎\tja\tジョウホウ, タロウ\tja-Kana\tJoho, Taro\ten\t情報\tja\tジョウホウ\tja-Kana\tJoho\ten\t太郎\tja\tタロウ\tja-Kana\tTaro\ten\txxxxxxx\tORCID\thttps://orcid.org/\txxxxxxx\tCiNii\thttps://ci.nii.ac.jp/\tzzzzzzz\tKAKEN2\thttps://kaken.nii.ac.jp/\t\t\t\t\t\t\t\t$MAIL\t情報, 太郎\tja\tジョウホウ, タロウ\tja-Kana\tJoho, Taro\ten\t情報\tja\tジョウホウ\tja-Kana\tJoho\ten\t太郎\tja\tタロウ\tja-Kana\tTaro\ten\txxxxxxx\tORCID\thttps://orcid.org/\txxxxxxx\tCiNii\thttps://ci.nii.ac.jp/\tzzzzzzz\tKAKEN2\thttps://kaken.nii.ac.jp/\t\t\t\t\t\t\t\t$MAIL\t情報, 太郎\tja\tジョウホウ, タロウ\tja-Kana\tJoho, Taro\ten\tContactPerson\t情報\tja\tジョウホウ\tja-Kana\tJoho\ten\t太郎\tja\tタロウ\tja-Kana\tTaro\ten\txxxxxxx\tORCID\thttps://orcid.org/\txxxxxxx\tCiNii\thttps://ci.nii.ac.jp/\txxxxxxx\tKAKEN2\thttps://kaken.nii.ac.jp/\topen access\thttp://purl.org/coar/access_right/c_abf2\tUnknown\tja\thttp://localhost\tRights Information\txxxxxx\tORCID\thttps://orcid.org/\tja\tRight Holder Name\tja\tOther\thttp://localhost/\tSibject1\tDescription<br/>Description<br/>Description\ten\tAbstract\t概要<br/>概要<br/>概要\tja\tAbstract\tja\tPublisher\tAvailable\t2021-06-30\tjpn\t$RESOURCE_TYPE\t$RESOURCE_TYPE_IDENTIFIER\tVersion\tAO\thttp://purl.org/coar/version/c_b1a7d7d4d402bcce\tURI\thttp://localhost\t\t\tisVersionOf\tarXiv\txxxxx\tja\tRelated Title\tja\tTemporal\t\t\t\t\t日本\t\t\tISNI\thttp://xxx\tja\tFunder Name\tAward URI\tAward Number\tja\tAward Title\tISSN\txxxx-xxxx-xxxx\tja\tSource Title\t1\t111\t12\t1\t3\t2021-07-06\tIssued\t11\t10\t10\t1\t1\tTitle\tja\t111\tDegree Name\tja\t2021-06-30\txxxxxx\tkakenhi\tDegree Grantor Name\tja\tConference Name\tja\t1\tSponsor\tja\t2020/12/11\t1\t12\t2000\t1\t12\t2020\tja\tConference Venue\tja\tConference Place\tja\tJPN\t$PATH\topen_access\tAvailable\t2021-07-12\t\t\t\t$FILENAME\t$KB KB\t$FORMAT\t\t\t\t\t\t\t\tja\tBanner Headline\tSubheading\ten\tBanner Headline\tSubheding" >> data/items.tsv;
  #index lock
  echo -e "\t\t\t$INDEX_NAME\tpublic\t$MAIL\t\t\t\tKeep\t2021-07-13\t$TITLE\tja\t$TITLE\ten\tAlternative Title\tja\tAlternative Title\tja\t\t\t\t\t\t\t\t$MAIL\t情報, 太郎\tja\tジョウホウ, タロウ\tja-Kana\tJoho, Taro\ten\t情報\tja\tジョウホウ\tja-Kana\tJoho\ten\t太郎\tja\tタロウ\tja-Kana\tTaro\ten\t4\tWEKO\t\txxxxxxx\tORCID\thttps://orcid.org/\txxxxxxx\tCiNii\thttps://ci.nii.ac.jp/\tzzzzzzz\tKAKEN2\thttps://kaken.nii.ac.jp/\t\t\t\t\t\t\t\t$MAIL\t情報, 太郎\tja\tジョウホウ, タロウ\tja-Kana\tJoho, Taro\ten\t情報\tja\tジョウホウ\tja-Kana\tJoho\ten\t太郎\tja\tタロウ\tja-Kana\tTaro\ten\txxxxxxx\tORCID\thttps://orcid.org/\txxxxxxx\tCiNii\thttps://ci.nii.ac.jp/\tzzzzzzz\tKAKEN2\thttps://kaken.nii.ac.jp/\t\t\t\t\t\t\t\t$MAIL\t情報, 太郎\tja\tジョウホウ, タロウ\tja-Kana\tJoho, Taro\ten\t情報\tja\tジョウホウ\tja-Kana\tJoho\ten\t太郎\tja\tタロウ\tja-Kana\tTaro\ten\txxxxxxx\tORCID\thttps://orcid.org/\txxxxxxx\tCiNii\thttps://ci.nii.ac.jp/\tzzzzzzz\tKAKEN2\thttps://kaken.nii.ac.jp/\t\t\t\t\t\t\t\t$MAIL\t情報, 太郎\tja\tジョウホウ, タロウ\tja-Kana\tJoho, Taro\ten\tContactPerson\t情報\tja\tジョウホウ\tja-Kana\tJoho\ten\t太郎\tja\tタロウ\tja-Kana\tTaro\ten\txxxxxxx\tORCID\thttps://orcid.org/\txxxxxxx\tCiNii\thttps://ci.nii.ac.jp/\txxxxxxx\tKAKEN2\thttps://kaken.nii.ac.jp/\topen access\thttp://purl.org/coar/access_right/c_abf2\tUnknown\tja\thttp://localhost\tRights Information\txxxxxx\tORCID\thttps://orcid.org/\tja\tRight Holder Name\tja\tOther\thttp://localhost/\tSibject1\tDescription<br/>Description<br/>Description\ten\tAbstract\t概要<br/>概要<br/>概要\tja\tAbstract\tja\tPublisher\tAvailable\t2021-06-30\tjpn\t$RESOURCE_TYPE\t$RESOURCE_TYPE_IDENTIFIER\tVersion\tAO\thttp://purl.org/coar/version/c_b1a7d7d4d402bcce\tURI\thttp://localhost\t\t\tisVersionOf\tarXiv\txxxxx\tja\tRelated Title\tja\tTemporal\t\t\t\t\t日本\t\t\tISNI\thttp://xxx\tja\tFunder Name\tAward URI\tAward Number\tja\tAward Title\tISSN\txxxx-xxxx-xxxx\tja\tSource Title\t1\t111\t12\t1\t3\t2021-07-06\tIssued\t11\t10\t10\t1\t1\tTitle\tja\t111\tDegree Name\tja\t2021-06-30\txxxxxx\tkakenhi\tDegree Grantor Name\tja\tConference Name\tja\t1\tSponsor\tja\t2020/12/11\t1\t12\t2000\t1\t12\t2020\tja\tConference Venue\tja\tConference Place\tja\tJPN\t$PATH\topen_access\tAvailable\t2021-07-12\t\t\t\t$FILENAME\t$KB KB\t$FORMAT\t\t\t\t\t\t\t\tja\tBanner Headline\tSubheading\ten\tBanner Headline\tSubheding" >> data/items.tsv;

done
/usr/bin/zip -r import.zip data/
