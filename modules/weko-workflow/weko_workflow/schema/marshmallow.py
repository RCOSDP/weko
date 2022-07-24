from marshmallow import Schema, fields 
from marshmallow.validate import Range

class InitActivitySchema(Schema):
    workflow_id = fields.Integer(required=True)
    flow_id = fields.Integer(required=True)
    itemtype_id = fields.Integer(required=True)
    class Meta:
        strict = True

class ResponseMessageSchema(Schema):
    code = fields.Integer(required=True,validate=Range(min=-1,max=0))
    msg = fields.String(required=True)
    data = fields.Dict(allow_none=True)
    class Meta:
        strict = True