import os
from typing import Any
from typing import Dict

# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
# -- Path setup --------------------------------------------------------------
# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
# import os
# import sys
# sys.path.insert(0, os.path.abspath('.'))
"""Sphinx configuration."""
# -- Project information -----------------------------------------------------
project = "Invenio-SWORD"
copyright = "2019, CottageLabs <hello@cottagelabs.com>"
author = "CottageLabs <hello@cottagelabs.com>"

# Get the version string. Cannot be done with import!
g: Dict[str, Any] = {}
with open(os.path.join("..", "invenio_sword", "version.py"), "rt") as fp:
    exec(fp.read(), g)
    release = g["__version__"]


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.coverage",
    "sphinx.ext.doctest",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "alabaster"

html_theme_options = {
    "description": "Module for depositing record metadata and uploading files using the SWORD protocol.",
    "github_user": "swordapp",
    "github_repo": "invenio-sword",
    "github_button": False,
    "github_banner": True,
    "show_powered_by": False,
    "extra_nav_links": {
        "invenio-sword@GitHub": "https://github.com/swordapp/invenio-sword",
        # Not yet uploaded to PyPI
        # 'invenio-sword@PyPI': 'https://pypi.python.org/pypi/invenio-sword/',
        "SWORDv3 specification": "https://swordapp.github.io/swordv3/swordv3.html",
    },
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]


# -- Extension configuration -------------------------------------------------
