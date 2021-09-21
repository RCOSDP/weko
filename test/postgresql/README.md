# indexA.sql

1032 インデックス

6種類のインデックス、3階層 x 4

- インデックス公開
- インデックスエンバーゴ期間内
- インデックス非公開
- インデックス公開・OAI-PMH公開
- インデックスエンバーゴ期間内・OAI-PMH公開
- インデックス非公開・OAI-PMH公開


```
docker-compose exec postgresql pg_dump -U invenio -c -T alembic_version -t index --column-inserts > index.sql
```

# indexB.sql

indexA.sql と同じ。

# indexC.sql

indexB.sql から作成した。indexA.sqlと同じ。

```
ORDER=$(awk -F',' '{print $39}' test/postgresql/indexB.sql | sort -n|tail -n 1)
IDX=$(awk -F',' '{print $37}' test/postgresql/indexB.sql | sort -n|tail -n 1)
awk -F',' '{OFS=",";print $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22, $23, $24, $25, $26, $27, $28, $29, $30, $31, $32, $33, $34, $35, $36, $37+'$IDX', $38+'$IDX', $39+'$ORDER', $40, $41, $42, $43, $44, $45, $46, $47, $48, $49, $50, $51, $52, $53, $54, $55, $56, $57, $58, $59, $60, $61, $62, $63, $64, $65, $66, $67, $68, $69, $70, $71, $72, $73, $74, $75, $76, $77, $78,$79,$80,$81,$82}' test/postgresql/indexB.sql|grep '^INSERT'|sed 's/'$IDX'/0/g'|sed 's/;,*/;/g'|sed 's/Index A/Index B/g' > test/postgresql/indexC.sql
```


