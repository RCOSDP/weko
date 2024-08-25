from invenio_assets.webpack import WebpackThemeBundle

weko_authors = WebpackThemeBundle(
    __name__,
    "assets",
    default="bootstrap3",
    themes={
        "bootstrap3": dict(
            entry={
                "authors_css_css": "./css/weko_authors/styles.bundle.css",
                "authors_css_author_search_css": "./css/weko_authors/styles.search.bundle.css",
                "authors_css_author_prefix_css": "./css/weko_authors/styles.prefix.bundle.css",
                "authors_css_author_affiliation_css": "./css/weko_authors/styles.affiliation.bundle.css",
                "authors_css_author_export_css": "./css/weko_authors/app-author-export.main.chunk.css",
                "authors_css_author_import_css": "./css/weko_authors/app-author-import.main.chunk.css",
            },
            dependencies={
            }
        )
    }
)
