from invenio_assets.webpack import WebpackThemeBundle

weko_theme = WebpackThemeBundle(
    __name__,
    "assets",
    default="bootstrap3",
    themes = {
        "bootstrap3": dict(
            entry = {
                'theme-scss-css-bootstrap':'css/weko_theme/styles.scss',
                'theme-css-styling':'css/weko_theme/styling.css',
                'theme-css-weko-theme-widget':'css/weko_theme/weko_theme_widget.css',
                'theme-scss-weko-theme':'css/weko_theme/theme.scss',
                'theme-js-weko-theme-tree-view':'js/weko_theme/weko_theme_tree_view.js',
                'theme-js-base': 'js/weko_theme/base.js',
                'theme-js-top-page': 'js/weko_theme/top_page.js',
                'theme-js-search-detail': 'js/weko_theme/search_detail.js',
                'theme-js-widget-lib': 'js/weko_theme/widget_lib.js',
                'theme-js-widget': 'js/weko_theme/widget_js.js',
            },
            dependencies={
                'almond': '~0.3.1',
                'bootstrap-sass': '~3.3.5',
                'font-awesome': '~4.4.0',
            }
        )
    }
)