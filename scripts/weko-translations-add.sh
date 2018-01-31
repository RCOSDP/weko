#!/usr/bin/env bash
# shellcheck disable=SC2103,SC2102
#
# This file is part of WEKO3.
# Copyright (C) 2017 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# WEKO3 is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with WEKO3; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.

# translations-add-begin
source=./scripts/translations
target=/home/invenio/.virtualenvs/invenio/lib/python3.5/site-packages

while read translations ; do
    echo $source/$translations/translations/ja $(docker-compose ps -q web):$target/$translations/translations/
    docker cp $source/$translations/translations/ja $(docker-compose ps -q web):$target/$translations/translations/
done << END 
invenio_access
invenio_accounts
invenio_i18n
invenio_pidstore
invenio_records
invenio_records_rest
invenio_theme
END
# translations-add-end
