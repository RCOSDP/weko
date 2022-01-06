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

"""Module tests."""

from datetime import datetime

import dateutil.tz
from flask import Flask
from invenio_records_rest.schemas.json import RecordSchemaJSONV1

from weko_records import WekoRecords
from weko_records.serializers.entry import WekoFeedEntry
from weko_records.serializers.feed import WekoFeedGenerator
from weko_records.serializers.rss import RssSerializer


def test_version():
    """Test version import."""
    from weko_records import __version__
    assert __version__


def test_init():
    """Test extension initialization."""
    app = Flask('testapp')
    ext = WekoRecords(app)
    assert 'weko-records' in app.extensions

    app = Flask('testapp')
    ext = WekoRecords()
    assert 'weko-records' not in app.extensions
    ext.init_app(app)
    assert 'weko-records' in app.extensions


def test_feed_entry(app, db):
    rss_v1 = RssSerializer(RecordSchemaJSONV1)

    entry = WekoFeedEntry()

    entry.guid('test')
    entry.title('test')
    entry.content(
        content='test',
        lang='en',
        type='xhtml'
    )
    entry.author({
        'name': 'test',
        'lang': 'en',
        'email': 'email',
        'uri': 'test'
    })
    entry.__atom_link = [{
        'rel': 'test',
        'type': 'test',
        'hreflang': 'en',
        'title': 'test',
        'length': 'test'
    }]

    entry.contributor({
        'name': 'test',
        'email': 'test',
        'uri': 'test'
    })
    entry.atom_entry()

    entry.rss_entry()

    entry.itemUrl('test')
    entry.jpcoar_entry()


def test_weko_feed_generator(app, db):
    fg = WekoFeedGenerator()
    # fg.add_entry()

    fg.id('1')
    fg.title('test')
    fg.updated(datetime.now(dateutil.tz.tzutc()))
    fg.contributor({
        'name': 'test',
        'email': 'test',
        'uri': 'test'
    })

    fg.atom_str(pretty=True)

    fg.link({
        'href': 'test',
        'rel': 'about',
        'type': 'test',
        'hreflang': 'en',
        'title': 'test',
        'length': 'test'
    })
    fg.image(
        url='test',
        title='test',
        width='test',
        height='test'
    )
    fg.items(['test'])
    fg._create_rss()

    fg.author({
        'name': 'John Doe',
        'email': 'jdoe@example.com'})
    fg.jpcoar_str(pretty=True)

    fg.category({
        'term': 'test',
        'scheme': 'test',
        'label': 'test'
    })

    fg.textInput(
        title='test',
        description='test',
        name='test',
        link='test'
    )
