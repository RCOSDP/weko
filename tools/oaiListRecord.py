import sys
import time

from flask import current_app
from sickle import Sickle


def countListRecords(baseURL='https://localhost/oai',
                     meta='oai_dc', setspec=''):
    startTime = time.process_time()
    sickle = Sickle(endpoint=baseURL,
                    max_retries=3, verify=False)
    ids = []
    deletedIds = []
    records = sickle.ListRecords(metadataPrefix=meta, set=setspec)
    for r in records:
        if r.header.deleted == False:
            ids.append(r.header.identifier)
        else:
            deletedIds.append(r.header.identifier)

    elapsedTime = time.process_time() - startTime
    current_app.logger.info("# of items: ".format(len(ids)))
    current_app.logger.info("# of deleted items: ".format(len(deletedIds)))
    current_app.logger.info("elapsed time: {0}".format(elapsedTime))
