{% include 'misc/header.py' %}
"""Minimal Flask application example.

SPHINX-START

First install {{ cookiecutter.project_name | lower }}, setup the application and load
fixture data by running:

.. code-block:: console

   $ pip install -e .[all]
   $ cd examples
   $ ./app-setup.sh
   $ ./app-fixtures.sh

Next, start the development server:

.. code-block:: console

   $ export FLASK_APP=app.py FLASK_DEBUG=1
   $ flask run

and open the example application in your browser:

.. code-block:: console

    $ open http://127.0.0.1:5000/

To reset the example application run:

.. code-block:: console

    $ ./app-teardown.sh

SPHINX-END
"""

from flask import Flask
from flask_babelex import Babel

from {{ cookiecutter.package_name }} import {{ cookiecutter.extension_class }}

# Create Flask application
app = Flask(__name__)
Babel(app)
{{ cookiecutter.extension_class }}(app)
