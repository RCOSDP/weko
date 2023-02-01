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


"""Groups Settings Blueprint."""

from flask import Blueprint, flash, jsonify, redirect, render_template, \
    request, url_for, current_app
import bleach
from flask_babelex import gettext as _
from flask_breadcrumbs import register_breadcrumb
from flask_login import current_user, login_required
from flask_menu import register_menu
from invenio_accounts.models import User
from invenio_admin.proxies import current_admin
from six.moves.urllib.parse import urlparse
from sqlalchemy.exc import IntegrityError
from invenio_db import db

from .forms import GroupForm, NewMemberForm
from .models import Group, Membership

blueprint = Blueprint(
    'weko_groups',
    __name__,
    template_folder='templates',
    static_folder='static',
    url_prefix='/accounts/settings/groups',
)


# default_breadcrumb_root(blueprint, '.settings.groups')


allow_tags = [
    'abbr',
    'acronym',
    'b',
    'blockquote',
    'br',
    'code',
    'div',
    'em',
    'h1',
    'h2',
    'h3',
    'h4',
    'h5',
    'i',
    'li',
    'ol',
    'p',
    'pre',
    'span',
    'strike',
    'strong',
    'sub',
    'sup',
    'u',
    'ul',
]
@blueprint.app_template_filter('sanitize_html_group')
def sanitize_html_group(value):
    """Sanitizes HTML using the bleach library."""
    return bleach.clean(
        value,
        tags=allow_tags,
        strip=False
    ).strip()


def get_group_name(id_group):
    """
    Use for breadcrumb dynamic_list_constructor.

    :param id_group: group id.
    :return: Group name.
    """
    group = Group.query.get(id_group)
    if group is not None:
        return group.escape_name


@blueprint.route('/groupcount', methods=['GET'])
def groupcount():
    """
    Get group count for current user.

    :return: Group count of current user in json type.
    """
    groups = Group.query_by_user(current_user, eager=True)
    group_map = {}
    for group in groups:
        count = group.members_count()
        group_map[group.get_id()] = count
    lists = type(Membership.group)
    return jsonify(count=group_map,
                   membership_group=str(lists))


@blueprint.route('/grouplist', methods=['GET'])
def grouplist():
    """
    Get logined group list info.

    :return: Logined grouplist in json type.
    """
    obj = Group.get_group_list()
    return jsonify(obj)


def _has_admin_access():
    """Use to check if a user has any admin access."""
    return current_user.is_authenticated and current_admin \
        .permission_factory(current_admin.admin.index_view).can()


@blueprint.route('/index', methods=['GET'])
@blueprint.route('/', methods=['GET'])
@register_menu(
    blueprint, 'settings.groups',
    _('%(icon)s Groups', icon='<i class="fa fa-users fa-fw"></i>'),
    order=13,
    active_when=lambda: request.endpoint.startswith("groups_settings.")
)
@register_breadcrumb(blueprint, 'breadcrumbs.settings.group', _('Groups'))
@login_required
def index():
    """List all user memberships."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 5, type=int)
    q = request.args.get('q', '')

    groups = Group.query_by_user(current_user, eager=True)
    if q:
        groups = Group.search(groups, q)
    groups = groups.paginate(page, per_page=per_page)

    requests = Membership.query_requests(current_user).count()
    invitations = Membership.query_invitations(current_user).count()
    is_admin = _has_admin_access()

    return render_template(
        'weko_groups/index.html',
        groups=groups,
        requests=requests,
        invitations=invitations,
        page=page,
        per_page=per_page,
        q=q,
        is_admin=is_admin
    )


@blueprint.route('/requests', methods=['GET'])
@register_breadcrumb(blueprint, 'breadcrumbs.settings.request', _('Requests'))
@login_required
def requests():
    """List all pending memberships, listed only for group admins."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 5, type=int)
    memberships = Membership.query_requests(current_user).all()

    return render_template(
        'weko_groups/pending.html',
        memberships=memberships,
        requests=True,
        page=page,
        per_page=per_page,
    )


@blueprint.route('/invitations', methods=['GET'])
@register_breadcrumb(
    blueprint,
    'breadcrumbs.settings.invitations',
    _('Invitations'))
