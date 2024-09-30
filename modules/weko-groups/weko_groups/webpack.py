from invenio_assets.webpack import WebpackThemeBundle

weko_groups = WebpackThemeBundle(
    __name__,
    "assets",
    default="bootstrap3",
    themes={
        "bootstrap3": dict(
            entry={
                "group_js_js": "./js/groups/init.js",
                "group_css_styles": "./css/groups/groups.less",
            },
            dependencies={
            }
        )
    }
)
