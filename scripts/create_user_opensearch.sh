

curl -ku admin:${OPENSEARCH_INITIAL_ADMIN_PASSWORD} -XPUT https://localhost:9200/_plugins/_security/api/user/${INVENIO_OPENSEARCH_USER} -H 'Content-Type:application/json' -d '{"password":"'${INVENIO_OPENSEARCH_PASS}'","backend_roles":["admin"]}'

