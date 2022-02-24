import re
from flask import current_app, request

from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_pidrelations.contrib.versioning import PIDVersioning
from invenio_db import db


def get_recid_p(recid):
    # recidから"."以下を排除
    try:
        c_recid = PersistentIdentifier.get('recid', str(recid))
    except PIDDoesNotExistError:
        c_recid = None
        # TODO :レコードが存在しないエラーを探す
    if c_recid:
        recid_version = PIDVersioning(child=c_recid)
        if recid_version.has_parents:
            return recid_version.parent.pid_value.replace('parent:', '')
        else:
            return recid


def get_records_pid(pid):
    # weko_records_ui.views.parent_view_methodの一部分参考
    # TODO:pidがない時の処理未考案
    try:
        p_pid = PersistentIdentifier.get('parent', 'parent:' + str(pid))
    except PIDDoesNotExistError:
        print("not found")
        p_pid = None
    if p_pid:
        pid_version = PIDVersioning(parent=p_pid)
        print(pid_version.children)
        if pid_version.last_child:
            print("found")
            print(pid_version.last_child.object_uuid)
            return pid_version.last_child.object_uuid
        else:
            print("not found")
            print(p_pid.object_uuid)
            return p_pid.object_uuid
        print("not last child")


def get_record_permalink(recid_p):
    """
    そのレコードの親要素のuuidを取得し、それに紐づいているdoiのuriを取得
    """
    uuid_p = \
        PersistentIdentifier.get('parent',
                                 'parent:'+str(recid_p)
                                 ).object_uuid
    print(uuid_p)
    try:
        pid = PersistentIdentifier.query.filter_by(
            pid_type='doi',
            object_uuid=uuid_p,
            status=PIDStatus.REGISTERED
        ).order_by(
            db.desc(PersistentIdentifier.created)
        ).first()
        if pid is None:
            return '{host_url}records/{recid}'.format(
                host_url=get_url_root(), recid=recid_p)
        else:
            return pid.pid_value
    except PIDDoesNotExistError as e:
        return '{host_url}records/{recid}'.format(
            host_url=get_url_root(), recid=recid_p)


def get_url_root():
    """Check a DOI is existed.

    weko_workflow.utils.get_url_rootのコピペ
    :return: url root.
    """
    site_url = current_app.config['THEME_SITEURL'] + '/'
    return request.host_url if request else site_url


def inbox_url(url=None):
    if url is not None:
        if ('localhost' in url) or (current_app.config['WEB_HOST'] in url):
            return re.sub('https://(.*)/inbox',
                          'https://'+current_app.config['NGINX_HOST']+'/inbox',
                          url
                          )
        else:
            return url
    else:
        return current_app.config['INBOX_URL']
