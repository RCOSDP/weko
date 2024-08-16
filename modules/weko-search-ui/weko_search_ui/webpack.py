from invenio_assets.webpack import WebpackThemeBundle

weko_search_ui = WebpackThemeBundle(
    __name__,
    "assets",
    default="bootstrap3",
    themes={
        "bootstrap3": dict(
            entry={
                'theme-weko-search-ui': 'css/weko_search_ui/dot_leaders.css',
                'weko-search-ui': 'js/weko_search_ui/app.js',
                'import': 'js/weko_search_ui/import.js',
                'export': 'js/weko_search_ui/export.js',
                'moment': 'js/weko_search_ui/moment.min.js',
                'theme-import': 'css/weko_search_ui/import.less',
                'theme-export': 'css/weko_search_ui/export.less',
                'facet-search': 'js/weko_search_ui/facet_search_bundle.js',
                'theme-facet-search': 'css/weko_search_ui/facet_search_bundle.less'
            },
            dependencies={
                "bootstrap-datepicker": "~1.7.1"
            }
        )
    }
)
