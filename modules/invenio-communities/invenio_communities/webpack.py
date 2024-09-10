from invenio_assets.webpack import WebpackThemeBundle

invenio_communities = WebpackThemeBundle(
    __name__,
    "assets",
    default="bootstrap3",
    themes={
        "bootstrap3": dict(
            entry={
                "communities_js_js": "./js/main.js",
                "communities_css_css": "./scss/communities.scss",
                "communities_css_css_tree": "./scss/styles.community.bundle.css",
                "communities_css_css_tree_display": "./scss/styles.bundle.css"
            },
            dependencies={
                "ckeditor": "~4.5.8"
            }
        )
    }
)