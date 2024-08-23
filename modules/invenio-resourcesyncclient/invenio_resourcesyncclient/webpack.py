from invenio_assets.webpack import WebpackThemeBundle

invenio_resourcesyncclient = WebpackThemeBundle(
    __name__,
    "assets",
    default="bootstrap3",
    themes={
        "bootstrap3": dict(
            entry={
                "resourcesyncserver_js_invenio_admin_resync_client_js": "./js/invenio_resourcesyncclient/resync_client.js",
                "resourcesyncserver_css_invenio_admin_resync_client_css": "css/invenio_resourcesyncclient/resync_client.css",
            },
            dependencies={
            }
        )
    }
)
