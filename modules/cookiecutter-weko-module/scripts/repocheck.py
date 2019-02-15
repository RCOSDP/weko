# -*- coding: utf-8 -*-
#
# This file is part of Cookiecutter - Invenio Module Template
# Copyright (C) 2016, 2017 CERN
#
# Cookiecutter - Invenio Module Template is free software; you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation; either version 2 of
# the License, or (at your option) any later version.
#
# Cookiecutter - Invenio Module Template is distributed in the hope that it
# will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# Cookiecutter - Invenio Module Template; if not, see
# <http://www.gnu.org/licenses>.
#
# In applying this license, CERN does not waive the privileges and immunities
# granted to it by virtue of its status as an Intergovernmental Organization
# or submit itself to any jurisdiction.

r"""Script for checking repository against cookiecutter output.

Usage:

.. code-block:: console

   $ pip install click
   $ cookiecutter gh:inveniosoftware/cookiecutter-invenio-module
   $ python repocheck.py ~/original/invenio-fungenerator \
     ~/new/invenio-fungenerator

Note: When running cookiecutter be sure to use same input values as when the
repository was orignally generated.
"""

import os
import subprocess
from os.path import join

import click

manual_diff = [
    'setup.py',
    '.travis.yml',
    'tests/conftest.py',
    'examples/app-fixtures.sh',
    'examples/app-setup.sh',
    'examples/app-teardown.sh',
    'examples/app.py',
    'tests/test_examples_app.py',
    'requirements-devel.txt',
]

diff_files = [
    '.editorconfig',
    '.tx/config',
    'AUTHORS.rst',
    'CHANGES.rst',
    'docs/conf.py',
    'INSTALL.rst',
    '{package_name}/version.py',
    'MANIFEST.in',
    'README.rst',
    'RELEASE-NOTES.rst',
]

identical_files = [
    '.dockerignore',
    '.gitignore',
    'babel.ini',
    'CONTRIBUTING.rst',
    'docs/authors.rst',
    'docs/changes.rst',
    'docs/configuration.rst',
    'docs/contributing.rst',
    'docs/index.rst',
    'docs/installation.rst',
    'docs/license.rst',
    'docs/make.bat',
    'docs/Makefile',
    'docs/requirements.txt',
    'docs/usage.rst',
    'LICENSE',
    'pytest.ini',
    'run-tests.sh',
    'setup.cfg',
]

identical_setuppy_attrs = [
  'name',
  'author',
  'author-email',
  'contact',
  'contact-email',
  'url',
  'license',
  'description',
]


def run_in_dir(path, cmd):
    """Run command in directory."""
    cur_dir = os.getcwd()
    os.chdir(path)
    output = subprocess.check_output(cmd, shell=True).decode('utf-8')
    os.chdir(cur_dir)
    return output


def diff_file(src, dst, f):
    """Diff a file in src and dst."""
    # Skip the lines containing copyright year in the header license
    cmd = 'diff -I "Copyright (C) .* CERN." {src} {dst}'.format(
        src=join(src, f), dst=join(dst, f))
    try:
        subprocess.check_output(cmd, shell=True).decode('utf-8')
        # Exit code 0 means no difference
        return ""
    except subprocess.CalledProcessError as e:
        if e.returncode >= 0:
            return e.output
        raise


def equal_content(src, dst, f):
    """Check if file content is equal."""
    return diff_file(src, dst, f) == ""


def equal_setuppy_attr(src, dst, attr):
    src_out = run_in_dir(src, 'python setup.py --{attr}'.format(attr=attr))
    dst_out = run_in_dir(dst, 'python setup.py --{attr}'.format(attr=attr))
    return src_out == dst_out


def check_setupy(src, dst, attrs):
    for a in attrs:
        if not equal_setuppy_attr(src, dst, a):
            click.secho('ERROR: setup.py:{0} is out of sync.'.format(a))


def check_identical_files(src, dst, files):
    """Check if files in source matches files in destination."""
    for f in files:
        try:
            if not equal_content(src, dst, f):
                click.secho('ERROR: {0} is out of sync.'.format(f))
        except IOError as e:
            click.secho('ERROR: {0}'.format(e))


def get_package_name(dst):
    """Get the package name e.g.: 'invenio-fungenerator'."""
    with open(join(dst, '.editorconfig'), 'r') as fp:
        for line in fp.readlines():
            if line.startswith('known_first_party'):
                return line.partition(' = ')[-1].partition(',')[0].strip()


def diff_similar_files(src, dst, files):
    """Diff files which are supposed to be very similar."""
    for f in files:
        click.secho('Diff of {0}'.format(f), fg='cyan')
        click.echo(diff_file(src, dst, f))


@click.command()
@click.argument('repo-dir', type=click.Path(exists=True, file_okay=False))
@click.argument(
    'cookiecutter-output-dir', type=click.Path(exists=True, file_okay=False))
def run(repo_dir, cookiecutter_output_dir):
    """Compare repository against CookieCutter output."""
    click.secho(
        'Please check diff output for almost identical files...', fg='green')

    # Format the diff files with the package name
    package_name = get_package_name(cookiecutter_output_dir)
    f_diff_files = [f.format(package_name=package_name) for f in diff_files]

    diff_similar_files(repo_dir, cookiecutter_output_dir, f_diff_files)
    click.secho('Checking identical files...', fg='green')
    check_identical_files(repo_dir, cookiecutter_output_dir, identical_files)
    click.secho('Please check following files manually:', fg='yellow')
    for f in manual_diff:
        print(f)
    click.secho('Checking identical setup.py attributes...', fg='green')
    check_setupy(repo_dir, cookiecutter_output_dir, identical_setuppy_attrs)


if __name__ == '__main__':
    run()
