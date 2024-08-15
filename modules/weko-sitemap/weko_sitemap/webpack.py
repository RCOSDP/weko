from invenio_assets.webpack import WebpackThemeBundle

weko_sitemap = WebpackThemeBundle(
    __name__,
    "assets",
    default="bootstrap3",
    themes = {
        "bootstrap3": dict(
            entry = {
                "weko-sitemap": 'js/weko_sitemap/sitemap.js',
                "theme-weko-sitemap": 'css/weko_sitemap/styles.css',
            },
            dependencies = {
                
            }
        )
    }
)