@login_required
def invitations():
    """List all user pending memberships."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 5, type=int)
    memberships = Membership.query_invitations(current_user, eager=True).all()

    return render_template(
        'weko_groups/pending.html',
        memberships=memberships,
        page=page,
        per_page=per_page,
    )


@blueprint.route('/new', methods=['GET', 'POST'])
@register_breadcrumb(blueprint, 'breadcrumbs.settings.group.new', _('New'))
@login_required
def new():
    """
    Create new group.

    :return: New group page.
    """
    form = GroupForm(request.form)

    if form.validate_on_submit():
        try:
            formdata = remove_csrf(form)

            group = Group.create(admins=[current_user], **formdata)

            flash(_('Group "%(name)s" created', name=group.name), 'success')
            return redirect(url_for(".index"))
        except IntegrityError:
            flash(_('Group creation failure'), 'error')

    return render_template(
        "weko_groups/new.html",
        form=form,
    )


@blueprint.route('/<int:group_id>/manage', methods=['GET', 'POST'])
@blueprint.route('/<int:group_id>/', methods=['GET', 'POST'])
@register_breadcrumb(
    blueprint, 'breadcrumbs.settings.manage', _('Manage'),
    dynamic_list_constructor=lambda:
    [{'text': get_group_name(request.view_args['group_id'])},
     {'text': _('Manage')}]
)
@login_required
def manage(group_id):
    """
    Manage your group.

    :param group_id: Group id.
    :return: New group page.
    """
    group = Group.query.get_or_404(group_id)
    form = GroupForm(request.form, obj=group)

    if form.validate_on_submit():
        if group.can_edit(current_user):
            try:
                formdata = remove_csrf(form)
                group.update(**formdata)
                flash(_('Group "%(name)s" was updated', name=group.name),
                      'success')
            except Exception as e:
                flash(str(e), 'error')
                return render_template(
                    "weko_groups/new.html",
                    form=form,
                    group=group,
                )
        else:
            flash(
                _(
                    'You cannot edit group %(group_name)s',
                    group_name=group.name
                ),
                'error'
            )

    return render_template(
        "weko_groups/new.html",
        form=form,
        group=group,
    )


@blueprint.route('/<int:group_id>/delete', methods=['POST'])
@login_required
def delete(group_id):
    """
    Delete group.

    :param group_id: Group id.
    :return: Group index page.
    """
    group = Group.query.get_or_404(group_id)

    if group.can_edit(current_user):
        try:
            group.delete()
        except Exception as e:
            flash(str(e), "error")
            return redirect(url_for(".index"))

        flash(_('Successfully removed group "%(group_name)s"',
                group_name=group.name), 'success')
        return redirect(url_for(".index"))

    flash(
        _(
            'You cannot delete the group %(group_name)s',
            group_name=group.name
        ),
        'error'
    )
    return redirect(url_for(".index"))


@blueprint.route('/<int:group_id>/members', methods=['GET', 'POST'])
@login_required
@register_breadcrumb(
    blueprint, 'breadcrumbs.settings.group.members', _('Members'),
    dynamic_list_constructor=lambda:
    [{'text': get_group_name(request.view_args['group_id'])},
     {'text': _('Members')}]
)
def members(group_id):
    """
    List user group members.

    :param group_id: Group id.
    :return: Group member page.
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 5, type=int)
    q = request.args.get('q', '')
    s = request.args.get('s', '')

    group = Group.query.get_or_404(group_id)
    if group.can_see_members(current_user):
        members = Membership.query_by_group(group_id, with_invitations=True)
        if q:
            members = Membership.search(members, q)
        if s:
            members = Membership.order(members, Membership.state, s)
        members = members.paginate(page, per_page=per_page)

        return render_template(
            "weko_groups/members.html",
            group=group,
            members=members,
            page=page,
            per_page=per_page,
            q=q,
            s=s,
        )

    flash(
        _(
            'You are not allowed to see members of this group %(group_name)s.',
            group_name=group.name
        ),
        'error'
    )
    return redirect(url_for('.index'))


@blueprint.route('/<int:group_id>/leave', methods=['POST'])
@login_required
def leave(group_id):
    """
    Leave group.

    :param group_id: Group id.
    :return: Group index page.
    """
    group = Group.query.get_or_404(group_id)

    if group.can_leave(current_user):
        try:
            group.remove_member(current_user)
        except Exception as e:
            flash(str(e), "error")
            return redirect(url_for('.index'))

        flash(
            _(
                'You have successfully left %(group_name)s group.',
                group_name=group.name
            ),
            'success'
        )
        return redirect(url_for('.index'))

    flash(
        _(
            'You cannot leave the group %(group_name)s',
            group_name=group.name
        ),
        'error'
    )
    return redirect(url_for('.index'))


@blueprint.route('/<int:group_id>/members/<int:user_id>/approve',
                 methods=['POST'])
