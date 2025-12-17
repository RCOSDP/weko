from ..api import Action

from .marshmallow import ActionSchema, NextSchema, NextItemLinkSchema, \
    NextIdentifierSchema, NextOAPolicySchema

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

    Returns:
        schema: アクションに対応するスキーマ
    """
    action = Action().get_action_detail(action_id)
    if not action:
        return None
    action_endpoint = action.action_endpoint
    
    if action_endpoint in ["begin_action", "end_action"]:
        return ActionSchema()
    elif action_endpoint in ["item_login", "approval"]:
        return NextSchema()
    elif action_endpoint == "item_link":
        return NextItemLinkSchema()
    elif action_endpoint == "identifier_grant":
        return NextIdentifierSchema()
    elif action_endpoint == "oa_policy":
        return NextOAPolicySchema()
    else:
        return ActionSchema()

def type_null_check(target, type):
    """型とnullチェック

    Args:
        target (object): 対象オブジェクト
        type (type): 型
        
    Returns: 
        bool: Noneでなく、targetの方がtypeである場合True,それ以外の場合False

    """
    
    if target == None or \
        not isinstance(target, type):
        return False
    return True 