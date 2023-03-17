from marshmallow import Schema, fields
from marshmallow.validate import Range

class ImportItemsSchema(Schema):
    data_path = fields.String(required=False, allow_none=False)
    list_record = fields.List(fields.Dict(), allow_none=False)
    class Meta:
        strict = True

class DownloadImportSchema(Schema):
    list_result = fields.List(fields.Dict(), required=False, allow_none=False)
    class Meta:
        strict = True

class ResponseMessageSchema(Schema):
    code = fields.Integer(required=True,validate=Range(min=-1,max=0))
    msg = fields.String(required=True)
    data = fields.Dict(allow_none=True)
    class Meta:
        strict = True


class ResponseObjectSchema(Schema):
    status = fields.String(required=True)
    data = fields.Dict(required=True)
    class Meta:
        strict = True
