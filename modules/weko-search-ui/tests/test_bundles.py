import pytest
import os

from flask_assets import Bundle
# from weko_search_ui.bundles import catalog
from pkg_resources import resource_filename

# def test_catalog():
#     domain = "messages"
#     assert catalog(domain)==os.path.join(
#         resource_filename("weko_search_ui", "translations"),
#         "*",  # language code
#         "LC_MESSAGES",
#         "{0}.po".format(domain),
#     )

