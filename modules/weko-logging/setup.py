# -*- coding: utf-8 -*-

"""Module providing logging capabilities."""

import os

from setuptools import find_packages, setup

readme = open("README.rst").read()
history = open("CHANGES.rst").read()

tests_require = [
    "coverage>=4.5.4",
    "mock>=3.0.5",
    "pytest>=5.4.3",
    "pytest-cache>=1.0",
    "pytest-cov>=2.10.1",
    "pytest-pep8>=1.0.6",
    "pytest-invenio>=1.3.4",
    "responses>=0.10.3",
    "pytest-runner>=5.3.2",
]

extras_require = {
    "docs": [
        "Sphinx>=1.5.1",
    ],
    "tests": tests_require,
}

extras_require["all"] = []
for reqs in extras_require.values():
    extras_require["all"].extend(reqs)

setup_requires = [
    "Babel>=2.5.1",
]

install_requires = [
    "Flask>=0.11.1",
    "Flask-BabelEx>=0.9.2",
]

packages = find_packages()


# Get the version string. Cannot be done with import!
g = {}
with open(os.path.join("weko_logging", "version.py"), "rt") as fp:
    exec(fp.read(), g)
    version = g["__version__"]

setup(
    name="weko-logging",
    version=version,
    description=__doc__,
    long_description=readme + "\n\n" + history,
    keywords="weko logging",
    license="MIT",
    author="National Institute of Informatics",
    author_email="wekosoftware@nii.ac.jp",
    url="https://github.com/wekosoftware/weko-logging",
    packages=packages,
    zip_safe=False,
    include_package_data=True,
    platforms="any",
    entry_points={
        "invenio_base.apps": [
            "weko_logging_fs = weko_logging.fs:WekoLoggingFS",
            "weko_logging_user_activity = weko_logging.audit:WekoLoggingUserActivity",
        ],
        "invenio_base.api_apps": [
            "weko_logging_fs = weko_logging.fs:WekoLoggingFS",
            "weko_logging_user_activity = weko_logging.audit:WekoLoggingUserActivity",
        ],
        "invenio_i18n.translations": [
            "messages = weko_logging",
        ],
        "invenio_admin.views": [
            "weko_logging_admin_log_export = weko_logging.admin:log_export_admin_view",
        ],
        "invenio_db.alembic": [
            "weko_logging = weko_logging:alembic",
        ],
        "invenio_db.models": [
            "weko_logging = weko_logging.models",
        ],
        "invenio_assets.bundles": [
            "weko_logging_export_css = "
            "weko_logging.bundles:weko_logging_export_css",
            "weko_logging_export_js = "
            "weko_logging.bundles:weko_logging_export_js",
        ],
    },
    extras_require=extras_require,
    install_requires=install_requires,
    setup_requires=setup_requires,
    tests_require=tests_require,
)
