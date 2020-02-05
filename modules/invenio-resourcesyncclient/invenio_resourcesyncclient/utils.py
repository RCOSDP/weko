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
from resync.client import Client
from resync.client_utils import url_or_file_open, init_logging
from resync.mapper import MapperError
from resync.resource_list_builder import ResourceListBuilder
from resync.sitemap import Sitemap


def read_capability(url):
    """Read capability of an url"""
    s = Sitemap()
    capability = None
    try:
        document = s.parse_xml(url_or_file_open(url))
    except IOError as e:
        raise e
    if 'capability' in document.md:
        capability = document.md['capability']
    return capability


def sync_baseline(map, base_url, dryrun=False):
    """Run resync baseline"""
    client = Client()
    init_logging(verbose=True)
    try:
        # set sitemap_name to specify the only url to sync
        # set mappings to specify the url will
        # be used to validate subitem in resync library
        client.sitemap_name = base_url
        client.dryrun = dryrun
        client.set_mappings(map)
        client.baseline_or_audit()
        return True
    except MapperError:
        # if mapper error then remove one element in url and retry
        paths = map[0].rsplit('/', 1)
        map[0] = paths[0]
        return False
    except Exception as e:
        raise e


def sync_audit(map):
    """Run resync audit"""
    client = Client()
    client.set_mappings(map)
    init_logging(verbose=True)
    src_resource_list = client.find_resource_list()
    rlb = ResourceListBuilder(mapper=client.mapper)
    dst_resource_list = rlb.from_disk()
    # Compare these resource lists respecting any comparison options
    (same, updated, deleted, created) = dst_resource_list.compare(
        src_resource_list)
    return dict(
        same=len(same),updated=len(updated),deleted=len(deleted),created=len(created)
    )

