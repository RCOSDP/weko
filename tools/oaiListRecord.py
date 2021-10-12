import sys
import time

from flask import current_app
from sickle import Sickle


def countListRecords(baseURL='https://localhost/oai',
                     meta='oai_dc', setspec=''):
    startTime = time.time()
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

    elapsedTime = time.time() - startTime
    current_app.logger.info("# of items: {0}".format(len(ids)))
    current_app.logger.info("# of deleted items: {0}".format(len(deletedIds)))
    current_app.logger.info("elapsed time: {0}".format(elapsedTime))
