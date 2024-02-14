import argparse
import oai_schema
import uuid
import orjson
import sys
from oai_schema import oai_schema_config

from invenio_db import db
from weko_schema_ui.models import OAIServerSchema


def main():
    try:
        type_list = ['overwrite_all', 'only_add_new', 'only_specified']
        # Read parameters.
        parser = argparse.ArgumentParser()
        parser.add_argument('reg_type', action='store')
        try:
            args = parser.parse_args()
        except BaseException:
            print('Please input parameter of register type.')
            print('List of valid parameters [{}].'.format(','.join(type_list)))
            sys.exit(0)
        if args.reg_type == 'overwrite_all':
            truncate_table()
            register_oai_schema_from_folder()
            db.session.commit()
        elif args.reg_type == 'only_add_new':
            elist = get_oai_schema_name()
            register_oai_schema_from_folder(exclusion_list=elist)
            db.session.commit()
        elif args.reg_type == 'only_specified':
            slist = oai_schema_config.SPECIFIED_LIST
            del_oai_schema(slist)
            elist = get_oai_schema_name()
            register_oai_schema_from_folder(exclusion_list=elist, specified_list=slist)
            db.session.commit()
        else: 
            print('Please input parameter of register type.')
            print('List of valid parameters [{}].'.format(','.join(type_list)))
            sys.exit(0) 
    except Exception as ex:
        print(ex)


def truncate_table():
    db.session.execute('TRUNCATE oaiserver_schema;')
    db.session.commit()


def get_oai_schema_name():
    oai_schema = db.session.query(OAIServerSchema.schema_name).all()
    return [x.schema_name for x in oai_schema]


def del_oai_schema(del_list):
    db.session.query(OAIServerSchema).filter(OAIServerSchema.schema_name.in_(del_list)).delete(synchronize_session='fetch')


def register_oai_schema_from_folder(exclusion_list=[], specified_list=[]):
    reg_list = []
    for i in dir(oai_schema):
        schema_obj = getattr(oai_schema, i)
        if getattr(schema_obj, 'schema_name', None) and schema_obj.schema_name:
            sname = schema_obj.schema_name
            if (sname not in exclusion_list) \
                    or (sname in specified_list):
                reg_list.append(dict(
                    id=str(uuid.uuid4()),
                    schema_name=schema_obj.schema_name,
                    form_data=schema_obj.form_data,
                    xsd=orjson.dumps(schema_obj.xsd).decode(),
                    namespaces=schema_obj.namespaces,
                    schema_location=schema_obj.schema_location,
                    isvalid=True,
                    version_id=1,
                    target_namespace=schema_obj.target_namespace
                ))
    if reg_list:
        db.session.execute(OAIServerSchema.__table__.insert(), reg_list)

    print('Processed id list: ', [x['schema_name'] for x in reg_list])


if __name__ == '__main__':
    main()