def type_null_check(target, type):
    """型とnullチェック
    Args:
        target (object): 対象オブジェクト
        type (type): 型
    Raises:
        ValueError: targetがNoneである、もしくは型がtypeでない場合発生する
    """

    if not isinstance(target, type) or \
        target == None:
        raise ValueError("{target} is None or not {type}.".format(target=target, type=type))
