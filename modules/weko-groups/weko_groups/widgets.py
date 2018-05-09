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

"""Implement custom field weko-group widgets."""

from wtforms.widgets import HTMLString


class RadioGroupWidget(object):
    """Render radio group with description."""

    def __init__(self, descriptions=None, **kwargs):
        """Initialize widget with description."""
        assert descriptions is None or isinstance(descriptions, dict)
        self.descriptions = descriptions

    def __call__(self, field, **kwargs):
        """Render radio group."""
        html = ""
        for subfield in field:
            label = subfield.label.text
            if field.default == subfield.data:
                subfield.checked = True
            else:
                subfield.checked = False
            description = self.descriptions.get(subfield.data, "")
            html += ('<div class="radio"><label>%s %s '
                     '<small class="text-muted">%s</small>'
                     '</label></div>') % (subfield(), label, description)
        return HTMLString(html)
