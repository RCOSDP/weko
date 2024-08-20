from invenio_assets.webpack import WebpackThemeBundle

weko_schema_ui = WebpackThemeBundle(
    __name__,
    "assets",
    default="bootstrap3",
    themes={
        "bootstrap3": dict(
            entry={
                "schema-ui-js": "./js/weko_schema_ui/app.js",
            },
            dependencies={
            }
        )
    }
)