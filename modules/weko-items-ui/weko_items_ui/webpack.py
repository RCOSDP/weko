from invenio_assets.webpack import WebpackThemeBundle

weko_items_ui = WebpackThemeBundle(
    __name__,
    "assets",
    default="bootstrap3",
    themes={
        "bootstrap3": dict(
            entry={
                "items_ui_css_indextree_style": "./css/weko_items_ui/indextree_style.css",
                "items_ui_js_dependencies_angularjs": "./js/weko_items_ui/js_angularjs.js",
                "items_ui_js_angular_ui": "./js/weko_items_ui/ui-bootstrap-tpls.min.js",
                "items_ui_css_items_author_search": "./css/weko_items_ui/styles.items.authorSearch.bundle.css",
                "items_ui_js_items_author_search": "./js/weko_items_ui/js_items_author_search.js",
                "items_ui_js_app": "./js/weko_items_ui/app.js",
                "items_ui_js_upload": "./js/weko_items_ui/upload.js",
                "items_ui_js_feedback_maillist": "./js/weko_items_ui/feedback_maillist.js",
                "items_ui_css_feedback_maillist": "./css/weko_items_ui/feedback.mail.css"
            },
            dependencies={
            }
        )
    }
)
