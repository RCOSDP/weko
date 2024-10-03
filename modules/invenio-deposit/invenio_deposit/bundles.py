# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""UI for Invenio-Deposit."""

from flask_assets import Bundle
# from invenio_assets import NpmBundle


class NpmBundle(Bundle):
    """Bundle extension with a name and npm dependencies.

    The npm dependencies are used to generate a package.json file.
    """

    def __init__(self, *contents, **options):
        """Initialize the named bundle.

        :param name: name of the bundle
        :type name: str
        :param npm: npm dependencies
        :type npm: dict
        """
        self.npm = options.pop('npm', {})
        super().__init__(*contents, **options)


css = Bundle(
    'node_modules/ui-select/dist/select.css',
    'node_modules/jqueryui/jquery-ui.css',
    'node_modules/rr-ng-ckeditor/ng-ckeditor.css',
    filters='cleancss',
    output='gen/deposit.%(version)s.css',
)

js_dependencies_jquery = NpmBundle(
    'node_modules/jquery/jquery.js',
    'node_modules/jqueryui/jquery-ui.js',
    npm={
        'jquery': '~1.9.1',
        'jqueryui': '~1.11.1',
    }
)

js_dependencies_ui_sortable = NpmBundle(
    'node_modules/angular-ui-sortable/dist/sortable.js',
    npm={
        'angular-ui-sortable': '~0.14.3',
    }
)

js_dependencies_ckeditor = NpmBundle(
    'node_modules/ckeditor/ckeditor.js',
    'node_modules/rr-ng-ckeditor/ng-ckeditor.js',
    'node_modules/angular-schema-form-ckeditor/bootstrap-ckeditor.js',
    npm={
        'angular-schema-form-ckeditor':
            'https://github.com/RCOSDP/angular-schema-form-ckeditor'
            '.git#5562b3237ea18aa9d11f5aeced88228d834186c6',
        'ckeditor': '~4.5.10',
        'rr-ng-ckeditor': '~0.2.1',
    }
)

js_dependecies_uploader = NpmBundle(
    'node_modules/ng-file-upload/dist/ng-file-upload-all.js',
    'node_modules/invenio-files-js/dist/invenio-files-js.js',
    npm={
        'invenio-files-js': '~0.0.2',
        'ng-file-upload': '~12.0.4',
        'underscore': '~1.8.3',
    }
)

js_dependecies_schema_form = NpmBundle(
    'node_modules/objectpath/lib/ObjectPath.js',
    'node_modules/tv4/tv4.js',
    'node_modules/angular-schema-form/dist/schema-form.js',
    'node_modules/angular-schema-form/dist/bootstrap-decorator.js',
    'node_modules/invenio-records-js/dist/invenio-records-js.js',
    npm={
        'angular-schema-form': '~0.8.13',
        'invenio-records-js': '~0.0.8',
        'objectpath': '~1.2.1',
        'tv4': '~1.2.7',
    }
)

js_dependecies_autocomplete = NpmBundle(
    'node_modules/angular-animate/angular-animate.js',
    'node_modules/angular-strap/dist/angular-strap.js',
    'node_modules/angular-strap/dist/angular-strap.tpl.js',
    'node_modules/angular-underscore/index.js',
    'node_modules/ui-select/dist/select.js',
    'node_modules/angular-translate/dist/angular-translate.js',
    'node_modules/angular-schema-form-dynamic-select/'
    'angular-schema-form-dynamic-select.js',
    npm={
        'angular-animate': '~1.4.8',
        'angular-sanitize': '~1.4.10',
        'angular-schema-form-dynamic-select': '~0.13.1',
        'angular-strap': '~2.3.9',
        'angular-translate': '~2.11.0',
        'angular-underscore': '~0.0.3',
        'ui-select': '~0.18.1',
    },
)

js_main = NpmBundle(
    'node_modules/angular/angular.js',
    'node_modules/angular-sanitize/angular-sanitize.js',
    'node_modules/underscore/underscore.js',
    npm={
        'almond': '~0.3.1',
        'angular-sanitize': '~1.4.10',
        'underscore': '~1.8.3',
    },
)

js_dependecies = NpmBundle(
    # ui-sortable requires jquery to be already loaded
    js_dependencies_jquery,
    js_main,
    js_dependecies_uploader,
    js_dependecies_schema_form,
    js_dependecies_autocomplete,
    js_dependencies_ui_sortable,
    js_dependencies_ckeditor,
    filters='jsmin',
    output='gen/deposit.dependencies.%(version)s.js',
)

js = Bundle(
    'js/invenio_deposit/app.js',
    filters='jsmin',
    output='gen/deposit.%(version)s.js',
)
