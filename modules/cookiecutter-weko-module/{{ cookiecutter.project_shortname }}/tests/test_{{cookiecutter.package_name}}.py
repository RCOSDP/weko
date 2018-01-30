{% include 'misc/header.py' %}
"""Module tests."""

from flask import Flask

from {{ cookiecutter.package_name }} import {{ cookiecutter.extension_class }}


def test_version():
    """Test version import."""
    from {{ cookiecutter.package_name }} import __version__
    assert __version__


def test_init():
    """Test extension initialization."""
    app = Flask('testapp')
    ext = {{ cookiecutter.extension_class }}(app)
    assert '{{ cookiecutter.project_shortname}}' in app.extensions

    app = Flask('testapp')
    ext = {{ cookiecutter.extension_class }}()
    assert '{{ cookiecutter.project_shortname}}' not in app.extensions
    ext.init_app(app)
    assert '{{ cookiecutter.project_shortname}}' in app.extensions


def test_view(app):
    """Test view."""
    {{ cookiecutter.extension_class}}(app)
    with app.test_client() as client:
        res = client.get("/")
        assert res.status_code == 200
        assert 'Welcome to {{ cookiecutter.project_name | lower }}' in str(res.data)
