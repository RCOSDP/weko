# -*- coding: utf-8 -*-
#
# This file is part of WEKO3.
# Copyright (C) 2017 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# WEKO3 is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with WEKO3; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.

"""Utilities for download file."""

import base64
import mimetypes
import os
import random
import shutil
import string
import tempfile
import unicodedata
from datetime import datetime, timezone

from flask import abort, current_app, render_template, request, redirect, send_file, url_for, session
from flask_babelex import gettext as _
from flask_babelex import get_locale
from flask_login import current_user
from flask_security.utils import verify_password
from invenio_db import db
from invenio_files_rest import signals
from invenio_files_rest.models import FileInstance
from invenio_files_rest.views import ObjectResource
from invenio_records_files.utils import record_file_factory
from sqlalchemy.exc import SQLAlchemyError
from weko_accounts.views import _redirect_method
from weko_admin.models import AdminSettings
from weko_deposit.api import WekoRecord
from weko_groups.api import Group
from weko_logging.activity_logger import UserActivityLogger
from weko_records.api import FilesMetadata, ItemTypes
from weko_redis.redis import RedisConnection
from weko_user_profiles.models import UserProfile
from weko_workflow.utils import is_terms_of_use_only
from werkzeug.datastructures import Headers
from werkzeug.urls import url_quote

from weko_records_ui.errors import AvailableFilesNotFoundRESTError
from weko_records_ui.models import (
    FileOnetimeDownload, FileSecretDownload, PDFCoverPageSettings
)
from weko_records_ui.pdf import make_combined_pdf
from weko_records_ui.permissions import (
    check_file_download_permission, check_original_pdf_download_permission,
    file_permission_factory, is_owners_or_superusers
)
from weko_records_ui.utils import (
    check_and_send_usage_report, convert_token_into_obj,
    generate_sha256_hash,
    get_billing_file_download_permission, get_groups_price,
    get_min_price_billing_file_download, get_valid_onetime_download,
    is_billing_item, save_download_log, validate_url_download
)


def weko_view_method(pid, record, template=None, **kwargs):
    r"""Display Weko view.

    Sends record_viewed signal and renders template.

    :param pid: PID object.
    :param record: Record object.
    :param template: Template to render.
    :returns: The rendered template.
    """
    flst = FilesMetadata.get_records(pid.pid_value)
    frecord = []

    if len(flst) > 0:
        for fj in flst:
            frecord.append(fj.dumps())

    item_type = ItemTypes.get_by_id(id_=record['item_type_id'])
    item_type_info = "{}({})".format(item_type.item_type_name.name,
                                     item_type.tag)
    return render_template(
        template,
        pid=pid,
        record=record,
        files=frecord,
        item_type_info=item_type_info
    )


def prepare_response(pid_value, fd=True):
    """Prepare response data and header.

    :param pid_value:
    :param fd:
    :return:
    """
    fn = request.view_args.get("filename")
    flst = FilesMetadata.get_records(pid_value)
    for fj in flst:
        if fj.dumps().get("display_name") == fn:
            stream = fj.model.contents[:]
            displaytype = fj.model.json.get("displaytype")
            file_name = fj.model.json.get("file_name")
            break

    headers = Headers()
    headers['Content-Length'] = len(stream)
    try:
        filenames = {'filename': fn.encode('latin-1')}
    except UnicodeEncodeError:
        filenames = {'filename*': "UTF-8''%s" % url_quote(fn)}
        encoded_filename = (unicodedata.normalize('NFKD', fn)
                            .encode('latin-1', 'ignore'))
        if encoded_filename:
            filenames['filename'] = encoded_filename

    if fd:
        headers.add('Content-Disposition', 'attachment', **filenames)
        mimetype = 'application/octet-stream'
    else:
        headers['Content-Type'] = 'text/plain; charset=utf-8'
        headers.add('Content-Disposition', 'inline')
        mimetype = mimetypes.guess_type(request.view_args.get("filename"))[0]
        # if 'detail' in displaytype and '.pdf' in file_name:
        #     from PyPDF2.pdf import PdfFileWriter, PdfFileReader
        #     import io
        #     source = PdfFileReader(io.BytesIO(stream), strict=True)
        #     fp = source.getPage(0)
        #     writer = PdfFileWriter()
        #     writer.addPage(fp)
        #     f = io.BytesIO()
        #     writer.write(f)
        #     stream = f.getvalue()

    rv = current_app.response_class(
        stream,
        mimetype=mimetype,
        headers=headers,
        direct_passthrough=True,
    )

    return rv


