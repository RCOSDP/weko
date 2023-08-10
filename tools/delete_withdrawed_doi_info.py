import traceback

from flask import current_app

from invenio_db import db
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_pidrelations.contrib.versioning import PIDVersioning
from invenio_pidrelations.models import PIDRelation
from invenio_pidrelations.serializers.utils import serialize_relations
from weko_deposit.api import WekoIndexer
from weko_workflow.models import Activity, ActionIdentifier
from weko_workflow.utils import IdentifierHandle

def get_deleted_doi():
    dois = PersistentIdentifier.query.filter_by(pid_type='doi',status='D').all()
    return dois

def get_record_list(dois):
    result = list()
    for doi in dois:
        targets = list()
        item_id = doi.object_uuid
        parent_item = PersistentIdentifier.query.filter_by(pid_type='recid',object_uuid=item_id).one()
        targets.append(parent_item)
        
        pv=PIDVersioning(child=parent_item)
        children = PIDVersioning(parent=pv.parent,child=parent_item).get_children(
            pid_status=PIDStatus.REGISTERED).filter(
                PIDRelation.relation_type==2).order_by(
                    PIDRelation.index.desc()).all()
                
        for child in children:
            is_target = False
            activities = Activity.query.filter_by(item_id=child.object_uuid,activity_status="F").all()
            for act in activities:
                idt_act = ActionIdentifier.query.filter_by(activity_id=act.activity_id).one_or_none()
                if idt_act:
                    if idt_act.action_identifier_select in [-2, -3]:
                        is_target = True
                        break
            if is_target:
                targets.append(child)
        result.append(targets)
    return result

def get_exist_idt_field(record_list):
    delete_target=list()
    for records in record_list:
        for record in records:
            ih = IdentifierHandle(record.object_uuid)
            key_value = ih.metadata_mapping.get_first_property_by_mapping(
                    "identifierRegistration.@value")
            key_id=key_value.split(".")[0] if key_value else ""
            if key_id in ih.item_metadata:
                delete_target.append(record)
    return delete_target

def delete_doi_info(delete_target):
    deleted_list = list()
    errors = list()
    for record in delete_target:
        try:
            ih = IdentifierHandle(record.object_uuid)
            ih.remove_idt_registration_metadata()
            relations = serialize_relations(record)
            if relations and 'version' in relations:
                relations_ver = relations['version'][0]
                relations_ver['id'] = record.object_uuid
                relations_ver['is_last'] = relations_ver.get('index') == 0
                WekoIndexer().update_relation_version_is_last(relations_ver)
            db.session.commit()
            deleted_list.append(record)
        except:
            current_app.logger.error(traceback.format_exc())
            db.session.rollback()
            errors.append(record)

    return deleted_list, errors

if __name__=="__main__":
    dois = get_deleted_doi()
    print("deleted dois:{}".format([doi.pid_value for doi in dois]))
    record_list = get_record_list(dois)
    print("target record list: {}".format([record.pid_value for records in record_list for record in records]))
    delete_target = get_exist_idt_field(record_list)
    print("delete target list: {}".format([record.pid_value for record in delete_target]))
    deleted_list, errors = delete_doi_info(delete_target)
    print("{} deleted success:{}".format(len(deleted_list), [item.pid_value for item in deleted_list]))
    print("{} delete failed: {}".format(len(errors), [item.pid_value for item in errors]))