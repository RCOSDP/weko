
# .tox/c1/bin/pytest --cov=invenio_communities tests/test_forms.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
from flask_wtf import Form
import pytest
from io import BytesIO
from wtforms import FileField, HiddenField, StringField, TextAreaField
from wtforms.validators import ValidationError
from invenio_communities.forms import (
    _validate_input_id,
    CommunityForm
)
# def _validate_input_id(form, field):
# .tox/c1/bin/pytest --cov=invenio_communities tests/test_forms.py::test_validate_input_id -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
def test_validate_input_id(app):
    class TestForm(Form):
        test_field = StringField()
    # first character is not alphabet,"-","_"
    data = {"test_field":"11111111"}
    with app.test_request_context(method="POST",data=data):
        form = TestForm()
        field = form._fields["test_field"]
        with pytest.raises(ValidationError) as e:
            _validate_input_id(form,field)
        assert str(e.value) == 'The first character cannot be a number or special character. It should be an alphabet character, "-" or "_"'
    
    # first character is alphabet,"-","_"  negative number
    data = {"test_field":"-1"}
    with app.test_request_context(method="POST",data=data):
        form = TestForm()
        field = form._fields["test_field"]
        with pytest.raises(ValidationError) as e:
            _validate_input_id(form,field)
        assert str(e.value) == 'Cannot set negative number to ID.'

    # special character
    data = {"test_field":"a-1^^"}
    with app.test_request_context(method="POST",data=data):
        form = TestForm()
        field = form._fields["test_field"]
        with pytest.raises(ValidationError) as e:
            _validate_input_id(form,field)
        assert str(e.value) == "Don't use space or special character except `-` and `_`."
        
    # correct_data
    data = {"test_field":"a-123456789"}
    with app.test_request_context(method="POST",data=data):
        form = TestForm()
        field = form._fields["test_field"]
        _validate_input_id(form,field)


# class CommunityForm(Form):
#          {'classes': 'in'}),
#     def data(self):
#     def get_field_icon(self, name):
#     def get_field_by_name(self, name):
#     def get_field_placeholder(self, name):
#     def get_field_state_mapping(self, field):
#     def has_field_state_mapping(self, field):
#     def has_autocomplete(self, field):
#     def validate_identifier(self, field):
# .tox/c1/bin/pytest --cov=invenio_communities tests/test_forms.py::test_CommunityForm -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
def test_CommunityForm(app,db,communities):

    data = {
        "identifier":"comm1",
        "title":"Title1",
        "description":"Description1",
        "curation_policy":"",
        "page":"",
        "logo":(BytesIO(), "test.png"),
    }
    with app.test_request_context(method="POST",data=data):
        form = CommunityForm()
        res = form.validate_on_submit()
        assert len(form.identifier.errors) > 0
        assert form.identifier.errors[0] == "The identifier already exists. Please choose a different one."
    
    data = {
        "identifier":"comm0",
        "title":"Title0",
        "description":"Description0",
        "curation_policy":"test_curation_policy",
        "page":"test_page",
        "logo":(BytesIO(), "test.png"),
    }
    with app.test_request_context(method="POST",data=data):
        form = CommunityForm()
        form.validate_on_submit()
        form_data = form.data
        assert form_data["identifier"] == "comm0"
        assert form_data["title"] == "Title0"
        assert form_data["description"] == "Description0"
        assert form_data["curation_policy"] == "test_curation_policy"
        assert form_data["page"] == "test_page"
        assert form_data["index_checked_nodeId"] == ""
        assert form_data["logo"].filename == "test.png"
        assert form_data["logo"].mimetype == "image/png"
        
        # test for get_field_icon
        form_icon = form.get_field_icon("title")
        assert form_icon == "file-alt"
        
        # test for get_field_by_name
        form_name = form.get_field_by_name("title")
        assert form_name.id == "title"
        assert form_name.data == "Title0"
        
        # test for get_field_by_name, raise KeyError
        form_name = form.get_field_by_name("not_exist_name")
        assert form_name==None
        
        # test for get_field_placeholder
        form_placeholder = form.get_field_placeholder("test_name")
        assert form_placeholder == ""
        
        # test for get_field_state_mapping
        form.field_state_mapping={"title":"success"}
        form_state = form.get_field_state_mapping(form._fields["title"])
        assert form_state == "success"
        
        # test for get_field_state_mapping, raise KeyError
        form_state = form.get_field_state_mapping(form._fields["identifier"])
        assert form_state == None

        # test for has_field_state_mapping
        has_state = form.has_field_state_mapping(form._fields["title"])
        assert has_state == True
        
        # test for has_autocomplete
        has_autocomplete = form.has_autocomplete(form._fields["title"])
        assert has_autocomplete == False
        
# class EditCommunityForm(CommunityForm):
# class DeleteCommunityForm(Form):
#     delete = HiddenField(default='yes', validators=[validators.DataRequired()])
# class SearchForm(Form):
