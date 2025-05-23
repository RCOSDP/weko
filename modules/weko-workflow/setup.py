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

"""Module of weko-workflow."""

import os

from setuptools import find_packages, setup

readme = open('README.rst').read()
history = open('CHANGES.rst').read()

tests_require = [
    'coverage>=4.5.3,<5.0.0',
    'mock>=3.0.0,<4.0.0',
    'pytest>=4.6.4,<5.0.0',
    'pytest-cache',
    'pytest-cov',
    'pytest-pep8',
    'pytest-invenio',
    'responses',
]

extras_require = {
    'docs': [
        'Sphinx>=1.5.1',
    ],
    'tests': tests_require,
}

extras_require['all'] = []
for reqs in extras_require.values():
    extras_require['all'].extend(reqs)

setup_requires = [
    'Babel>=1.3',
    'pytest-runner>=3.0.0,<5',
]

install_requires = [
    'Flask>=0.11.1',
    'Flask-BabelEx>=0.9.2',
]

packages = find_packages()


# Get the version string. Cannot be done with import!
g = {}
with open(os.path.join('weko_workflow', 'version.py'), 'rt') as fp:
    exec(fp.read(), g)
    version = g['__version__']

setup(
    name='weko-workflow',
    version=version,
    description=__doc__,
    long_description=readme + '\n\n' + history,
    keywords='weko workflow',
    license='GPLv2',
    author='National Institute of Informatics',
    author_email='wekosoftware@nii.ac.jp',
    url='https://github.com/wekosoftware/weko-workflow',
    packages=packages,
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    entry_points={
        'flask.commands': [
            'workflow = weko_workflow.cli:workflow',
        ],
        'invenio_celery.tasks': [
            'weko_workflow = weko_workflow.tasks',
        ],
        'invenio_base.apps': [
            'weko_workflow = weko_workflow:WekoWorkflow',
        ],
        'invenio_base.api_apps': [
            'weko_workflow_rest = weko_workflow:WekoWorkflow',
            'weko_workflow_rest2 = weko_workflow.ext:WekoWorkflowREST',
        ],
        'invenio_admin.views': [
            'weko_workflow = weko_workflow.admin:workflow_adminview',
            'weko_flow = weko_workflow.admin:flow_adminview',
        ],
        'invenio_assets.bundles': [
            'workflow_js = weko_workflow.bundles:js_workflow',
            'workflow_item_link_js = weko_workflow.bundles:js_item_link',
            'workflow_activity_list_js = '
            'weko_workflow.bundles:js_activity_list',
            'workflow_iframe_js = weko_workflow.bundles:js_iframe',
            'workflow_oa_policy_js = weko_workflow.bundles:js_oa_policy',
            'workflow_css = weko_workflow.bundles:css_workflow',
            'workflow_datepicker_css ='
            ' weko_workflow.bundles:css_datepicker_workflow',
            'workflow_identifier_grant_js = '
            'weko_workflow.bundles:js_identifier_grant',
            'workflow_quit_confirmation_js = '
            'weko_workflow.bundles:js_quit_confirmation',
            'workflow_lock_activity_js = '
            'weko_workflow.bundles:js_lock_activity',
            'workflow_detail_admin_js = '
            'weko_workflow.bundles:js_admin_workflow_detail',
            'flow_detail_admin_js = '
            'weko_workflow.bundles:js_admin_flow_detail',
        ],
        'invenio_i18n.translations': [
            'messages = weko_workflow',
        ],
        'invenio_db.models': [
            'weko_workflow = weko_workflow.models',
        ],
        'invenio_db.alembic': [
            'weko_workflow = weko_workflow:alembic',
        ],
        'invenio_oauth2server.scopes': [
            'weko_workflow = weko_workflow.scopes:activity_scope',
        ],
    },
    extras_require=extras_require,
    install_requires=install_requires,
    setup_requires=setup_requires,
    tests_require=tests_require,
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Development Status :: 1 - Planning',
    ],
)
