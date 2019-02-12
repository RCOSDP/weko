{% include 'misc/header.py' %}
"""{{ cookiecutter.description }}"""

from __future__ import absolute_import, print_function

from flask_babelex import gettext as _

from . import config


class {{ cookiecutter.extension_class }}(object):
    """{{ cookiecutter.project_name}} extension."""

    def __init__(self, app=None):
        """Extension initialization."""
        # TODO: This is an example of translation string with comment. Please
        # remove it.
        # NOTE: This is a note to a translator.
        _('A translation string')
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Flask application initialization."""
        self.init_config(app)
        app.extensions['{{ cookiecutter.project_shortname}}'] = self

    def init_config(self, app):
        """Initialize configuration."""
        # Use theme's base template if theme is installed
        if 'BASE_TEMPLATE' in app.config:
            app.config.setdefault(
                '{{ cookiecutter.config_prefix}}_BASE_TEMPLATE',
                app.config['BASE_TEMPLATE'],
            )
        for k in dir(config):
            if k.startswith('{{ cookiecutter.config_prefix}}_'):
                app.config.setdefault(k, getattr(config, k))
