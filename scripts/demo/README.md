# item_type2.sql

## 作成

```
docker-compose exec postgresql pg_dump -U invenio -c -T alembic_version -t item_type -t oaiserver_schema -t item_type_property -t item_type_name -t item_type_mapping --column-inserts > item_type2.sql
```

```
kubectl exec -n weko3pg -it weko3pg-cluster-0 -c postgres -- pg_dump -U invenio -c -T alembic_version -t item_type -t oaiserver_schema -t item_type_property -t item_type_name -t item_type_mapping --column-inserts tsukuba_repo_nii_ac_jp > item_type.sql
```

## 説明

