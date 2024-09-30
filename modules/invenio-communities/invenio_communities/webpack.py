from invenio_assets.webpack import WebpackThemeBundle

invenio_communities = WebpackThemeBundle(
    __name__,
    "assets",
    default="bootstrap3",
    themes={
        "bootstrap3": dict(
            entry={
                "communities_js_js": "./js/invenio_communities/main.js",
                "communities_css_css": "./scss/invenio_communities/communities.scss",
                "communities_css_css_tree": "./scss/invenio_communities/styles.community.bundle.css",
                "communities_css_css_tree_display": "./scss/invenio_communities/styles.bundle.css"
            },
            dependencies={
                "angular": "~1.4.9",
                "ckeditor": "~4.5.8",
                "jquery": "~3.2.1",
            }
        )
    }
)
