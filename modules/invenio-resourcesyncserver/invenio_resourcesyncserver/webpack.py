from invenio_assets.webpack import WebpackThemeBundle

invenio_resourcesyncserver = WebpackThemeBundle(
    __name__,
    "assets",
    default="bootstrap3",
    themes={
        "bootstrap3": dict(
            entry={
                "resourcesyncserver_js_invenio_admin_resource_js": "./js/invenio-resourcesyncserver/resource.js",
                "resourcesyncserver_css_invenio_admin_resource_css": "./css/invenio-resourcesyncserver/resource.css",
                "resourcesyncserver_js_invenio_admin_change_list_js": "./js/invenio-resourcesyncserver/change_list.js",
                "resourcesyncserver_css_invenio_admin_change_list_css": "./css/invenio-resourcesyncserver/change_list.css",
            },
            dependencies={
            }
        )
    }
)