def file_preview_ui(pid, record, _record_file_factory=None, **kwargs):
    """File preview view for a given record.

    Plug this method into your ``RECORDS_UI_ENDPOINTS`` configuration:

    .. code-block:: python

        RECORDS_UI_ENDPOINTS = dict(
            recid=dict(
                # ...
                route='/records/<pid_value/file_preview/<filename>',
                view_imp='invenio_records_files.utils:file_preview_ui',
                record_class='invenio_records_files.api:Record',
            )
        )

    :param _record_file_factory:
    :param pid: The :class:`invenio_pidstore.models.PersistentIdentifier`
        instance.
    :param record: The record metadata.
    """
    return file_ui(
        pid,
        record,
        _record_file_factory,
        is_preview=True,
        **kwargs)


def file_download_ui(pid, record, _record_file_factory=None, **kwargs):
    """File download view for a given record.

    Plug this method into your ``RECORDS_UI_ENDPOINTS`` configuration:

    .. code-block:: python

        RECORDS_UI_ENDPOINTS = dict(
            recid=dict(
                # ...
                route='/records/<pid_value/files/<filename>',
                view_imp='invenio_records_files.utils:file_download_ui',
                record_class='invenio_records_files.api:Record',
            )
        )

    :param _record_file_factory:
    :param pid: The :class:`invenio_pidstore.models.PersistentIdentifier`
        instance.
    :param record: The record metadata.
    """
    return file_ui(
        pid,
        record,
        _record_file_factory,
        is_preview=False,
        **kwargs)


def file_ui(
        pid,
        record,
        _record_file_factory=None,
        is_preview=False,
        **kwargs):
    """File Ui.

    :param is_preview: Determine the type of event.
           True: file-preview, False: file-download
    :param _record_file_factory:
    :param pid: The :class:`invenio_pidstore.models.PersistentIdentifier`
        instance.
    :param record: The record metadata.
    """
    _record_file_factory = _record_file_factory or record_file_factory
    # Extract file from record.
    fileobj = _record_file_factory(
        pid, record, kwargs.get('filename')
    )

    if not fileobj:
        abort(404)

    obj = fileobj.obj

    # Check file contents permission
    is_terms_of_use_only = _is_terms_of_use_only(fileobj,request.args)
    if not file_permission_factory(record, fjson=fileobj).can():
        # [利用規約のみ]の場合、アクセス権無しでもファイルダウンロード可能。
        if not is_terms_of_use_only:
            if not current_user.is_authenticated:
                return _redirect_method(has_next=True)
            abort(403)

    if not is_preview:
        # open_restricted download
        if 'open_restricted' in fileobj.get('accessrole', '') \
            and not is_terms_of_use_only \
            and not is_owners_or_superusers(record):

            filename = fileobj["filename"]
            record_id = pid.pid_value
            user_mail = current_user.email
            onetime_download:FileOnetimeDownload = get_valid_onetime_download(
                filename, record_id, user_mail
            )
            if onetime_download is None:
                current_app.logger.info('onetime_download is None')
                abort(403)

            # Create one-time token
            hash = generate_sha256_hash(onetime_download)
            bytes = hash + b'_' + str(onetime_download.id).encode()
            token = base64.urlsafe_b64encode(bytes).decode()

            # Download file using one-time token
            return validate_onetime_token(
                pid, record, filename, token,
                _record_file_factory=_record_file_factory
            )

    # #Check permissions
    # ObjectResource.check_object_permission(obj)

    # Get user's language and defautl language for PDF coverpage.
    user_profile = UserProfile.get_by_userid(current_user.get_id())
    lang = user_profile.language if user_profile and user_profile.language \
        else 'en'

    return _download_file(fileobj, is_preview, lang, obj, pid, record)


