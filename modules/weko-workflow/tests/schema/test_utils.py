from mock import patch

from weko_workflow.models import Action
from weko_workflow.schema.utils import get_schema_action, type_null_check
from weko_workflow.schema.marshmallow import ActionSchema, NextSchema, NextItemLinkSchema, NextIdentifierSchema, NextOAPolicySchema

# .tox/c1/bin/pytest --cov=weko_workflow tests/schema/test_utils.py::test_get_schema_action -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_get_schema_action():
    with patch('weko_workflow.schema.utils.Action.get_action_detail') as mock_get_action_detail:
        # Action is None
        mock_get_action_detail.return_value = None
        assert get_schema_action(1) is None

        # Endpoint is begin_action
        mock_get_action_detail.return_value = Action(action_endpoint='begin_action')
        assert isinstance(get_schema_action(1), ActionSchema)

        # Endpoint is end_action
        mock_get_action_detail.return_value = Action(action_endpoint='end_action')
        assert isinstance(get_schema_action(1), ActionSchema)

        # Endpoint is approval
        mock_get_action_detail.return_value = Action(action_endpoint='approval')
        assert isinstance(get_schema_action(1), NextSchema)

        # Endpoint is item_login
        mock_get_action_detail.return_value = Action(action_endpoint='item_login')
        assert isinstance(get_schema_action(1), NextSchema)

        # Endpoint is item_link
        mock_get_action_detail.return_value = Action(action_endpoint='item_link')
        assert isinstance(get_schema_action(1), NextItemLinkSchema)

        # Endpoint is identifier_grant
        mock_get_action_detail.return_value = Action(action_endpoint='identifier_grant')
        assert isinstance(get_schema_action(1), NextIdentifierSchema)

        # Endpoint is oa_policy
        mock_get_action_detail.return_value = Action(action_endpoint='oa_policy')
        assert isinstance(get_schema_action(1), NextOAPolicySchema)

        # Endpoint is other
        mock_get_action_detail.return_value = Action(action_endpoint='dummy')
        assert isinstance(get_schema_action(1), ActionSchema)

# .tox/c1/bin/pytest --cov=weko_workflow tests/schema/test_utils.py::test_type_null_check -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_type_null_check():
    # target is None
    assert not type_null_check(None, int)

    # target is not int
    assert not type_null_check('test', int)

    # target is int
    assert type_null_check(1, int)