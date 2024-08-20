from invenio_assets.webpack import WebpackThemeBundle

weko_records_ui = WebpackThemeBundle(
    __name__,
    "assets",
    default="bootstrap3",
    themes={
        "bootstrap3": dict(
            entry={
                "records_ui_css_style": "./css/weko_records_ui/style.css",
                "records_ui_js_dependecies": "./js/weko_records_ui/js‗dependencies.js",
                "records_ui_js": "./js/weko_records_ui/js_angular.js",
                "records_ui_preview_carousel": "./js/weko_records_ui/preview_carousel.js",
                "records_ui_file_action_js": "./js/weko_records_ui/file_action.js",
                "records_ui_bootstrap_popover_js": "./js/weko_records_ui/bootstrap-popover-x.min.js",
                "records_ui_bootstrap_popover_css": "./css/weko_records_ui/bootstrap-popover-x.min.css"
            },
            dependencies={
                "bootstrap-sass": "~3.3.5",
                "bootstrap-switch": "~3.0.2",
                "font-awesome": "~4.4.0",
                "typeahead.js-bootstrap-css": "~1.2.1",
                "angular-animate": "~1.4.8",
                "angular-sanitize": "~1.4.10",
                "angular-strap": "~2.3.9",
                "angular-ui-bootstrap": "~0.13.2",
                "almond": "~0.3.1",
                "angular-loading-bar": "~0.9.0",
                "typeahead.js": "~0.11.1",
                "invenio-csl-js": "~0.1.3",
                "bootstrap-switch": "~3.0.2"
            }
        )
    }
)
