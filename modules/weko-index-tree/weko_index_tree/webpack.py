from invenio_assets.webpack import WebpackThemeBundle

weko_index_tree = WebpackThemeBundle(
    __name__,
    "assets",
    default="bootstrap3",
    themes={
        "bootstrap3": dict(
            entry={
                "index_tree_css_style": "./css/weko_index_tree/styles.bundle.css",
                "index_tree_js_treeview": "./js/weko_index_tree/js_treeview.js",
                "index_tree_js_js": "./js/weko_index_tree/app.js",
            },
            dependencies={
            }
        )
    }
)
