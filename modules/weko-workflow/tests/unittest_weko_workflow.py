from flask import Flask

from weko_workflow import WekoWorkflow
from invenio_db import db
from datetime import datetime, timedelta
import threading
import unittest

class Test_get_new_activity_id(unittest.TestCase):
    def test_workflow_id_thread_check(self):
        """test thread safe id create check"""
        from weko_forkwflow.api import WorkActivity 

        t1 = threading.Thread(target=WorkActivity.get_new_activity_id, args=(datetime.utcnow())
        t2 = threading.Thread(target=WorkActivity.get_new_activity_id, args=(datetime.utcnow())
        t3 = threading.Thread(target=WorkActivity.get_new_activity_id, args=(datetime.utcnow())

        print "start thread test wrokflow_id"

        t1.start()
        t2.start()
        t3.start()

        print "end thread test wrokflow_id"

if __name__ == "__main__":
    unittest.main()