def _download_file(file_obj, is_preview, lang, obj, pid, record):
    """Download file.

    :param file_obj:File object
    :param is_preview: preview flag.
    :param lang: Language
    :param obj:
    :param pid:
    :param record:Record json
    :return:
    """
    # Add download signal
    add_signals_info(record, obj)

    if not is_preview:
        UserActivityLogger.info(
            operation="FILE_DOWNLOAD",
            target_key=pid.pid_value,
        )

    # Send file without its pdf cover page
    try:
        pdfcoverpage_set_rec = PDFCoverPageSettings.find(1)
        coverpage_state = WekoRecord.get_record_cvs(pid.object_uuid)

        is_original = request.args.get('original') or False
        is_pdf = 'pdf' in file_obj.mimetype
        can_download_original_pdf = check_original_pdf_download_permission(
            record)

        convert_to_pdf = False
        if is_preview \
            and ('msword' in file_obj.mimetype
                 or 'vnd.ms' in file_obj.mimetype
                 or 'vnd.openxmlformats' in file_obj.mimetype):
            convert_to_pdf = True

        # if not pdf or cover page disabled: Download directly
        # if pdf and cover page enabled and has original in query param: check
        # permission (user roles)
        if is_pdf is False \
                or pdfcoverpage_set_rec is None \
                or pdfcoverpage_set_rec.avail == 'disable' \
                or coverpage_state is False \
                or (is_original and can_download_original_pdf):
            return ObjectResource.send_object(
                obj.bucket, obj,
                expected_chksum=file_obj.get('checksum'),
                logger_data={
                    'bucket_id': obj.bucket_id,
                    'pid_type': pid.pid_type,
                    'pid_value': pid.pid_value,
                },
                as_attachment=not is_preview,
                is_preview=is_preview,
                convert_to_pdf=convert_to_pdf
            )
    except AttributeError:
        return ObjectResource.send_object(
            obj.bucket, obj,
            expected_chksum=file_obj.get('checksum'),
            logger_data={
                'bucket_id': obj.bucket_id,
                'pid_type': pid.pid_type,
                'pid_value': pid.pid_value,
            },
            as_attachment=not is_preview,
            is_preview=is_preview
        )
    # Send file with its pdf cover page
    file_instance_record = FileInstance.query.filter_by(
        id=obj.file_id).first()

    # Send download signal
    signals.file_downloaded.send(current_app._get_current_object(), obj=obj)

    return make_combined_pdf(pid, file_obj, obj, lang)


def add_signals_info(record, obj):
    """Add event signals info.

    Add user role, site license flag, item index list.

    :param record: the record metadate.
    :param obj: send object.
    """
    # Add user role info to send_obj

    userrole = 'guest'
    userid = 0
    user_groups = []
    if hasattr(current_user, 'id'):
        userid = current_user.id
        user_groups = Group.query_by_user(current_user).all()
        if len(current_user.roles) == 0:
            userrole = 'user'
        elif len(current_user.roles) == 1:
            userrole = current_user.roles[0].name
        else:
            max_power_role_id = 2147483646
            for r in current_user.roles:
                if max_power_role_id > r.id:
                    if max_power_role_id == 2147483646 or r.id > 0:
                        max_power_role_id = r.id
                        userrole = r.name
    obj.userrole = userrole
    obj.userid = userid

    # Add groups of current users
    groups = [{'group_id': g.id, 'group_name': g.name} for g in user_groups]
    obj.user_group_list = groups if groups else None

    # Check whether billing file or not
    obj.is_billing_item = is_billing_item(record['item_type_id'])

    # Add billing file price
    billing_file_price = ''
    if obj.is_billing_item:
        groups_price = get_groups_price(record)
        billing_files_permission = \
            get_billing_file_download_permission(groups_price)
        min_price_dict = \
            get_min_price_billing_file_download(groups_price,
                                                billing_files_permission)
        if isinstance(min_price_dict, dict):
            billing_file_price = min_price_dict.get(obj.key)
    obj.billing_file_price = billing_file_price

    # Add site license flag to send_obj
    obj.site_license_flag = True if hasattr(current_user, 'site_licese_flag') \
        else False
    obj.site_license_name = current_user.site_license_name \
        if hasattr(current_user, 'site_license_name') else ''

    # Add index list info to send_obj
    index_list = ''
    record_navs = record.navi
    if len(record_navs) > 0:
        for index in record_navs:
            current_app.logger.debug(index)
            if index[3] is not None:
                index_list += index[3] + '|'
            else:
                index_list += index[4] + '|'
    obj.index_list = index_list[:len(index_list) - 1]

    # Add item info to send_obj
    obj.item_title = record['item_title']
    obj.item_id = record['_deposit']['id']


