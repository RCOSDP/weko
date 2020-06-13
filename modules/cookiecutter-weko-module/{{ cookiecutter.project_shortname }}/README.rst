{% include 'misc/header.rst' %}
{{ '=' * (cookiecutter.project_name|length + 2) }}
 {{ cookiecutter.project_name }}
{{ '=' * (cookiecutter.project_name|length + 2) }}

.. image:: https://img.shields.io/travis/{{ cookiecutter.github_repo }}.svg
        :target: https://travis-ci.org/{{ cookiecutter.github_repo }}

.. image:: https://img.shields.io/coveralls/{{ cookiecutter.github_repo }}.svg
        :target: https://coveralls.io/r/{{ cookiecutter.github_repo }}

.. image:: https://img.shields.io/github/tag/{{ cookiecutter.github_repo }}.svg
        :target: https://github.com/{{ cookiecutter.github_repo }}/releases

.. image:: https://img.shields.io/pypi/dm/{{ cookiecutter.project_shortname }}.svg
        :target: https://pypi.python.org/pypi/{{ cookiecutter.project_shortname }}

.. image:: https://img.shields.io/github/license/{{ cookiecutter.github_repo }}.svg
        :target: https://github.com/{{ cookiecutter.github_repo }}/blob/master/LICENSE

{{ cookiecutter.description }}

TODO: Please provide feature overview of module

Further documentation is available on
https://{{ cookiecutter.project_shortname }}.readthedocs.io/
