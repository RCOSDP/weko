from flask_assets import Bundle

weko_logging_export_css = Bundle(
    "css/weko_logging/export.less",
    filters="cleancss",
    output="gen/logExport.%(version)s.css",
)

weko_logging_export_js = Bundle(
    "js/weko_logging/export.js",
    # filters="jsmin",
    output="gen/logExport.%(version)s.js",
)