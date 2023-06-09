# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 National Institute of Informatics.
#
# WEKO-Indextree-Journal is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Module tests."""

from __future__ import absolute_import, print_function

from flask import Flask

from weko_indextree_journal import WekoIndextreeJournal, WekoIndextreeJournalREST

# .tox/c1/bin/pytest --cov=weko_indextree_journal tests/test_weko_indextree_journal.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-indextree-journal/.tox/c1/tmp
def test_version():
    """Test version import."""
    from weko_indextree_journal import __version__
    assert __version__

# .tox/c1/bin/pytest --cov=weko_indextree_journal tests/test_weko_indextree_journal.py::test_init -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-indextree-journal/.tox/c1/tmp
def test_init():
    """Test extension initialization."""
    app = Flask('testapp')
    app.config.update(
        WEKO_INDEXTREE_JOURNAL_REST_ENDPOINTS = dict(
            tid=dict(
                record_class='weko_indextree_journal.api:Journals',
                admin_indexjournal_route='/admin/indexjournal/<int:journal_id>',
                journal_route='/admin/indexjournal',
                # item_tree_journal_route='/tree/journal/<int:pid_value>',
                # journal_move_route='/tree/journal/move/<int:index_id>',
                default_media_type='application/json',
                create_permission_factory_imp='weko_indextree_journal.permissions:indextree_journal_permission',
                read_permission_factory_imp='weko_indextree_journal.permissions:indextree_journal_permission',
                update_permission_factory_imp='weko_indextree_journal.permissions:indextree_journal_permission',
                delete_permission_factory_imp='weko_indextree_journal.permissions:indextree_journal_permission',
            )
        ),
    )
    ext = WekoIndextreeJournal(app)
    assert 'weko-indextree-journal' in app.extensions
    ext_rest = WekoIndextreeJournalREST(app)
    assert 'weko-indextree-journal-rest' in app.extensions
    
    app = Flask('testapp')
    app.config.update(
        WEKO_INDEXTREE_JOURNAL_REST_ENDPOINTS = dict(
            tid=dict(
                record_class='weko_indextree_journal.api:Journals',
                admin_indexjournal_route='/admin/indexjournal/<int:journal_id>',
                journal_route='/admin/indexjournal',
                # item_tree_journal_route='/tree/journal/<int:pid_value>',
                # journal_move_route='/tree/journal/move/<int:index_id>',
                default_media_type='application/json',
                create_permission_factory_imp='weko_indextree_journal.permissions:indextree_journal_permission',
                read_permission_factory_imp='weko_indextree_journal.permissions:indextree_journal_permission',
                update_permission_factory_imp='weko_indextree_journal.permissions:indextree_journal_permission',
                delete_permission_factory_imp='weko_indextree_journal.permissions:indextree_journal_permission',
            )
        ),
    )
    app.config["BASE_EDIT_TEMPLATE"] = "test/test"
    ext = WekoIndextreeJournal(app)

# .tox/c1/bin/pytest --cov=weko_indextree_journal tests/test_weko_indextree_journal.py::test_init_withoutapp -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-indextree-journal/.tox/c1/tmp
def test_init_withoutapp():
    app = Flask('testapp')
    app.config.update(
        WEKO_INDEXTREE_JOURNAL_REST_ENDPOINTS = dict(
            tid=dict(
                record_class='weko_indextree_journal.api:Journals',
                admin_indexjournal_route='/admin/indexjournal/<int:journal_id>',
                journal_route='/admin/indexjournal',
                # item_tree_journal_route='/tree/journal/<int:pid_value>',
                # journal_move_route='/tree/journal/move/<int:index_id>',
                default_media_type='application/json',
                create_permission_factory_imp='weko_indextree_journal.permissions:indextree_journal_permission',
                read_permission_factory_imp='weko_indextree_journal.permissions:indextree_journal_permission',
                update_permission_factory_imp='weko_indextree_journal.permissions:indextree_journal_permission',
                delete_permission_factory_imp='weko_indextree_journal.permissions:indextree_journal_permission',
            )
        ),
    )
    ext = WekoIndextreeJournal()
    assert 'weko-indextree-journal' not in app.extensions
    ext.init_app(app)
    assert 'weko-indextree-journal' in app.extensions
    ext_rest = WekoIndextreeJournalREST()
    assert 'weko-indextree-journal-rest' not in app.extensions
    ext_rest.init_app(app)
    assert 'weko-indextree-journal-rest' in app.extensions
    