def error_response(error_message, status_code=400):
    error_template = "weko_theme/error.html"
    return render_template(error_template, error=error_message), status_code


def check_onetime_token_and_validate(
    pid, record, filename, _record_file_factory=None, **kwargs):
    """
    Retrieve necessary data and delegate to validate_onetime_token for validation.

    Args:
    pid (PersistentIdentifier): The identifier for the item.
    record (WekoRecord): The record metadata of the item.
    filename (str): The name of the file to download.

    Returns:
    Response: The Flask wrapper object for the file download
    """
    # get token from request args
    token = request.args.get('token', type=str)
    redirect_url = request.url
    return validate_onetime_token(
        pid, record, filename, token, _record_file_factory, redirect_url
    )


def validate_onetime_token(
    pid, record, filename, token,
    _record_file_factory=None, redirect_url=None
):
    """Download a file using a one-time download URL.

    Args:
        pid (PersistentIdentifier): The identifier for the item.
        record (WekoRecord): The record metadata of the item.
        filename (str): The name of the file to download.
        token (str): The one-time token.
        _record_file_factory (callable, optional): A factory function to create
            file objects. Defaults to None, which uses the default
            `record_file_factory`.
        redirect_url (str, optional): URL to redirect if user is not authenticated.
            Defaults to None, which uses the login view.
    Returns:
        Response: The Flask wrapper object for the file download
    """
    # check restricted access is enabled
    if not current_app.config.get("WEKO_ADMIN_RESTRICTED_ACCESS_DISPLAY_FLAG", False):
        return error_response(_('Restricted access is disabled.'), 403)

    # Validate the onetime download token
    is_validated, error_msg = validate_url_download(
        record, filename, token, is_secret_url=False)
    if not is_validated:
        return error_response(error_msg, 403)

    # Locate the file object
    _record_file_factory = _record_file_factory or record_file_factory
    file_object = _record_file_factory(pid, record, filename)
    if not file_object or not file_object.obj:
        return error_response(_('The file "%s" does not exist.') % filename, 404)

    # Update 'extra_info' of the one-time URL object
    url_obj = convert_token_into_obj(token, is_secret_url=False)

    # Check if created by guest user
    if url_obj.is_guest:
        return validate_onetime_guest(url_obj, pid, token, redirect_url)

    # Check if not authenticated or email doesn't match
    if not current_user.is_authenticated or \
        current_user.email != url_obj.user_mail:
        return error_response(_('Invalid token.'), 403)

    # process the file download
    return process_onetime_file_download(
        pid, record, filename, token, _record_file_factory)


def validate_onetime_guest(onetime_url_record, pid, token, onetime_url):
    """Download a file using a one-time download URL.
    Args:
        onetime_url_record (OnetimeURLRecord): The one-time URL record.
        pid (PersistentIdentifier): The identifier for the item.
        token (str): The one-time token.
        onetime_url (str): URL to redirect if user is not authenticated.
    Returns:
        Response: The Flask wrapper object for the file download
    """
    # set pending token and email
    session["user_mail"] = onetime_url_record.user_mail
    session["pending_onetime_token"] = token

    # redirect password_check
    redirect_url = url_for(
        endpoint="invenio_records_ui.recid",
        pid_value=pid.pid_value,
        onetime_url=onetime_url or "",
        v="mailcheckflag"
    )
    return redirect(redirect_url)


