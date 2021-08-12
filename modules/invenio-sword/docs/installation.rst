Installation
============

With InvenioRDM
---------------

The simplest way to get set up with invenio-sword is through InvenioRDM. If you don't already have an InvenioRDM
instance, follow `the InvenioRDM installation instructions <https://inveniordm.docs.cern.ch/install/>`_

First, add "invenio-sword" to your ``Pipfile`` with:

.. code:: shell

   $ pipenv install invenio-sword

Then you can run your InvenioRDM instance as normal with `invenio-cli containerize`.


Outside InvenioRDM
------------------

If you are using invenio-app, then invenio-sword will be discovered automatically through its entrypoints. Otherwise,
add ``InvenioSword`` to your API application:

.. code:: python

   from invenio_sword import InvenioSword

   api_app = Flask("api-app")
   # …
   InvenioSword(api_app)

Because invenio-sword extends invenio-deposit, you will also need to ensure that the invenio-deposit search mappings
are installed, either by adding an entrypoint to your project, or registering them at application creation time:

.. code:: python

   # Entrypoint, in setup.py
   setup(
       # …
       entry_points={
           "invenio_search.mappings": [
               # …
               "deposits = invenio_deposit.mappings",
           ],
       },
       # …
   )

   # At application creation time
   from invenio_search import InvenioSearch

   app = Flask("app")
   # …
   search = InvenioSearch(app)
   search.register_mappings("deposits", "invenio_deposit.mappings")

Once all that's done, you should have a default SWORD service document endpoint at
http://localhost:5000/api/sword/service-document.