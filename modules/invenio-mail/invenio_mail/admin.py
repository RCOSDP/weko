# -*- coding: utf-8 -*-

"""Admin model views for Mail sets."""

import json
import sys

from flask import abort, current_app, flash, jsonify, request
from flask_admin import BaseView, expose
from flask_babelex import gettext as _
from flask_mail import Message
from werkzeug.local import LocalProxy

from invenio_mail.models import MailConfig

from . import config
from .models import MailTemplates

_app = LocalProxy(lambda: current_app.extensions['weko-admin'].app)


def _load_mail_cfg_from_db():
    return MailConfig.get_config()


def _save_mail_cfg_to_db(cfg):
    MailConfig.set_config(cfg)


def _set_flask_mail_cfg(cfg):
    current_app.extensions['mail'].suppress = False
    current_app.extensions['mail'].server = cfg.get('mail_server', '')
    current_app.extensions['mail'].port = cfg.get('mail_port', '')
    current_app.extensions['mail'].username = cfg.get('mail_username', '')
    current_app.extensions['mail'].password = cfg.get('mail_password', '')
    current_app.extensions['mail'].use_tls = cfg.get('mail_use_tls', '')
    current_app.extensions['mail'].use_ssl = cfg.get('mail_use_ssl', '')
    current_app.extensions['mail'].default_sender = cfg.get('mail_default_sender', '')
    current_app.extensions['mail'].debug = 0
    current_app.extensions['mail'].local_hostname = cfg['mail_local_hostname']


class MailSettingView(BaseView):
    @expose('/', methods=['GET', 'POST'])
    def index(self):
        mail_cfg = {
            'mail_server': 'localhost',
            'mail_port': 25,
            'mail_use_tls': False,
            'mail_use_ssl': False,
            'mail_username': None,
            'mail_password': None,
            'mail_default_sender': None,
            'mail_local_hostname':None
        }
        try:
            mail_cfg.update(_load_mail_cfg_from_db())
            if request.method == 'POST':
                mail_cfg['mail_use_tls'] = False
                mail_cfg['mail_use_ssl'] = False
                rf = request.form.to_dict()
                # confirm data
                check = True
                if not rf.get('mail_server'):
                    check = False
                    flash(_('Mail server can\'t be empty.'), category='error')
                if not rf.get('mail_port'):
                    check = False
                    flash(_('Mail port can\'t be empty.'), category='error')
                if not rf.get('mail_default_sender'):
                    check = False
                    flash(_('Mail default sender can\'t be empty.'),
                          category='error')
                # if check ok, to update setting
                if check:
                    mail_cfg.update(rf)
                    if 'mail_use_tls' in rf:
                        mail_cfg['mail_use_tls'] = True
                    if 'mail_use_ssl' in rf:
                        mail_cfg['mail_use_ssl'] = True
                    _save_mail_cfg_to_db(mail_cfg)
                    flash(_('Mail settings have been updated.'),
                          category='success')
            test_form = {
                'recipient': '',
                'subject': '',
                'body': ''}
            return self.render(config.INVENIO_MAIL_SETTING_TEMPLATE,
                               mail_cfg=mail_cfg, test_form=test_form)
        except BaseException:
            current_app.logger.error(
                "Unexpected error: {}".format(sys.exc_info()))
        return abort(400)

    @expose('/send_test_mail', methods=['POST'])
    def send_test_mail(self):
        try:
            mail_cfg = _load_mail_cfg_from_db()
            _set_flask_mail_cfg(mail_cfg)
            msg = Message()
            rf = request.form.to_dict()
            msg.subject = rf['subject']
            msg.body = rf['body']
            msg.recipients = [rf['recipient']]
            current_app.extensions['mail'].send(msg)
            flash(_('Test mail sent.'), category='success')
        except Exception as ex:
            flash(_('Failed to send mail.'), category='error')
            flash(str(ex), category='error')
        test_form = {
            'recipient': '',
            'subject': '',
            'body': ''}
        test_form.update(rf)
        return self.render(config.INVENIO_MAIL_SETTING_TEMPLATE,
                           mail_cfg=mail_cfg, test_form=test_form)

    @classmethod
    def send_statistic_mail(cls, rf):
        """Send statistic mail to user.

        Keyword Arguments:
            rf {dictionary} -- mail data

        Returns:
            boolean -- True if send mail successfully

        """
        try:
            mail_cfg = _load_mail_cfg_from_db()
            _set_flask_mail_cfg(mail_cfg)
            msg = Message()
            msg.subject = rf['subject']
            msg.body = rf['body']
            msg.recipients = [rf['recipient']]
            current_app.extensions['mail'].send(msg)
            return True
        except Exception as ex:
            current_app.logger.error('Cannot send email:{}'.format(str(ex)))
            return False


class MailTemplatesView(BaseView):
    @expose('/', methods=['GET'])
    def index(self):
        """Mail template top page."""
        mts = MailTemplates.get_templates()
        return self.render(config.INVENIO_MAIL_TEMPLATES_TEMPLATE,
                           data=json.dumps({"mail_templates": mts}))

    @expose('help', methods=['GET'])
    def help(self):
        """Get help of mail template."""
        return self.render(config.INVENIO_MAIL_HELP_TEMPLATE,
                           data=config.INVENIO_MAIL_VARIABLE_HELP)

    @expose('/save', methods=['POST'])
    def save_mail_template(self):
        """Save mail template.

        :return:
        """

        mail_templates = request.get_json()['mail_templates']
        status = True
        for m in mail_templates:
            status = status and MailTemplates.save_and_update(m)
        if status:
            result = {
                "status": status,
                "msg": _("Mail template was successfully updated."),
                "data": MailTemplates.get_templates()
            }
        else:
            result = {
                "status": status,
                "msg": _("Mail template update failed."),
                "data": MailTemplates.get_templates()
            }
        return jsonify(result), 200

    @expose('/delete', methods=['DELETE'])
    def delete_mail_template(self):
        """Delete mail template.

        :return:
        """

        template_id = request.get_json()['template_id']
        status = MailTemplates.delete_by_id(template_id)
        if status:
            result = {
                "status": status,
                "msg": _("Mail template was successfully deleted."),
                "data": MailTemplates.get_templates()
            }
        else:
            result = {
                "status": status,
                "msg": _("Mail template delete failed."),
                "data": MailTemplates.get_templates()
            }
        return jsonify(result), 200


mail_adminview = {
    'view_class': MailSettingView,
    'kwargs': {
        'category': _('Setting'),
        'name': _('Mail'),
        'endpoint': 'mail'
    }
}

mail_templates_adminview = {
    'view_class': MailTemplatesView,
    'kwargs': {
        'category': _('Setting'),
        'name': _('Mail Templates'),
        'endpoint': 'mailtemplates'
    }
}

__all__ = (
    'mail_adminview',
    'mail_templates_adminview'
)
