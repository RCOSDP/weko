Developing invenio-sword
========================

Pre-commit checks
-----------------

invenio-sword uses `pre-commit <https://pre-commit.com/>`_ for automated checking and reformatting on every commit. This
includes:

* using `black <https://black.readthedocs.io/en/stable/>`_ for consistent code style
* using `mypy <http://mypy-lang.org/>`_ for static type checking

These checks are also run in CI.

You should ensure you have pre-commit installed, by e.g.

.. code:: shell

   pip install --user pre-commit

Once you have cloned the invenio-sword repository, you should install the pre-commit hook:

.. code:: shell

   git clone https://github.com/swordapp/invenio-sword.git
   cd invenio-sword
   pre-commit install
