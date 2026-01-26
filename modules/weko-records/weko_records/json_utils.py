# -*- coding: utf-8 -*-
#
# This file is part of WEKO3.
# Copyright (C) 2017 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# WEKO3 is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with WEKO3; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.

"""JSON処理のための互換性レイヤー.

段階的にorjsonへ移行するためのラッパー関数を提供します。
標準ライブラリのjsonモジュールと互換性のあるインターフェースを提供しつつ、
内部的にはorjsonを使用して高速化を実現します。
"""

import orjson
from typing import Any, Callable, Optional, Union


def dumps(
    obj: Any,
    indent: Optional[int] = None,
    ensure_ascii: bool = False,
    sort_keys: bool = False,
    default: Optional[Callable] = None,
) -> str:
    """オブジェクトをJSON文字列にシリアライズします.

    標準ライブラリのjson.dumps()と互換性のあるインターフェースを提供します。
    内部的にはorjson.dumps()を使用して高速化を実現します。

    Args:
        obj: シリアライズするオブジェクト
        indent: インデントレベル（2スペースまたは4スペース）
        ensure_ascii: ASCII文字のみ使用するか（orjsonはデフォルトでUTF-8）
        sort_keys: キーをソートするか
        default: カスタムエンコーダー関数

    Returns:
        JSON文字列

    Example:
        >>> data = {"name": "テスト", "value": 123}
        >>> dumps(data)
        '{"name":"テスト","value":123}'
    """
    option = 0

    if indent:
        # orjsonはOPT_INDENT_2のみサポート
        option |= orjson.OPT_INDENT_2

    if sort_keys:
        option |= orjson.OPT_SORT_KEYS

    # ensure_asciiのデフォルトはFalse（UTF-8を使用）
    # Trueの場合は、orjsonではサポートされていないため標準jsonにフォールバック
    if ensure_ascii:
        import json

        return json.dumps(
            obj, indent=indent, ensure_ascii=True, sort_keys=sort_keys, default=default
        )

    try:
        return orjson.dumps(obj, option=option, default=default).decode("utf-8")
    except TypeError:
        # orjsonでエラーが発生した場合は標準jsonにフォールバック
        import json

        return json.dumps(
            obj, indent=indent, ensure_ascii=ensure_ascii, sort_keys=sort_keys, default=default
        )


def loads(s: Union[str, bytes]) -> Any:
    """JSON文字列をオブジェクトにデシリアライズします.

    標準ライブラリのjson.loads()と互換性のあるインターフェースを提供します。
    内部的にはorjson.loads()を使用して高速化を実現します。

    Args:
        s: JSON文字列またはバイト列

    Returns:
        デシリアライズされたオブジェクト

    Example:
        >>> loads('{"name":"テスト","value":123}')
        {'name': 'テスト', 'value': 123}
    """
    if isinstance(s, str):
        s = s.encode("utf-8")
    return orjson.loads(s)


def dump(obj: Any, fp, **kwargs):
    """オブジェクトをJSONとしてファイルに書き込みます.

    標準ライブラリのjson.dump()と互換性のあるインターフェースを提供します。

    Args:
        obj: シリアライズするオブジェクト
        fp: ファイルオブジェクト
        **kwargs: dumps()に渡される追加の引数

    Example:
        >>> with open('data.json', 'w') as f:
        ...     dump({"key": "value"}, f)
    """
    fp.write(dumps(obj, **kwargs))


def load(fp):
    """ファイルからJSONを読み込んでオブジェクトにデシリアライズします.

    標準ライブラリのjson.load()と互換性のあるインターフェースを提供します。

    Args:
        fp: ファイルオブジェクト

    Returns:
        デシリアライズされたオブジェクト

    Example:
        >>> with open('data.json', 'r') as f:
        ...     data = load(f)
    """
    return loads(fp.read())


def dumps_bytes(
    obj: Any,
    indent: Optional[int] = None,
    sort_keys: bool = False,
    default: Optional[Callable] = None,
) -> bytes:
    """オブジェクトをJSONバイト列にシリアライズします.

    orjsonのネイティブな戻り値型（bytes）を直接返します。
    バイト列が必要な場合に文字列への変換オーバーヘッドを避けることができます。

    Args:
        obj: シリアライズするオブジェクト
        indent: インデントレベル
        sort_keys: キーをソートするか
        default: カスタムエンコーダー関数

    Returns:
        JSONバイト列

    Example:
        >>> data = {"name": "テスト", "value": 123}
        >>> dumps_bytes(data)
        b'{"name":"\\xe3\\x83\\x86\\xe3\\x82\\xb9\\xe3\\x83\\x88","value":123}'
    """
    option = 0

    if indent:
        option |= orjson.OPT_INDENT_2

    if sort_keys:
        option |= orjson.OPT_SORT_KEYS

    return orjson.dumps(obj, option=option, default=default)
