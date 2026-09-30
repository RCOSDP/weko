# -*- coding: utf-8 -*-
"""Ad-hoc reproduction: dump the real SWORD v3 deposit HTTP response.

論文(recid=1) と 根拠データ(recid=2) を ItemReference(isSupplementedBy) で
関連付け、実装関数 `_get_status_multi_document` が生成するレスポンスを
Direct / Workflow の両方でダンプする。

実行:
  docker compose -f docker-compose2.yml exec -T web bash -lc '\
    /home/invenio/.virtualenvs/invenio/bin/python -m pytest \
    /code/modules/weko-swordserver/tests/test_sword_response_dump.py \
    -s -q -p no:warnings'

不要になったらこのファイルは削除してよい（gitには含めない）。
"""
import json
from flask import jsonify

import weko_swordserver.views as V
from weko_swordserver.views import _get_status_multi_document, _get_status_document


def _dump(app, doc, status):
    resp = app.make_response((jsonify(doc), status))
    lines = ["HTTP/1.1 {}".format(resp.status)]
    for k, v in resp.headers.items():
        lines.append("{}: {}".format(k, v))
    lines.append("")
    lines.append(json.dumps(json.loads(resp.get_data(as_text=True)),
                            indent=2, ensure_ascii=False))
    return "\n".join(lines)


def test_dump_real(app, db, location, records, monkeypatch):
    from weko_records.models import ItemReference

    # paper(recid=1) --isSupplementedBy--> data(recid=2)   (RO-Crate の itemLink 相当)
    db.session.add(ItemReference(
        src_item_pid="1", dst_item_pid="2", reference_type="isSupplementedBy"))
    db.session.commit()

    real_url_for = V.url_for

    def fake_url_for(endpoint, **kw):
        if endpoint == "weko_workflow.display_activity":
            return "https://repository.example.org/workflow/activity/detail/{}".format(
                kw.get("activity_id"))
        return real_url_for(endpoint, **kw)
    monkeypatch.setattr(V, "url_for", fake_url_for)

    recids = ["1", "2"]
    with app.test_request_context(
            "/sword/service-document", base_url="https://repository.example.org"):
        direct = _get_status_multi_document(recids, None, "Direct")
        workflow = _get_status_multi_document(
            recids, ["A-20260717-00001", "A-20260717-00002"], "Workflow")

        print("\n\n########## DIRECT (workflow disabled) -> 201 ##########")
        print(_dump(app, direct, 201))
        print("\n\n########## WORKFLOW (workflow enabled) -> 202 ##########")
        print(_dump(app, workflow, 202))
