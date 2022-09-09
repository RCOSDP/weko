from ..api import Action

from .marshmallow import ActionSchema, NextSchema, NextItemLinkSchema, NextIdentifierSchema
def get_schema_action(action_id):
    """アクションIDから対応するスキーマを返す
    
    アクションのエンドポイントと対応するスキーマは以下の通り
    * begin_action, end_action, approval
        ActionSchema
    * item_login
        NextSchema
    * item_link
        NextItemLinkSchema
    * identifier_grant
        NextIdentifierSchema
    * その他
        ActionSchema

    Args:
        action_id (int): アクションID

    Raises:
        Exception: アクションが取得できない場合に発生

    Returns:
        schema: アクションに対応するスキーマ
    """
    action = Action().get_action_detail(action_id)
    if not action:
        raise Exception("can not get action")
    action_endpoint = action.action_endpoint
    
    if action_endpoint in ["begin_action", "end_action", "approval"]:
        return ActionSchema()
    elif action_endpoint == "item_login":
        return NextSchema()
    elif action_endpoint == "item_link":
        return NextItemLinkSchema()
    elif action_endpoint == "identifier_grant":
        return NextIdentifierSchema()
    else:
        return ActionSchema()

def type_null_check(target, type):
    """型とnullチェック

    Args:
        target (object): 対象オブジェクト
        type (type): 型

    Raises:
        ValueError: targetがNoneである、もしくは型がtype出ない場合発生する
    """
    
    if not isinstance(target, type) or \
        target == None:
        raise ValueError("{target} is None or not {type}.".format(target=target, type=type)) 