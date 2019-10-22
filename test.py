import json

def get_record(file):
    with open(file, encoding="utf8") as json_file:
        data = json.load(json_file)
        return data

record1 = get_record("C:\\Users\\huytaq.kg\\Desktop\\record_1.json")
record2 = get_record("C:\\Users\\huytaq.kg\\Desktop\\record_2.json")
json_keys = get_record("C:\\Users\\huytaq.kg\\Desktop\\json_keys.json")

dictRecord_2nd = dict()
dictRecord_3rd = dict()
list_dict_record_2nd = []
list_dict_record_3rd = []

def dict_record_recurssive(att, data, prepath, field):
    key, value = "", ""
    
    key_template = ".metadata.{}{}.{}"
    if (isinstance(data[att][field][0], dict)):
        print('-------- DICT -----------')
        print(att, data, prepath, field)
        for idx, items in enumerate(data[field]):
        #     for sub_item in items:
        #         key = key_template.format(prepath, "[" + str(idx) + "]", sub_item)
        #         # print('-------- SUB ITEM -----------')
        #         # print(sub_item, items[sub_item])
        #         if (isinstance(items[sub_item], list)):
        #             print('-------- SUB ITEM -----------')
        #             print(att, items[sub_item], key, str(sub_item))
        #             # prepath = prepath + '.' + sub_item
                    
        #             if len(items[sub_item][0]) == 0:
        #                 value = ''
        #             else:
        #                 dict_record_recurssive(att, items[sub_item], prepath, str(sub_item))
        #         else:
        #             value = items[sub_item]
        #         print(key, value)
    else:
        print('-------- NO DICT -----------')
        print(att, data, prepath, field)
    
        
        

def dict_record(record):
    for att in record:
        # key, value = "", ""
        if any(att in s for s in json_keys):      
            if ('attribute_value_mlt' in record[att]) == True:
                prepath = '.metadata.' + att
                dict_record_recurssive(att, record, prepath, 'attribute_value_mlt')
    # for att in record:
    #     key, value = "", ""
    #     if any(att in s for s in json_keys):        
    #         if isinstance(record[att], dict):
    #             if ('attribute_type' in record[att]) == True:
    #                 if (record[att]['attribute_type'] == 'creator'):
    #                     for idx, creator in enumerate(record[att]['attribute_value_mlt'][0]):
    #                         key_template = ".metadata.{}.{}{}.{}"
    #                         for sub_item in record[att]['attribute_value_mlt'][0][str(creator)][0]:
    #                             key = key_template.format(att, creator, "[" + str(idx) + "]", sub_item)
    #                             value = record[att]['attribute_value_mlt'][0][str(creator)][0][sub_item]
    #                             dictRecord_2nd[key] = creator
    #                             dictRecord_3rd[key] = value
                                
    #             else:
    #                 if ('attribute_value_mlt' in record[att]) == True:
    #                     attr_name = record[att]['attribute_name']
    #                     for idx, val in enumerate(record[att]['attribute_value_mlt']):
    #                         key_template = ".metadata.{}{}.{}"
    #                         for sub_item in val:
    #                             key = key_template.format(att, "[" + str(idx) + "]", sub_item)
    #                             value = val[sub_item]
    #                             dictRecord_2nd[key] = attr_name
    #                             dictRecord_3rd[key] = value
    #                 else:
    #                     dictRecord_2nd[att] = record[att]['attribute_name']
    #                     dictRecord_3rd[att] = record[att]['attribute_value']
    #         else:
    #             print("-----NON DICT")
    #             if att == 'path':
    #                 print(att, record[att])
    #                 dictRecord_2nd[att] = 'インデックス'
    #                 dictRecord_3rd[att] = record[att]

    #             dictRecord_2nd['#.id'] = '#ID'
    #             dictRecord_3rd['#.id'] = record['_deposit']['id']

    #             dictRecord_2nd['.uri'] = 'URI'
    #             dictRecord_3rd['.uri'] = "request_url" + 'records/' + record['_deposit']['id']

    # list_dict_record_2nd.append(dictRecord_2nd.copy())
    # list_dict_record_3rd.append(dictRecord_3rd.copy())
    
dict_record(record1)
# dict_record(record2)

# print(list_dict_record_2nd)
# print(list_dict_record_3rd)