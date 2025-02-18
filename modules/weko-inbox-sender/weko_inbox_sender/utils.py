import re
from flask import current_app, request

from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_pidrelations.contrib.versioning import PIDVersioning
from invenio_db import db


def get_recid_p(recid):
    """Remove the version number from the recid that has the version number

    :param string recid: recid that has
    :type recid: _type_
    :return: recid
    :rtype: string
    """
    try:
        c_recid = PersistentIdentifier.get('recid', str(recid))
    except PIDDoesNotExistError:
        c_recid = None
    if c_recid:
        recid_version = PIDVersioning(child=c_recid)
        if recid_version.has_parents:
            return recid_version.parent.pid_value.replace('parent:', '')
        else:
            return recid


def get_records_pid(pid):
    """Get the uuid of the latest record
    from the recid without the version number

    :param string pid: recid without the version number
    :return: uuid of the latest record
    :rtype: string
    """
    try:
        p_pid = PersistentIdentifier.get('parent', 'parent:' + str(pid))
    except PIDDoesNotExistError:
        p_pid = None
    if p_pid:
        pid_version = PIDVersioning(parent=p_pid)
        if pid_version.last_child:
            return pid_version.last_child.object_uuid
        else:
            return p_pid.object_uuid


def get_record_permalink(recid_p):
    """Get the uuid of the parent element of the record
    and get the uri of the doi associated with it

    :param string recid_p: recid
    :return: uri of doi
    :rtype: string
    """
    uuid_p = \
        PersistentIdentifier.get('parent',
                                 'parent:'+str(recid_p)
                                 ).object_uuid
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

    :return: url root.
    """
    site_url = current_app.config['THEME_SITEURL'] + '/'
    return request.host_url if request else site_url


def inbox_url(url=None):
    """Convert inbox url to your own inbox url

    :param string url: inbox url, defaults to None
    :return: own inbox url
    :rtype: string
    """
    if url is not None:
        if ('localhost' in url) or (current_app.config['WEB_HOST'] in url) or get_url_root() in url:
            return re.sub(
                'https://(.*)/inbox',
                current_app.config['INBOX_URL'],
                url
            )
        else:
            return url
    else:
        return current_app.config['INBOX_URL']
