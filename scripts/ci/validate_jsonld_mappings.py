"""install.sh が投入した JSON-LD マッピングを、紐づくアイテムタイプに対して検証する。

マッピングとアイテムタイプはどちらも scripts/demo/item_type.sql から投入されるので、
ここでの不一致は item_type.sql 自体の不整合を意味する。

web コンテナ内で実行し、結果を Markdown で出力する:

    docker compose exec -T web python /code/scripts/ci/validate_jsonld_mappings.py

不一致が1件でもあれば終了コード 1 で終わる。
"""
import sys

from invenio_app.factory import create_app


def main():
    from weko_records.models import ItemTypeJsonldMapping
    from weko_search_ui.mapper import JsonLdMapper

    lines = ['# JSON-LD マッピングの検証', '',
             '| マッピング | アイテムタイプ | エラー数 |', '| --- | --- | ---: |']
    details = []
    with create_app().app_context():
        mappings = ItemTypeJsonldMapping.query.filter_by(is_deleted=False) \
            .order_by(ItemTypeJsonldMapping.id).all()
        for m in mappings:
            errors = JsonLdMapper(m.item_type_id, m.mapping).validate() or []
            lines.append(f'| {m.id} {m.name} | {m.item_type_id} | {len(errors)} |')
            if errors:
                details += [f'## {m.id} {m.name}', '']
                details += [f'- {e}' for e in errors]
                details.append('')
    print('\n'.join(lines + [''] + details))
    return 1 if details else 0


if __name__ == '__main__':
    sys.exit(main())
