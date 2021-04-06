# -*- coding: utf-8 -*-
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

"""Reverse events stats from ES to DB."""

import json
import click

from elasticsearch_dsl import Search
from invenio_db import db
from invenio_search import current_search_client
from invenio_stats.models import StatsEvents, _generate_id

EVENTS_STATS_INDEX = '*{}*'.format('events-stats-record-view')
# events-stats-search
# events-stats-top-view
# events-stats-record-view
# events-stats-file


def main():
    """Process."""
    print(current_search_client)
    query = Search(
        using=current_search_client,
        index=EVENTS_STATS_INDEX
    ).params(scroll='5m')[0:100]

    response = query.execute().to_dict()
    total = 0
    ret = []
    print(response['hits']['total'])

    while total < response['hits']['total']:
        for item in response['hits']['hits']:
            rtn_data = dict(
                _id=item['_id'],
                _op_type='index',
                _index=item['_index'],
                _type=item['_type'],
                _source=item['_source'],
            )
            ret.append(rtn_data)

        total += len(response['hits']['hits'])
        response = current_search_client.scroll(
            scroll_id=response['_scroll_id'],
            scroll='5m',
        )

    objects = []
    try:
        with db.session.begin_nested():
            for item in ret:
                objects.append(StatsEvents(
                    id=_generate_id(),
                    source_id=item.get("_id"),
                    index=item.get("_index"),
                    type=item.get("_type"),
                    source=json.dumps(item.get("_source")),
                    date=item.get("_source").get("timestamp"),
                ))
            db.session.bulk_save_objects(objects)
        db.session.commit()
    except Exception:
        print('Error while processing event')
        db.session.rollback()

    print('*' * 10)
    print(len(objects))
    click.secho(
        'Finished!',
        fg='green'
    )


if __name__ == '__main__':
    main()
