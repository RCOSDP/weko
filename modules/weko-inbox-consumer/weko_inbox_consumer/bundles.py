from flask_assets import Bundle


push_notify_js = Bundle(
    'js/check_inbox.js',
    output='gen/inbox_check.%(version)s.js'
)


interval_check_js = Bundle(
    'js/interval_check.js',
    output='get/interval_check.%(version)s.js'
)
