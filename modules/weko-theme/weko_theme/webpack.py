from invenio_assets.webpack import WebpackThemeBundle

weko_theme = WebpackThemeBundle(
    __name__,
    "assets",
    default="bootstrap3",
    themes={
        "bootstrap3": dict(
            entry={
                'theme-scss-bootstrap': './css/weko_theme/styles.scss',
                'theme-css': './css/weko_theme/theme.scss',
                'theme-css-buttons': './css/weko_theme/styling.css',
                'theme-css-widget': './css/weko_theme/weko_theme_widget.css',
                'theme-js': './js/weko_theme/base.js',
                'theme-js-top-page': './js/weko_theme/top_page.js',
                'theme-search-detail': './js/weko_theme/search_detail.js',
                'theme-widget-lib': './js/weko_theme/widget_lib.js',
                'theme-widget': './js/weko_theme/widget_js.js',
                'theme-angular': './node_modules/angular/angular.js',
                'theme-schema-form': './node_modules/angular-schema-form/dist/schema-form.min.js',
            },
            dependencies={
                'almond': '~0.3.1',
                'angular': '~1.4.9',
                "bootstrap": "~3.3.7",
                'bootstrap-sass': '~3.3.5',
                'font-awesome': '~4.4.0',
                'jquery': '~2.1.3',
                'lodash': '~3.10.1',
                'mootools': '~1.5.1',
            },
            aliases={
                '../../theme.config$': 'less/weko_theme/theme.config',
            }
        )
    }
)
