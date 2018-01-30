{% include 'misc/header.py' %}
"""{{ cookiecutter.description }}"""

from .ext import {{ cookiecutter.extension_class }}
from .version import __version__

__all__ = ('__version__', '{{ cookiecutter.extension_class }}')
