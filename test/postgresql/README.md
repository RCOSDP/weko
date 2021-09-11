# index.sql

インデックスの公開・非公開・エンバーゴ公開、
OAI-PMHの公開・非公開の全6パターンの組合せの

```
docker-compose exec postgresql pg_dump -U invenio -c -T alembic_version -t index --column-inserts > index.sql
```


