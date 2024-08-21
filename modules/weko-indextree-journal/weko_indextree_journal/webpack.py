from invenio_assets.webpack import WebpackThemeBundle

weko_indextree_journal = WebpackThemeBundle(
    __name__,
    "assets",
    default="bootstrap3",
    themes={
        "bootstrap3": dict(
            entry={
                "indextree_journal_css_style": "./css/weko_indextree_journal/styles.bundle.css",
                "indextree_journal_js_treeview": "./js/weko_indextree_journal/js_treeview.js",
                "indextree_journal_js_js": "./js/weko_indextree_journal/app.js",
            },
            dependencies={
            }
        )
    }
)
