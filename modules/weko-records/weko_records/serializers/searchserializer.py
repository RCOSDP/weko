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

"""WEKO Search Serializer."""

from flask import current_app
from invenio_records_rest.serializers.json import JSONSerializer


class SearchSerializer(JSONSerializer):
    """
    extend JSONSerializer to modify search result
    """

    def transform_search_hit(self, pid, record_hit, links_factory=None):
        self.reset_metadata(record_hit)
        return super(SearchSerializer, self).transform_search_hit(pid,
                                                                  record_hit,
                                                                  links_factory)

    def reset_metadata(self, record_hit):
        """
        reset metadata by '_options'
        :param record_hit:
        :return:
        """
        rlt = ""
        src = record_hit['_source']
        if '_comment' in src:
            return
        op = src.pop("_options", {})
        ignore_meta = ('title', 'alternative', 'fullTextURL')
        if isinstance(op, dict):
            src["_comment"] = []
            for k, v in sorted(op.items(),
                               key=lambda x: x[1]['index'] if x[1].get(
                                   'index') else x[0]):
                if k in ignore_meta:
                    continue
                # item value
                vals = src.get(k)
                if isinstance(vals, list):
                    # index, options
                    v.pop('index', "")
                    for k1, v1 in sorted(v.items()):
                        i = int(k1)
                        if i < len(vals):
                            crtf = v1.get("crtf")
                            showlist = v1.get("showlist")
                            hidden = v1.get("hidden")
                            is_show = False if hidden else showlist
                            # list index value
                            if is_show:
                                rlt = rlt + ((vals[i] + ",") if not crtf
                                             else vals[i] + "\n")
                elif isinstance(vals, str):
                    crtf = v.get("crtf")
                    showlist = v.get("showlist")
                    hidden = v.get("hidden")
                    is_show = False if hidden else showlist
                    if is_show:
                        rlt = rlt + ((vals + ",") if not crtf
                                     else vals + "\n")
            if len(rlt) > 0:
                if rlt[-1] == ',':
                    rlt = rlt[:-1]
                src['_comment'] = rlt.split('\n')
                if len(src['_comment'][-1]) == 0:
                    src['_comment'].pop()
