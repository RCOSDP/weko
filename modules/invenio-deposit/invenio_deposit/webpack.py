from invenio_assets.webpack import WebpackThemeBundle

invenio_deposit = WebpackThemeBundle(
    __name__,
    "assets",
    default="bootstrap3",
    themes={
        "bootstrap3": dict(
            entry={
                "deposit_css_css": "./css/invenio_deposit/css.css",
                "deposit_js_dependencies": "./js/invenio_deposit/js-dependencies.js",
                "deposit_js_js": "./js/invenio_deposit/app.js",
            },
            dependencies={
                'jquery': '~1.9.1',
                'jqueryui': '~1.11.1',
                'angular-ui-sortable': '~0.14.3',
                'angular-schema-form-ckeditor': 'https://github.com/RCOSDP/angular-schema-form-ckeditor.git#5562b3237ea18aa9d11f5aeced88228d834186c6',
                'ckeditor': '~4.5.10',
                'rr-ng-ckeditor': '~0.2.1',
                'invenio-files-js': '~0.0.2',
                'ng-file-upload': '~12.0.4',
                'underscore': '~1.8.3',
                'angular-schema-form': '~0.8.13',
                'invenio-records-js': '~0.0.8',
                'objectpath': '~1.2.1',
                'tv4': '~1.2.7',
                'angular-animate': '~1.4.8',
                'angular-sanitize': '~1.4.10',
                'angular-schema-form-dynamic-select': '~0.13.1',
                'angular-strap': '~2.3.9',
                'angular-translate': '~2.11.0',
                'angular-underscore': '~0.0.3',
                'ui-select': '~0.18.1',
                'almond': '~0.3.1',
                'angular-sanitize': '~1.4.10',
                'underscore': '~1.8.3',
            }
        )
    }
)
