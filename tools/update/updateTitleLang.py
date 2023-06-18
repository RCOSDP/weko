# -*- coding: utf-8 -*-
# fix tool for issue 37855
# 使い方
# docker-compose exec web invenio shell /code/tools/update/fixTitleLang.py
# docker-compose exec web invenio index reindex -t recid --yes-i-know
# docker-compose exec web invenio index run -d -c 3 --skip-errors

from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from flask import current_app
from invenio_oaiserver import current_oaiserver
from invenio_oaiserver.models import OAISet
from invenio_communities.config import COMMUNITIES_OAI_FORMAT
from invenio_records.models import RecordMetadata
from elasticsearch.exceptions import TransportError
from weko_deposit.api import WekoDeposit

from datetime import datetime
import os
import sys
import math
import json
import logging
import traceback

# for logging
start_time = datetime.today()

# global connect
engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
connection = engine.connect()

def updateTitleinItemMeta():
    """Update title lang in item_metadata table.
    """    
    current_app.logger.info('UPDATE title in item_metadata')
    update_sql = "UPDATE public.item_metadata SET json = jsonb_set(json::jsonb, '{item_titles,0}', (json->'item_titles'->0) || jsonb_build_object('subitem_title_language', 'ja')) WHERE NOT(json->'item_titles'->0 ? 'subitem_title _language');"
    try:
        with connection.begin() as c:
            result = connection.execute(update_sql)
            if result:
                current_app.logger.info('Updated titles:{}'.format(result.rowcount))
            
    except SQLAlchemyError as ex:
        current_app.logger.info("{}".format(ex))
    current_app.logger.info('UPDATED title in item_metadata')

def updateTitleinRecordsMeta():
    current_app.logger.info('UPDATE title in records_metadata')
    update_sql = "UPDATE records_metadata SET json=jsonb_set(json::jsonb, '{item_titles,attribute_value_mlt,0}', (json->'item_titles'->'attribute_value_mlt'->0) || jsonb_build_object('subitem_title_language', 'ja')) WHERE NOT(json->'item_titles'->'attribute_value_mlt'->0 ? 'subitem_title_language');"
    try:
        with connection.begin() as c:
            result = connection.execute(update_sql)
            if result:
                current_app.logger.info('Updated titles:{}'.format(result.rowcount))     
    except SQLAlchemyError as ex:
        current_app.logger.info("{}".format(ex))
    current_app.logger.info('UPDATED title in records_metadata')


def updateCreatorinItemMeta():
    current_app.logger.info('UPDATE item_metadata')
    count_sql = "SELECT MAX(jsonb_array_length(json->'item_creator')) AS max from item_metadata WHERE json ? 'item_creator'"
    update_sql = "update item_metadata set json=jsonb_set(json::jsonb, '{item_creator,%s,creatorNames,0}', (json->'item_creator'->%s->'creatorNames'->0) || jsonb_build_object('subitem_title_language', 'ja')) WHERE json ? 'item_creator' AND NOT(json->'item_creator'->%s->'creatorNames'->0 ? 'creatorNameLang');"
    try:
        with connection.begin() as c:
            result = connection.execute(count_sql)
            for row in result:
               max_creators = row['max']
            for i in range(max_creators):
                val = [i,i,i]
                result2 = connection.execute(update_sql,val)
                current_app.logger.info('Updated creator{}:{}'.format(i,result2.rowcount))
    except SQLAlchemyError as ex:
        current_app.logger.info("{}".format(ex))
    current_app.logger.info('UPDATED item_metadata')

def updateCreatorinRecordsMeta():
    current_app.logger.info('UPDATE records_metadata')
    count_sql = "SELECT MAX(jsonb_array_length(json->'item_creator'->'attribute_value_mlt')) FROM records_metadata WHERE json ? 'item_creator';"
    update_sql = "UPDATE records_metadata SET json=jsonb_set(json::jsonb, '{item_creator,attribute_value_mlt,%s,creatorNames,0}', (json->'item_creator'->'attribute_value_mlt'->%s->'creatorNames'->0) || jsonb_build_object('creatorNameLang', 'ja')) WHERE json ? 'item_creator' AND NOT(json->'item_creator'->'attribute_value_mlt'->%s->'creatorNames'->0 ? 'creatorNameLang');"
    try:
        with connection.begin() as c:
            result = connection.execute(count_sql)
            for row in result:
               max_creators = row['max']
            for i in range(max_creators):
                val = [i,i,i]
                result2 = connection.execute(update_sql,val)
                current_app.logger.info('Updated creator{}:{}'.format(i,result2.rowcount))
    except SQLAlchemyError as ex:
        current_app.logger.info("{}".format(ex))
    current_app.logger.info('UPDATED records_metadata')


def main():
    """Application's main function."""
    # Start logging
    logging.basicConfig(
        level=logging.INFO,
        filename='logging-setjalang-' +
                 '{:-%Y%m%d-%s.}'.format(datetime.now()) +
                 str(os.getpid()) + ".log",
        filemode='w',
        format="%(asctime)-15s %(levelname)-5s %(message)s")
    logging.info('*' * 60)
    
    updateTitleinItemMeta()
    updateTitleinRecordsMeta()
    updateCreatorinItemMeta()
    updateCreatorinRecordsMeta()

    end_time = datetime.today()

    current_app.logger.info('Finished')
    current_app.logger.info('start time: {}'.format(start_time))
    current_app.logger.info('end time: {}'.format(end_time))
    connection.close()



if __name__ == '__main__':
    """Main context."""
    main()

