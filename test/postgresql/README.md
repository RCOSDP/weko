# index.sql

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


