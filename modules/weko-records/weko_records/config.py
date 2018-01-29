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

"""weko records config file."""

WEKO_RECORDS_PERMISSION_FACTORY = 'weko_records.permissions.permission_factory'

OAISERVER_METADATA_FORMATS = {
    'junii2': {
        'namespace': 'http://irdb.nii.ac.jp/oai',
        'schema': 'http://irdb.nii.ac.jp/oai/junii2-3-1.xsd',
        'serializer': 'weko_records.serializers.oaipmh_junii2_v2',
    },
    'jpcoar': {
        'namespace': 'https://irdb.nii.ac.jp/schema/jpcoar/1.0/',
        'schema': 'https://irdb.nii.ac.jp/schema/jpcoar/1.0/jpcoar_scm.xsd',
        'serializer': 'weko_records.serializers.oaipmh_jpcoar_v1',
    }
}
