{% include 'misc/header.py' %}
"""Blueprint for {{ cookiecutter.project_name | lower }}."""


from flask import Blueprint, render_template
from flask_babelex import gettext as _

blueprint = Blueprint(
    '{{ cookiecutter.package_name }}',
    __name__,
    template_folder='templates',
    static_folder='static',
)


@blueprint.route("/")
def index():
    """Render a basic view."""
    return render_template(
        "{{ cookiecutter.package_name }}/index.html",
        module_name=_('{{ cookiecutter.project_name | lower }}'))
