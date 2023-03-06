
import pkg_resources
from mock import patch

from weko_admin.permissions import admin_permission_factory
# .tox/c1/bin/pytest --cov=weko_admin tests/test_permissions.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp


# def admin_permission_factory(action):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_permissions.py::test_admin_permission_factory -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_admin_permission_factory(app, users):
    action = "update-style-action"
    result = admin_permission_factory(action)
    permission_values = [permission.value for permission in list(result.needs)]
    assert action in permission_values
    
    with patch("weko_admin.permissions.pkg_resources.get_distribution", side_effect=pkg_resources.DistributionNotFound):
        result = admin_permission_factory(action)
        permission_values = [permission.value for permission in list(result.needs)]
        assert action in permission_values
