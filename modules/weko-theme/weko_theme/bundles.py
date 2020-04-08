# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""JS/CSS bundles for theme.

You include one of the bundles in a page like the example below (using ``js``
bundle as an example):

.. code-block:: html

    {%- asset "invenio_theme.bundles:js" %}
    <script src="{{ASSET_URL}}"  type="text/javascript"></script>
    {%- end asset %}
"""

from flask_assets import Bundle
from invenio_assets import NpmBundle

css_bootstrap = NpmBundle(
    'css/weko_theme/styles.scss',
    depends=(
        'scss/invenio_theme/*.scss',
        'css/weko_theme/_variables.scss',
        'scss/invenio_communities/variables.scss',
        'scss/invenio_communities/communities/*.scss',
    ),
    filters='node-scss,cleancssurl',
    output='gen/weko_styles.%(version)s.css',
    npm={
            'almond': '~0.3.1',
            'bootstrap-sass': '~3.3.5',
            'font-awesome': '~4.4.0',
    })
"""Default CSS bundle with Bootstrap and Font-Awesome."""

css = Bundle(
    'css/weko_theme/theme.scss',
    'css/weko_theme/styles.bundle.css',
    filters='cleancssurl',
    output='gen/weko_theme.%(version)s.css',
)
"""Default CSS bundle ."""

css_buttons = Bundle(
    'css/weko_theme/styling.css',
    output='gen/weko_theme_buttons.%(version)s.css',
)
""" Button Styling CSS File. """

css_widget = Bundle(
    'css/weko_theme/gridstack.min.css',
    'css/weko_theme/widget.css',
    'css/weko_gridlayout/trumbowyg.min.css',
    output='gen/weko_theme_widget.%(version)s.css',
)
"""Widget CSS."""

js_treeview = Bundle(
    'js/weko_theme/inline.bundle.js',
    'js/weko_theme/polyfills.bundle.js',
    'js/weko_theme/main.bundle.js',
    output="gen/index_tree_view.js"
)

js = Bundle(
    'js/weko_theme/base.js',
    filters='requirejs',
    output="gen/weko_theme.%(version)s.js",
)

js_top_page = Bundle(
    'js/weko_theme/top_page.js',
    filters='requirejs',
    output="gen/weko_top_page.%(version)s.js",
)

js_detail_search = Bundle(
    'js/weko_theme/search_detail.js',
    filters='requirejs',
    output="gen/weko_detail_search.%(version)s.js",
)


js_widget_lib = Bundle(
    'js/weko_theme/lodash.js',
    'js/weko_theme/gridstack.js',
    'js/weko_theme/ResizeSensor.js',
    filters='jsmin',
    output="gen/widget_lib.%(version)s.js",
)

widget_js = Bundle(
    js_widget_lib,
    'js/weko_theme/widget.js',
    filters='jsmin',
    output="gen/widget.%(version)s.js",
)
