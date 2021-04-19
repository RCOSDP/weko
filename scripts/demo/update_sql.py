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

import concurrent.futures
import json
import logging
import uuid
from datetime import datetime
from functools import wraps
from time import mktime

import click
from dateutil.parser import parse as dateutil_parse
from invenio_db import db
from invenio_stats.contrib.event_builders import build_search_unique_id
from invenio_stats.models import StatsEvents
from invenio_stats.proxies import current_stats
from pytz import utc
from sqlalchemy import and_, asc
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.local import LocalProxy

EVENTS = [
    'events-stats-search',
    'events-stats-top-view',
    'events-stats-record-view',
    'events-stats-file-download',
    'events-stats-file-preview']


def _verify_date(ctx, param, value):
    """Verify datetime input."""
    if value:
        dateutil_parse(value)
        return value


def lazy_result(f):
    """Decorate function to return LazyProxy."""
    @wraps(f)
    def decorated(ctx, param, value):
        return LocalProxy(lambda: f(ctx, param, value))

    return decorated


@lazy_result
def _validate_event_type(ctx, param, value):
    """Verify input events."""
    invalid_values = set(value) - set(current_stats.enabled_events)
    if invalid_values:
        raise click.BadParameter(
            'Invalid event type(s): {}. Valid values: {}'.format(
                ', '.join(invalid_values),
                ', '.join(current_stats.enabled_events)))
    return value


def build_file_unique_id(doc):
    """Build file unique identifier."""
    key = '{0}_{1}_{2}_{3}'.format(
        doc['bucket_id'],
        doc['file_id'],
        doc['remote_addr'],
        doc['unique_session_id']
    )
    doc['unique_id'] = str(uuid.uuid3(uuid.NAMESPACE_DNS, key))

    return doc


def build_top_unique_id(doc):
    """Build top unique identifier."""
    key = '{0}_{1}_{2}_{3}'.format(
        doc['site_license_name'],
        doc['remote_addr'],
        doc['unique_session_id'],
        doc['visitor_id'])

    doc['unique_id'] = str(uuid.uuid3(uuid.NAMESPACE_DNS, key))

    return doc


def build_record_unique_id(doc):
    """Build record unique identifier."""
    key = '{0}_{1}_{2}_{3}_{4}'.format(
        doc['pid_type'],
        doc['pid_value'],
        doc['remote_addr'],
        doc['unique_session_id'],
        doc['visitor_id'])
    doc['unique_id'] = str(uuid.uuid3(uuid.NAMESPACE_DNS, key))

    return doc


def build_events(event_name, start_date, end_date):
    """Build a celery-task event."""
    logging.basicConfig(
        level=logging.DEBUG,
        filename="message-" + event_name + ".log",
        filemode="w",
        format="%(asctime)-15s %(levelname)-5s %(message)s")

    try:
        items = dict()
        deletes = []
        mappers = []
        errors = []
        events = []

        logging.info(event_name)
        logging.info('*' * 60)
        with db.session.no_autoflush:
            events = StatsEvents.query.filter(
                and_(
                    StatsEvents.index.like('%{}%'.format(event_name)),
                    StatsEvents.date >= start_date,
                    StatsEvents.date <= end_date,
                )
            ).order_by(
                asc(StatsEvents.date)
            ).all()

        with db.session.begin_nested():
            for event in events:
                logging.info('EVENT ID: {}'.format(event.id))
                try:
                    _source_id = event.source_id
                    suffix = _source_id.split('-')[-1]
                    source_id = '-'.join(_source_id.split('-')[:-1])
                    if source_id:
                        datetime_object = datetime.strptime(
                            source_id,
                            r"%Y-%m-%dT%H:%M:%S")
                        datetime_object.replace(microsecond=0).isoformat()
                        timestamp = mktime(
                            utc.localize(datetime_object).utctimetuple())
                        datetime_object = datetime_object.fromtimestamp(
                            timestamp // 30 * 30
                        )

                    source_id = '{0}-{1}'.format(
                        datetime_object.isoformat(),
                        suffix)
                    logging.info(
                        'Updated source_id: {} - {}'.format(
                            _source_id,
                            source_id))

                    # Update unique_id
                    doc = json.loads(event.source)
                    _unique_id = doc.get('unique_id')

                    if event_name in ['events-stats-file-download',
                                      'events-stats-file-preview']:
                        doc = build_file_unique_id(doc)
                    elif event_name == 'events-stats-search':
                        doc = build_search_unique_id(doc)
                    elif event_name == 'events-stats-top-view':
                        doc = build_top_unique_id(doc)
                    elif event_name == 'events-stats-record-view':
                        doc = build_record_unique_id(doc)
                    logging.info(
                        'Update unique_id: {} - {}'.format(
                            _unique_id,
                            doc.get('unique_id'))
                    )

                    if items.get(source_id):
                        deletes.append(items[source_id].get('id'))
                    items[source_id] = dict(id=event.id, source=doc)
                    logging.info('-' * 30)
                except Exception as ex:
                    logging.error(ex)
                    errors.append(event.id)
                    continue

        for item in items:
            mappers.append({
                'id': items[item].get('id'),
                'source_id': item,
                'source': json.dumps(items[item].get('source'))
            })

        db.session.bulk_update_mappings(StatsEvents, mappers)
        for event in deletes:
            db.session.delete(event)
        db.session.commit()

        logging.info('*' * 60)
        logging.info('Updated: {}'.format(len(mappers)))
        logging.info('Removed: {}'.format(len(deletes)))
        logging.info('Errors: {}'.format(len(errors)))
        print('{} - finished!'.format(event_name))
    except SQLAlchemyError as err:
        logging.error(err)
        db.session.rollback()


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

    args = ([start_date for _ in events], [end_date for _ in events])
    with concurrent.futures.ProcessPoolExecutor(max_workers=10) \
            as executor:
        executor.map(build_events, events, *args)


if __name__ == '__main__':
    """Main context."""
    main()
