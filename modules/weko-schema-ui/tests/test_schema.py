from weko_schema_ui.schema import SchemaConverter
import pytest

# class SchemaConverter:

@pytest.fixture
def schemaConverter_ins(app):
    schema = "tests/data/oai_dc.xsd"
    rootname = "dc"
    with app.app_context():
        return SchemaConverter(schema,rootname) 


def test_SchemaConverter(schemaConverter_ins):
    assert isinstance(schemaConverter_ins,SchemaConverter)

#     def __init__(self, schemafile, rootname):
#     def to_dict(self):
#     def create_schema(self, schema_file):
#         def getXSVal(element_name):  # replace prefix namespace
#         def get_element_type(type):
#         def is_valid_element(element_name):
#         def get_elements(element):
#     def __init__(self, record=None, schema_name=None):
#     def get_ignore_item_from_option(self):
#     def get_mapping_data(self):
#         def get_mapping():
#     def __converter(self, node):
#         def list_reduce(olst):
#         def get_attr(x):
#         def create_json(name, node1, node2):
#         def _check_description_type(_attr, _alst):
#         def json_reduce(node):
#     def get_jpcoar_json(cls, records, schema_name="jpcoar_mapping"):
#     def __get_value_list(self, remove_empty=False):
#         def analysis(field):
#         def set_value(nd, nv):
#         def get_sub_item_value(atr_vm, key, p=None):
#         def get_value_from_content_by_mapping_key(atr_vm, list_key):
#         def get_url(z, key, val):
#         def get_key_value(nd, key=None):
#         def get_exp_value(atr_list):
#         def get_items_value_lst(atr_vm, key, rlst, z=None, kn=None):
#         def analyze_value_with_exp(nlst, exp):
#         def get_atr_value_lst(node, atr_vm, rlst):
#         def get_mapping_value(mpdic, atr_vm, k, atr_name):
#             def remove_empty_tag(mp):
#             def get_type_item(item_type_mapping, atr_name):
#             def get_item_by_type(temporary, type_item):
#             def handle_type_ddi(atr_name, list_type, vlst):
#             def clean_none_value(dct):
#         def remove_hide_data(obj, parentkey):
#         def replace_resource_type_for_jpcoar_v1(atr_vm_item):
#     def create_xml(self):
#         def check_node(node):
#         def get_prefix(str):
#         def get_atr_list(node):
#             def get_max_count(node):
#         def set_children(kname, node, tree, parent_keys,
#         def recorrect_node(val, attr, current_lang, mandatory=True,
#         def merge_json_xml(json, dct):
#         def remove_custom_scheme(name_identifier, v,
#         def count_aff_childs(key, creator_idx):
#         def create_affiliation(numbs_child, k, v, child,
#     def __remove_files_do_not_publish(self):
#         def __get_file_permissions(files_json):
#     def __build_jpcoar_relation(self, list_json_xml):
#         def __build_relation(data):
#     def support_for_output_xml(self, data):
#     def to_list(self):
#         def get_element(str):
#         def get_key_list(nodes):
#     def get_node(self, dc, key=None):
#     def find_nodes(self, mlst):
#         def del_type(nid):
#         def cut_pre(str):
#         def items_node(nid, nlst, index=0):
#         def get_node_dic(key):
#         def get_path_list(key):
# def cache_schema(schema_name, delete=False):
#     def get_schema():
# def delete_schema_cache(schema_name):
# def schema_list_render(pid=None, **kwargs):
# def delete_schema(pid):
# def get_oai_metadata_formats(app):