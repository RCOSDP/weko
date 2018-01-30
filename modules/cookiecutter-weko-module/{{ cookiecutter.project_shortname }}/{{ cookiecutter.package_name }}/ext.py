{% include 'misc/header.py' %}
"""Flask extension for {{ cookiecutter.project_name | lower }}."""

from . import config
from .views import blueprint


class {{ cookiecutter.extension_class }}(object):
    """{{ cookiecutter.project_name | lower }} extension."""

    def __init__(self, app=None):
        """Extension initialization.

        :param app: The Flask application. (Default: ``None``)
        """
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Flask application initialization.

        :param app: The Flask application.
        """
        self.init_config(app)
        app.register_blueprint(blueprint)
        app.extensions['{{ cookiecutter.project_shortname}}'] = self

    def init_config(self, app):
        """Initialize configuration.

        :param app: The Flask application.
        """
        # Use theme's base template if theme is installed
        if 'BASE_TEMPLATE' in app.config:
            app.config.setdefault(
                '{{ cookiecutter.config_prefix}}_BASE_TEMPLATE',
                app.config['BASE_TEMPLATE'],
            )
        for k in dir(config):
            if k.startswith('{{ cookiecutter.config_prefix}}_'):
                app.config.setdefault(k, getattr(config, k))
