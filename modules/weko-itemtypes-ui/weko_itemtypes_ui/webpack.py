from invenio_assets.webpack import WebpackThemeBundle

weko_itemtypes_ui = WebpackThemeBundle(
    __name__,
    "assets",
    default="bootstrap3",
    themes={
        "bootstrap3": dict(
            entry={
                "itemstypes_ui_css_style": "./css/weko_itemtypes_ui/itemtype.less",
                "itemstypes_ui_css_style_mapping": "./css/weko_itemtypes_ui/mapping.less",
                "itemstypes_ui_css_style_rocrate_mapping": "./css/weko_itemtypes_ui/rocrate_mapping.less",
                "itemstypes_ui_js_dependencies_schema_editor": "./js/weko_itemtypes_ui/js_react.js",
                "itemstypes_ui_js_schema_editor": "./js/weko_itemtypes_ui/jsonschemaeditor.js",
                "itemstypes_ui_js_js": "./js/weko_itemtypes_ui/create_itemtype.js",
                "itemstypes_ui_js_js_property": "./js/weko_itemtypes_ui/create_property.js",
                "itemstypes_ui_js_js_mapping": "./js/weko_itemtypes_ui/create_mapping.js",
                "itemstypes_ui_js_js_rocrate_mapping": "./js/weko_itemtypes_ui/create_rocrate_mapping.js",
            },
            dependencies={
                'react': '0.14.8',
                'react-dom': '0.14.8',
            }
        )
    }
)
