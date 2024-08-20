from invenio_assets.webpack import WebpackThemeBundle

weko_accounts = WebpackThemeBundle(
    __name__,
    "assets",
    default="bootstrap3",
    themes={
        "bootstrap3": dict(
            entry={
                "accounts_css_embedded_wayf_custom": "./css/weko_accounts/wayf_custom.css",
                "accounts_js_embedded_ds_multi_language_js": "./js/weko_accounts/change_translation_embedded.js",
                "accounts_js_suggest_js": "./js/weko_accounts/suggest.js",
            },
            dependencies={
            }
        )
    }
)
