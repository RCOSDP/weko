from invenio_assets.webpack import WebpackThemeBundle

weko_admin = WebpackThemeBundle(
    __name__,
    "assets",
    default="bootstrap3",
    themes={
        "bootstrap3": dict(
            entry={
                "admin_js_js": "./js/weko_admin/js.js",
                "admin_js_statistics_reactjs_lib": "./js/weko_admin/statistics-reactjs-lib.js",
                "admin_js_custom_report_js": "./js/weko_admin/custom_report.js",
                "admin_js_search_management_js": "./js/weko_admin/search_management.js",
                "admin_js_react_bootstrap_js": "./js/weko_admin/react-bootstrap.min.js",
                "admin_js_stats_report_js": "./js/weko_admin/stats-report-js.js",
                "admin_js_feedback_mail_js": "./js/weko_admin/feedback_mail.js",
                "admin_js_log_analysis_js": "./js/weko_admin/log_analysis.js",
                "admin_css_date_picker_css": "./css/weko_admin/date-picker-css.css",
                "admin_js_date_picker_js": "./js/weko_admin/date-picker-js.js",
                "admin_css_css": "./css/weko_admin/styles.css",
                "admin_css_weko_admin_quill_sknow_css": "./css/weko_admin/quill.snow.css",
                "admin_css_weko_admin_feedback_mail_css": "./css/weko_admin/feedback.mail.css",
                "admin_js_admin_lte_js_dependecies": "./js/weko_admin/admin-lte-js-dependecies.js",
                "admin_js_weko_admin_site_info_js": "./js/weko_admin/site_info.js",
                "admin_css_weko_admin_site_info_css": "./css/weko_admin/site.info.css",
                "admin_js_weko_admin_ng_js_tree_js": "./js/weko_admin/weko-admin-ng-js-tree-js.js",
                "admin_js_weko_admin_restricted_access_js": "./js/weko_admin/restricted_access.js",
                "admin_js_weko_admin_facet_search_js": "./js/weko_admin/facet_search_admin.js",
                "admin_js_reindex_elasticsearch_js": "./js/weko_admin/reindex_elasticsearch.js",
            },
            dependencies={
                'requirejs': '~2.3.6',
                'jquery': '~1.9.1',
                'angular': '~1.4.9',
                'moment': '~2.9.0',
                'select2': '~4.0.2',
                'admin-lte': '~2.3.6',
                'angular': '~1.4.9',
            }
        )
    }
)
