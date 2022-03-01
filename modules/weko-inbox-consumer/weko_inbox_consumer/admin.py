import sys

from flask import abort, current_app, flash, request
from flask_admin import BaseView, expose
from flask_babelex import gettext as _
from werkzeug.local import LocalProxy


_app = LocalProxy(lambda: current_app.extentions['weko-admin'].app)


class CheckIntervalSettingView(BaseView):
    @expose('/', methods=['GET', 'POST'])
    def index(self):
        try:
            form = request.form.get('submit', None)
            if form == 'save_checkinterval_settings':
                check_interval = \
                    request.form.get('save_checkinterval_setting', 30000)
                _app.config['WEKO_CHECK_INBOX_INTERVAL'] = check_interval
                flash(
                    _('Intervel Check Inbox was updated.'),
                    category='success')
            return self.render(
                current_app.config['WEKO_INBOX_CONSUMER_SETTING_TEMPLATE'],
                check_interval=check_interval
                )
        except BaseException:
            current_app.logger.error(
                'Unexpected error: {}'.format(sys.exc_info())
            )
        return abort(400)


check_interval_adminview = {
    'view_class': CheckIntervalSettingView,
    'kwargs': {
        'category': _('Setting'),
        'name': _('Shibboleth'),
        'endpoint': 'interval_check'
    }
}


__all__ = (
    'check_interval_adminview',
    'CheckIntervalSettingView',
)
