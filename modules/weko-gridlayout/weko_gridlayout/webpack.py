from invenio_assets.webpack import WebpackThemeBundle

weko_gridlayout = WebpackThemeBundle(
    __name__,
    "assets",
    default="bootstrap3",
    themes={
        "bootstrap3": dict(
            entry={
                "gridlayout_js_widget_design_js_lib": "./js/weko_gridlayout/widget-design-js-lib.js",
                "gridlayout_js_widget_design_reactjs_lib": "./js/weko_gridlayout/widget-design-reactjs-lib.js",
                "gridlayout_js_widget_design_js": "./js/weko_gridlayout/widget.design.js",
                "gridlayout_js_widget_setting_js": "./js/weko_gridlayout/widget.setting.js",
                "gridlayout_css_widget_design_css": "./css/weko_gridlayout/widget-design-css.css",
                "gridlayout_css_widget_setting_css": "./css/weko_gridlayout/widget.item.css",
                "gridlayout_css_katex_min_css": "./css/weko_gridlayout/katex.min.css",
                "gridlayout_css_trumbowyg_css": "./css/weko_gridlayout/trumbowyg-css.css",
                "gridlayout_js_katex_min_js": "./js/weko_gridlayout/katex.min.js",
                "gridlayout_js_prop_types_js": "./js/weko_gridlayout/prop.types.js",
                "gridlayout_js_react_quill_js": "./js/weko_gridlayout/react.quill.js",
                "gridlayout_js_trumbowyg_js_plugin": "./js/weko_gridlayout/react-trumbowyg-js.js",
            },
            dependencies={
            }
        )
    }
)
