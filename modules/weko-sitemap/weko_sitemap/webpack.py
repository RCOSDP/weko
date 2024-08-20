from invenio_assets.webpack import WebpackThemeBundle

weko_sitemap = WebpackThemeBundle(
    __name__,
    "assets",
    default="bootstrap3",
    themes={
        "bootstrap3": dict(
            entry={
                'sitemap-js-js': './js/weko_sitemap/sitemap.js',
                'sitemap-css-css': './css/weko_sitemap/styles.css',
            },
            dependencies={
            }
        )
    }
)