def file_download_onetime(pid, record, filename, _record_file_factory=None,
                          **kwargs):
    """Download a file using a one-time download URL.

    Args:
        pid (PersistentIdentifier): The identifier for the item.
        record (WekoRecord): The record metadata of the item.
        filename (str): The name of the file to download.

    Returns:
        Response: The Flask wrapper object for the file download
    """
    def _error_response_text(error_message, status_code=400):
        return error_message, status_code

    # Validate the download request (skipped)
    token = request.args.get('token', type=str)
    is_validated, error_msg = validate_url_download(
        record, filename, token, is_secret_url=False)
    if not is_validated:
        return _error_response_text(error_msg, 403)

    # Check pending token
    if session.get("pending_onetime_token", None) != token:
        return _error_response_text(_('Invalid token.'), 403)

    # Update 'extra_info' of the one-time URL object
    url_obj = convert_token_into_obj(token, is_secret_url=False)

    # Check mail address
    request_body = request.get_json(force=True)
    mail_address = request_body.get('mail_address', None)
    if mail_address != url_obj.user_mail:
        return _error_response_text(_("Could not download file."), 403)

    # Check password (if required)
    input_password = request_body.get('input_password', None)
    restricted_access = AdminSettings.get(name='restricted_access',dict_to_object=False)
    password_for_download = url_obj.extra_info.get("password_for_download", "")
    enable_check_password_for_guest = restricted_access and restricted_access.get('password_enable', False)
    if enable_check_password_for_guest and password_for_download:
        if not input_password or not verify_password(input_password, password_for_download):
            return _error_response_text(_('Invalid verification info.'), 403)

    # Clear pending token
    session.pop("pending_onetime_token", None)
    session.pop("user_mail", None)

    # Process the file download
    return process_onetime_file_download(
        pid, record, filename, token, _record_file_factory,
        error_handler=_error_response_text
    )


def process_onetime_file_download(
    pid, record, filename, token, _record_file_factory=None, error_handler=error_response
):
    """Process a file download using a one-time download URL.
    Args:
        pid (PersistentIdentifier): The identifier for the item.
        record (WekoRecord): The record metadata of the item.
        filename (str): The name of the file to download.
        token (str): The one-time token.
        is_page_access (bool): Flag indicating if the request is from a page access.
        _record_file_factory (callable, optional): A factory function to create
            file objects. Defaults to None, which uses the default
            `record_file_factory`.
    Returns:
        Response: The Flask wrapper object for the file download, or an error
            response if validation fails.
    """
    # Locate the file object
    _record_file_factory = _record_file_factory or record_file_factory
    file_object = _record_file_factory(pid, record, filename)
    if not file_object or not file_object.obj:
        return error_handler(
            _('The file "%s" does not exist.') % filename, status_code=404
        )

    # Update 'extra_info' of the one-time URL object
    url_obj = convert_token_into_obj(token, is_secret_url=False)
    extra_info = url_obj.extra_info
    if extra_info:
        try:
            # 'extra_info' can be changed by this method
            error = check_and_send_usage_report(
                extra_info, url_obj.user_mail ,record, file_object)
            if error:
                return error_handler(error, status_code=403)
            url_obj.update_extra_info(extra_info)
            db.session.commit()
        except SQLAlchemyError as ex:
            current_app.logger.error(f'SQLAlchemy error: {ex}')
            db.session.rollback()
            return error_handler('Unexpected error occurred.', status_code=500)
        except BaseException as ex:
            current_app.logger.error(f'Unexpected error: {ex}')
            db.session.rollback()
            return error_handler('Unexpected error occurred.', status_code=500)

    # Increase the download count and save the download log
    try:
        save_download_log(record, filename, token, is_secret_url=False)
        url_obj.increment_download_count()
    except Exception as e:
        current_app.logger.error(e)
        return error_handler(_('Unexpected error occurred.'), status_code=500)

    return _download_file(
        file_object, False, 'en', file_object.obj, pid, record)


