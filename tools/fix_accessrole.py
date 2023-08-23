import csv
import sys
from flask import current_app
import traceback
from datetime import datetime
from sqlalchemy.orm.attributes import flag_modified

from invenio_db import db
from invenio_pidstore.models import PersistentIdentifier
from invenio_pidrelations.contrib.versioning import PIDVersioning
from invenio_pidrelations.models import PIDRelation
from invenio_records.models import RecordMetadata
from invenio_records_files.models import RecordsBuckets
from invenio_files_rest.models import FileInstance,ObjectVersion
from weko_deposit.api import WekoDeposit
from weko_records.models import ItemMetadata
from weko_records.utils import set_timestamp



def read_file(filename):
    files = dict()
    with open(filename,encoding='utf-8',newline="") as f:
        for cols in csv.reader(f, delimiter='\t'):
            if cols[0] not in files:
                files[cols[0]]=list()
            files[cols[0]].append(cols[1])
    return files

def get_records(data):
    records=dict()
    for recid in data:
        parent = PersistentIdentifier.query.filter_by(pid_type='recid',pid_value=recid).one_or_none()
        if parent:
            records[recid]=dict()
            pv=PIDVersioning(child=parent)
            children=PIDVersioning(parent=pv.parent,child=parent).get_children(
                PIDRelation.relation_type==2).order_by(
                    PIDRelation.index.desc()).all()
            for child in children:
                records[recid][child]=PIDVersioning(child=child).parent
    return records

def fix_metadata(records, fix_target):
    for recid in records:
        pid_parents = records.get(recid)
        targets = fix_target.get(recid)
        for pid, parent in pid_parents.items():
            try:
                record_metadata = RecordMetadata.query.filter_by(id=pid.object_uuid).one_or_none()
                item_metadata = ItemMetadata.query.filter_by(id=pid.object_uuid).one_or_none()
                file_items = get_file_item(record_metadata.json)
                flg = False
                fixed=list()
                errors=dict()
                
                # fix db data
                flg,fixed, errors=fix_record_metadata(file_items, record_metadata,targets,flg,fixed,errors)
                flg,fixed, errors=fix_item_metadata(file_items, item_metadata,targets,flg,fixed,errors)
                flg,fixed, errors=fix_file_contents(pid.object_uuid,targets,flg,fixed,errors)
                
                # fix es data
                if record_metadata and flg:
                    deposit=WekoDeposit(record_metadata.json,record_metadata)
                    args=[{"index":deposit.get("path",[]),"action":deposit.get("publish_status")},item_metadata.json]
                    deposit.update(*args)
                    if record_metadata and record_metadata.json and '_oai' in record_metadata.json:
                        deposit.jrc['_oai'] = record_metadata.json.get('_oai')
                    if 'path' in deposit.jrc and '_oai' in deposit.jrc \
                            and ('sets' not in deposit.jrc['_oai']
                                 or not deposit.jrc['_oai']['sets']):
                        setspec_list = deposit.jrc['path'] or []
                        if setspec_list:
                            deposit.jrc['_oai'].update(dict(sets=setspec_list))
                    set_timestamp(deposit.jrc, deposit.created, deposit.updated)
                    deposit.get_content_files()
                    deposit.indexer.get_es_index()
                    deposit.indexer.client.update(index=deposit.indexer.es_index,
                                                  doc_type=deposit.indexer.es_doc_type,
                                                  id=pid.object_uuid,
                                                  body={"doc":deposit.jrc})
                db.session.commit()
                
                print("* [{date}] {recid},uuid: {uuid} (parent: {parent})".format(
                    date=datetime.strftime(datetime.now(),"%Y-%m-%d %H:%M:%S:%f"),
                    recid=pid.pid_value,
                    uuid=pid.object_uuid,
                    parent=parent.pid_value
                ))
                print("** exist target:")
            
                finds = fixed+list(errors.keys())
                for filename in finds:
                    print("  - {filename}: {result}".format(filename=filename,result="fixed" if filename in fixed else "not fixed({})".format(errors[filename])))
                print("** can not find target:")
                for filename in [f for f in targets if f not in finds]:
                    print("  - {filename}".format(filename=filename))

            except:
                current_app.logger.error(traceback.format_exc())
                db.session.rollback()
            
                

def get_file_item(record):
    items = list()
    for key in record:
        metadata = record.get(key)
        if isinstance(metadata, dict) and \
            metadata.get("attribute_type","") == "file":
                items.append(key)
    return items

def fix_record_metadata(file_items, record, targets,flg,fixed,errors):
    data = record.json
    for item in file_items:
        metadata = data.get(item).get("attribute_value_mlt",[])
        for f in metadata:
            if f.get("filename") in targets:
                if f.get("accessrole") == "open_no":
                    flg |= True
                    if f.get("filename") not in fixed:
                        fixed.append(f.get("filename"))
                    f["accessrole"] = "open_login"
                else:
                    if f.get("filename") not in errors:
                        errors[f.get("filename")]="no 'open_no'"
    if flg:
        flag_modified(record,'json')
        db.session.merge(record)
    return flg,fixed, errors

def fix_item_metadata(file_items, record, targets,flg,fixed,errors):
    data = record.json
    for item in file_items:
        metadata = data.get(item)
        for f in metadata:
            if f.get("filename") in targets:
                if f.get("accessrole") == "open_no":
                    flg |= True
                    if f.get("filename") not in fixed:
                        fixed.append(f.get("filename"))
                    f["accessrole"] = "open_login"
                else:
                    if f.get("filename") not in errors:
                        errors[f.get("filename")]="no 'open_no'"
    if flg:
        flag_modified(record,'json')
        db.session.merge(record)
    return flg,fixed, errors

def fix_file_contents(rec_uuid, targets,flg,fixed,errors):
    files = FileInstance.query.filter(FileInstance.id.in_(
        ObjectVersion.query.with_entities(ObjectVersion.root_file_id).filter(ObjectVersion.bucket_id.in_(
            RecordsBuckets.query.with_entities(RecordsBuckets.bucket_id).filter(RecordsBuckets.record_id==rec_uuid)
        ))
    )).all()
    for f in files:
        f_data = f.json
        if f_data.get("filename") in targets:
            if f_data.get("accessrole") == "open_no":
                f_data["accessrole"] = "open_login"
                flg|=True
                if f_data.get("filename") not in fixed:
                    fixed.append(f_data.get("filename"))
            else:
                if f_data.get("filename") not in errors:
                    errors[f_data.get("filename")] = "no 'open_no'"
        if flg:
            flag_modified(f,'json')
            db.session.merge(f)
    return flg,fixed, errors

if __name__ == "__main__":
    args = sys.argv
    filename=args[1]
    data = read_file(filename)
    records=get_records(data)
    fix_metadata(records, data)
    