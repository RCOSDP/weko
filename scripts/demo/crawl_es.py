#!/usr/bin/python3
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

"""WEKO3 module docstring."""

import json
import logging
import traceback

import click
from dateutil.parser import parse as dateutil_parse
from elasticsearch_dsl import Search
from invenio_db import db
from invenio_search import current_search_client
from invenio_stats.cli import _validate_event_type
from invenio_stats.models import StatsEvents, _generate_id
from invenio_stats.proxies import current_stats
from sqlalchemy.exc import SQLAlchemyError

EVENTS = [
    'events-stats-search',
    'events-stats-top-view',
    'events-stats-record-view',
    'events-stats-file-download',
    'events-stats-file-preview']


def crawl(event_name, start_date, end_date):
    """Crawl ES events."""
    try:
        print(event_name)
        print('*' * 60)
        time_range = {}
        time_range['gte'] = start_date
        time_range['lte'] = end_date
        query = Search(
            using=current_search_client,
            index='*{}*'.format(event_name)
        ).filter(
            'range',
            **{'timestamp': time_range}
        ).params(scroll='5m')[0:100]

        response = query.execute().to_dict()
        total = 0
        ret = []
        print('Process: {}'.format(response['hits']['total']))

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
        except SQLAlchemyError as err:
            logging.error(err)
            db.session.rollback()

        print('-' * 10)
        print('Results: {}'.format(len(objects)))
    except Exception:
        traceback.print_exc()


def _verify_date(ctx, param, value):
    """Verify datetime input."""
    if value:
        dateutil_parse(value)
        return dateutil_parse(value).isoformat()


# Read parameters.
@click.command()
@click.argument(
    'start_date',
    nargs=1,
    default=None,
    callback=_verify_date
)
@click.argument(
    'end_date',
    nargs=1,
    default=None,
    callback=_verify_date
)
@click.argument(
    'event_types',
    nargs=-1,
    callback=_validate_event_type
)
def main(event_types, start_date, end_date):
    """Application's main function."""
    event_types = event_types or list(current_stats.enabled_events)
    events = []
    for type in event_types:
        for idx in EVENTS:
            if type in idx:
                events.append(idx)

    for event in events:
        crawl(event, start_date, end_date)
    print('Done!')


if __name__ == '__main__':
    """Main context."""
    main()
