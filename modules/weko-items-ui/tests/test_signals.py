import uuid
import pytest
from weko_items_ui.signals import receiver
from mock import MagicMock, patch

def test_receiver(app,db ,db_records):
    depid, recid, parent, doi, record, item = db_records[0]
    # db.execute("PRAGMA foreign_keys=OFF;")
    db.session.commit()
    with patch("weko_items_ui.signals.current_celery_app", return_value=MagicMock()):
        with patch("weko_items_ui.signals.CRISLinkageResult.set_running", return_value=MagicMock()):
            app.config.update(LINKAGE_MQ_EXCHANGE=MagicMock(),
                            LINKAGE_MQ_QUEUE=MagicMock())
            receiver(recid.object_uuid)