def _is_terms_of_use_only(file_obj:dict , req :dict) -> bool:
    """
        return true if the user can apply and apply workflow is terms_of_use_only
        in case of terms_of_use_only download terms of use is agreed (or terms of use is not setted) 
    Args
        dict:file_obj :file object
        dict:req :request.args
    Returns
        bool
    """

    consent:bool = req.get('terms_of_use_only',False)
    if not consent :
        return False

    provides = file_obj.get("provide" , [])
    workflow_id = ""
    for provide in provides :
        if current_user.is_authenticated :
            roles = list(current_user.roles or [])
            for role in roles :
                if provide.get("role", "") == str(role.id) :
                    workflow_id = provide.get("workflow", "")
                    break
        else :
            if provide.get("role", "") == "none_loggin" :
                workflow_id = provide.get("workflow", "")

        if workflow_id != "" :
            break

    return is_terms_of_use_only(workflow_id) if workflow_id != "" else False


def file_download_secret(pid, record, filename, _record_file_factory=None,
                         **kwargs):
    """Download a file using a secret URL.

    Args:
        pid (PersistentIdentifier): The identifier for the item.
        record (WekoRecord): The record metadata of the item.
        filename (str): The name of the file to download.

    Returns:
        Response: The Flask wrapper object for the file download.
    """
    # Validate the download request
    token = request.args.get('token', type=str)
    is_validated, error_msg = (
        validate_url_download(record, filename, token, is_secret_url=True))
    if not is_validated:
        return error_response(error_msg, 403)

    # Locate the file object
    _record_file_factory = _record_file_factory or record_file_factory
    file_object = _record_file_factory(pid, record, filename)
    if not file_object or not file_object.obj:
        return error_response(_('The file "%s" does not exist.') % filename, 404)

    # Set language for PDF cover page
    lang = 'en'
    if current_user.is_authenticated :
        user_profile = UserProfile.get_by_userid(current_user.get_id())
        lang = user_profile.language if user_profile else 'en'

    # Increase the download count and save the download log
    url_obj = convert_token_into_obj(token, is_secret_url=True)
    try:
        save_download_log(record, filename, token, is_secret_url=True)
        url_obj.increment_download_count()
    except Exception as e:
        current_app.logger.error(e)
        return error_response(_('Unexpected error occurred.'), 500)

    return _download_file(
        file_object, False, lang, file_object.obj, pid, record)


def file_list_ui(record, files):
    """File List Ui.

    :param record: All metadata of a record.
    :param files: File metadata list(only attribute_type "file").
    """
    if not files:
        abort(404)

    # Language setting
    from weko_user_profiles.config import USERPROFILES_LANGUAGE_LIST
    language = request.headers.get('Accept-Language')
    if not language in [lang[0] for lang in USERPROFILES_LANGUAGE_LIST[1:]]:
        language = 'en'
    get_locale().language = language

    item_title = record.get_titles

    temp_path = tempfile.TemporaryDirectory(
        prefix=current_app.config.get('WEKO_RECORDS_UI_FILELIST_TMP_PREFIX'))

    # Set export folder
    export_path = temp_path.name + '/' + datetime.utcnow().strftime("%Y%m%d%H%M%S")
    files_export_path = export_path + '/data'
    os.makedirs(files_export_path)

    # Exclude thumbnails
    filenames = [f.get('filename') for f in files]
    target_files = [f for f in record.files if f.info().get('filename') in filenames]

    # Export files
    available_files = []
    for file in target_files:
        if check_file_download_permission(record, file.info()):
            available_files.append(file)
            file_buffered = file.obj.file.storage().open()
            temp_file = open(
                files_export_path + '/' + file.obj.basename, 'wb')
            temp_file.write(file_buffered.read())
            temp_file.close()
    if not available_files:
        raise AvailableFilesNotFoundRESTError()

    # Create TSV file
    from .utils import create_tsv
    with open(f'{export_path}/file_list.tsv', 'w', encoding="utf-8") as tsv_file:
        tsv_file.write(create_tsv(available_files, language).getvalue())

    # Create download file
    shutil.make_archive(export_path, 'zip', export_path)

    return send_file(
        export_path + '.zip',
        as_attachment=True,
        attachment_filename=item_title + '.zip'
    )
