from marshmallow import Schema, fields 
from marshmallow.validate import Range

class ActivitySchema(Schema):
    workflow_id = fields.Integer(required=True)
    flow_id = fields.Integer(required=True)
    itemtype_id = fields.Integer(allow_none=True)
    extra_info = fields.Dict(allow_none=True)
    related_title = fields.String(allow_none=True)
    activity_confirm_term_of_use = fields.Boolean(allow_none=True)
    activity_login_user= fields.Integer(allow_none=True)
    activity_update_user= fields.Integer(allow_none=True)
    class Meta:
        strict = True

class ActionSchema(Schema):
    action_version = fields.String(allow_none=True)
    commond = fields.String(allow_none=True)
    class Meta:
        strict = True

class CancelSchema(ActionSchema):
    pid_value = fields.String(allow_none=True)

class NextSchema(ActionSchema):
    temporary_save = fields.Integer(allow_none=True)

class NextItemLinkSchema(NextSchema):
    link_data = fields.List(fields.Dict(),required=True)

class NextIdentifierSchema(NextSchema):
    identifier_grant = fields.String(required=True)
    identifier_grant_jalc_doi_suffix = fields.String(allow_none=True)
    identifier_grant_jalc_doi_link = fields.String(required=True)
    identifier_grant_jalc_cr_doi_suffix = fields.String(allow_none=True)
    identifier_grant_jalc_cr_doi_link = fields.String(required=True)
    identifier_grant_jalc_dc_doi_suffix = fields.String(allow_none=True)
    identifier_grant_jalc_dc_doi_link = fields.String(required=True)
    identifier_grant_ndl_jalc_doi_suffix = fields.String(allow_none=True)
    identifier_grant_ndl_jalc_doi_link = fields.String(required=True)
    
class ResponseMessageSchema(Schema):
    code = fields.Integer(required=True,validate=Range(min=-2,max=0))
    msg = fields.String(required=True)
    data = fields.Dict(allow_none=True)
    class Meta:
        strict = True