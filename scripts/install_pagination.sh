# Delete existing invenio-search-js inside web container
docker-compose exec web rm -rf /home/invenio/.virtualenvs/invenio/var/instance/static/node_modules/invenio-search-js/

# Clone the updated invenio-search-js for search-after-pagination
docker-compose exec web git clone --branch feature/changePaginationForSearchAfterUse https://github.com/RCOSDP/invenio-search-js.git /home/invenio/.virtualenvs/invenio/var/instance/static/node_modules/invenio-search-js
# Collect and build assets and restart web container
docker-compose exec web invenio collect -v && docker-compose exec web invenio assets build
docker-compose restart web