@login_required
def approve(group_id, user_id):
    """
    Approve a user.

    :param group_id: Group id.
    :param user_id: User id.
    :return: Group index page or group page of group_name.
    """
    membership = Membership.query.get_or_404((user_id, group_id))
    group = membership.group

    if group.can_edit(current_user):
        try:
            membership.accept()
        except Exception as e:
            flash(str(e), 'error')
            return redirect(url_for('.requests', group_id=membership.group.id))

        flash(_('%(user)s accepted to %(group_name)s group.',
                user=membership.user.email,
                group_name=membership.group.name), 'success')
        return redirect(url_for('.requests', group_id=membership.group.id))

    flash(
        _(
            'You cannot approve memberships for the group %(group_name)s',
            group_name=group.name
        ),
        'error'
    )
    return redirect(url_for('.index'))


@blueprint.route('/<int:group_id>/members/<int:user_id>/remove',
                 methods=['POST'])
@login_required
def remove(group_id, user_id):
    """
    Remove user from a group.

    :param group_id: Group id.
    :param user_id: User id.
    :return: Group index page or group page of group_name.
    """
    group = Group.query.get_or_404(group_id)
    user = User.query.get_or_404(user_id)

    if group.can_edit(current_user):
        try:
            group.remove_member(user)
        except Exception as e:
            flash(str(e), "error")
            return redirect(urlparse(request.referrer).path)

        flash(_('User %(user_email)s was removed from %(group_name)s group.',
                user_email=user.email, group_name=group.name), 'success')
        return redirect(urlparse(request.referrer).path)

    flash(
        _(
            'You cannot delete users of the group %(group_name)s',
            group_name=group.name
        ),
        'error'
    )
    return redirect(url_for('.index'))


@blueprint.route('/<int:group_id>/members/accept',
                 methods=['POST'])
@login_required
def accept(group_id):
    """
    Accpet pending invitation.

    :param group_id: Group id.
    :return: Invitation page.
    """
    membership = Membership.query.get_or_404((current_user.get_id(), group_id))

    # no permission check, because they are checked during Memberships creating

    try:
        membership.accept()
    except Exception as e:
        flash(str(e), 'error')
        return redirect(url_for('.invitations', group_id=membership.group.id))

    flash(_('You are now part of %(group_name)s group.',
            user=membership.user.email,
            group_name=membership.group.name), 'success')
    return redirect(url_for('.invitations', group_id=membership.group.id))


@blueprint.route('/<int:group_id>/members/reject',
                 methods=['POST'])
@login_required
def reject(group_id):
    """
    Reject invitation.

    :param group_id: Group id.
    :returns: Invitations page.
    """
    membership = Membership.query.get_or_404((current_user.get_id(), group_id))
    user = membership.user
    group = membership.group

    # no permission check, because they are checked during Memberships creating

    try:
        membership.reject()
    except Exception as e:
        flash(str(e), 'error')
        return redirect(url_for('.invitations', group_id=membership.group.id))

    flash(_('You have rejected invitation to %(group_name)s group.',
            user=user.email,
            group_name=group.name), 'success')
    return redirect(url_for('.invitations', group_id=membership.group.id))


@blueprint.route('/<int:group_id>/members/new', methods=['GET', 'POST'])
@login_required
@register_breadcrumb(
    blueprint,
    'breadcrumbs.settings.newmember',
    _('NewMember')
)
def new_member(group_id):
    """
    Add (invite) new member.

    :param group_id: Group id.
    :return: New member page or member page of given group id.
    """
    group = Group.query.get_or_404(group_id)

    if group.can_invite_others(current_user):
        form = NewMemberForm()

        if form.validate_on_submit():
            emails = filter(None, form.data['emails'].splitlines())
            group.invite_by_emails(emails)
            flash(_('Requests sent!'), 'success')
            return redirect(url_for('.members', group_id=group.id))

        return render_template(
            "weko_groups/new_member.html",
            group=group,
            form=form
        )

    flash(
        _(
            'You cannot invite users or yourself (i.e. join) to the group '
            '%(group_name)s',
            group_name=group.name
        ),
        'error'
    )
    return redirect(url_for('.index'))


def remove_csrf(form):
    """
    Remove csrf sign in th form.

    :param form: Form object.
    :return:
    """
    map = {}
    for key, val in form.data.items():
        if key != 'csrf_token':
            map[key] = val
    return map

@blueprint.teardown_request
def dbsession_clean(exception):
    current_app.logger.debug("weko_groups dbsession_clean: {}".format(exception))
    if exception is None:
        try:
            db.session.commit()
        except:
            db.session.rollback()
    db.session.remove()