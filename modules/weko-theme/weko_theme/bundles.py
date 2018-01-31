# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015, 2016, 2017 CERN.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""JS/CSS bundles for theme.

You include one of the bundles in a page like the example below (using ``js``
bundle as an example):

.. code-block:: html

    {%- asset "invenio_theme.bundles:js" %}
    <script src="{{ASSET_URL}}"  type="text/javascript"></script>
    {%- end asset %}
"""

from flask_assets import Bundle


css = Bundle(
    'css/weko_theme/theme.scss',
    'css/weko_theme/jsontreeview.css',
    filters='cleancssurl',
    output='gen/weko_theme.%(version)s.css',
)
"""Default CSS bundle ."""

js_treeview = Bundle(
    'js/weko_theme/jsontreeview.js',
    output="gen/index_tree_view.js"
)

js = Bundle(
    'js/weko_theme/app.js',
    filters='requirejs',
    output="gen/weko_theme.%(version)s.js",
)



