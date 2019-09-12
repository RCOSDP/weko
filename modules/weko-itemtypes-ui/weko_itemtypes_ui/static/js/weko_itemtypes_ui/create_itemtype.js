// require(["jquery", "bootstrap"],function() {});
$(document).ready(function () {
  src_render = {};
  src_mapping = {};
  page_global = {
    upload_file: false,
    table_row: [],        // 追加した行番号を保存する元々順番()
    table_row_map: {},    // 生成したschemaとformの情報を保存する
    meta_list: {},        // 追加した行の情報を保存する(セットした詳細情報)
    meta_fix: {},
    schemaeditor: {       // objectの場合
      schema:{}           //   生成したschemaの情報を保存する
    },
    edit_notes: {}         // Map of notes for each attribute, keep seperate
  };
  properties_obj = {}     // 作成したメタデータ項目タイプ
  select_option = '';
  page_json_editor = {}   //   一時的editorオブジェクトの保存
  url_update_schema = '/admin/itemtypes/register';
  // デフォルトマッピングのテンプレート
  mapping_value = {
    "display_lang_type": "",
    "oai_dc_mapping": "",
    "jpcoar_mapping": "",
    "junii2_mapping": "",
    "lido_mapping": "",
    "lom_mapping": "",
    "spase_mapping": ""
  }
  meta_system_info = {
      updated_date : {
        title : "Updated Date",
        title_i18n: {ja: "更新日時", en: "Updated Date"},
        input_type: "cus_122",
        option: {
          required : false,
          multiple : false,
          hidden : true,
          showlist : false,
          crtf : false
        }
      },
      created_date : {
        title: "Created Date",
        title_i18n: {ja: "作成日時", en: "Created Date"},
        input_type: "cus_122",
        option: {
          required : false,
          multiple : false,
          hidden : true,
          showlist : false,
          crtf : false
        }
      },
      persistent_identifier_doi : {
        input_type: "cus_121",
        title: "Persistent Identifier(DOI)",
        title_i18n: {ja: "永続識別子（DOI）", en: "Persistent Identifier(DOI)"},
        option: {
          required : false,
          multiple : false,
          hidden : true,
          showlist : false,
          crtf : false
        }
      },
      persistent_identifier_h : {
        input_type: "cus_123",
        title: "Persistent Identifier(Handle)",
        title_i18n: {ja: "永続識別子（ハンドル）", en: "Persistent Identifier(Handle)"},
        option: {
          required : false,
          multiple : false,
          hidden : true,
          showlist : false,
          crtf : false
        }
      },
      ranking_page_url : {
        input_type: "cus_123",
        title: "Ranking Page URL",
        title_i18n: {ja: "ランディングページのURL", en: "Ranking Page URL"},
        option: {
          required : false,
          multiple : false,
          hidden : true,
          showlist : false,
          crtf : false
        }
      },
      belonging_index_info : {
        input_type: "cus_124",
        title: "Belonging Index Info",
        title_i18n: {ja: "所属インデックスの情報", en: "Belonging Index Info"},
        option: {
          required : false,
          multiple : false,
          hidden : true,
          showlist : false,
          crtf : false
        }
      },
    };
    meta_fix = {
      pubdate : {
        input_type: "Date",
        title: "Publish Date",
        title_i18n: {ja: "公開日", en: "Publish Date"},
        option: {
          required : true,
          multiple : false,
          hidden : false,
          showlist : false,
          crtf : false
        }
      },
    }
    property_default = {}

  $('#myModal').modal({
    show: false
  })

  if($('#item-type-lists').val().length > 0) {
    // バージョンアップ
    $('#upt_version').attr('checked', true);
    $('#new_version').attr('checked', false);
    itemname = $('#item-type-lists').find("option:selected").text();
    itemname = itemname.substr(0,itemname.lastIndexOf('('));
    $('#itemtype_name').val(itemname);
    url_update_schema = '/admin/itemtypes/'+$('#item-type-lists').val()+'/register';
  }

  $('.radio_versionup').on('click', function(){
    if($(this).val() == 'upt') {
      url_update_schema = '/admin/itemtypes/'+$('#item-type-lists').val()+'/register';
    } else {
      url_update_schema = '/admin/itemtypes/register';
    }
  });

  $('#item-type-lists').on('change', function(){
    window.location.href = '/admin/itemtypes/' + $('#item-type-lists').val();
  });

  $('input[type=radio][name=item_type]').on ('change', function(){
      if (this.value === 'normal') {
          $('option.normal_type').show()
          $('option.harvesting_type').hide()
          disabled_deleted_type();
      } else if (this.value === 'harvesting') {
          $('option.normal_type').hide()
          $('option.harvesting_type').show()
          disabled_deleted_type();
      } else {
          $('option.deleted_type').show();
          $('option.normal_type').hide();
          $('option.harvesting_type').hide();
          $('#btn_restore_itemtype_schema').prop('disabled', false);
          $('div.metadata-content *').not("[id=btn_restore_itemtype_schema]").prop('disabled', true);
      }
  });

  function disabled_deleted_type(){
      $('option.deleted_type').hide();
      $('#btn_restore_itemtype_schema').prop('disabled', true);
      $('div.metadata-content *').not("[id=btn_restore_itemtype_schema]").prop('disabled', false);
  }

  $('#btn_create_itemtype_schema').on('click', function(){
    if($('#itemtype_name').val() == "") {
      $('#itemtype_name_warning').removeClass('hide');
      $('#itemtype_name').focus();
      return;
    }
    $('#itemtype_name_warning').addClass('hide');
    create_itemtype_schema();
    send(url_update_schema, page_global);
  });

  $('#btn_previews_itemtype_schema').on('click', function(){
    create_itemtype_schema();
    $('#schema_json').text(JSON.stringify(page_global.table_row_map.schema, null, 4));
    $('#form_json').text(JSON.stringify(page_global.table_row_map.form, null, 4));
    $('#render_json').text(JSON.stringify(page_global, null, 4));
  });

  function create_itemtype_schema(){
    page_global.table_row_map['name'] = $('#itemtype_name').val();
    page_global.table_row_map['action'] = $('[name=radio_versionup]:checked').val();
    page_global.table_row_map['mapping'] = {
        updated_date : {
          "display_lang_type": "",
          "oai_dc_mapping": "",
          "jpcoar_mapping": {
            "date": {
              "@attributes": {"dateType": "subitem_system_date_type"},
              "@value": "subitem_system_date"
            },
          },
          "junii2_mapping": "",
          "lido_mapping": "",
          "lom_mapping": "",
          "spase_mapping": ""
        },
        created_date :{
          "display_lang_type": "",
          "oai_dc_mapping": "",
          "jpcoar_mapping": {
            "date": {
              "@attributes": {"dateType": "subitem_system_date_type"},
              "@value": "subitem_system_date",
            },
          },
          "junii2_mapping": "",
          "lido_mapping": "",
          "lom_mapping": "",
          "spase_mapping": ""
        },
        persistent_identifier_doi: {
          "display_lang_type": "",
          "oai_dc_mapping": "",
          "jpcoar_mapping": {
            "identifier": {
              "@attributes": {"identifierType": "subitem_system_identifier_doi_type"},
              "@value": "subitem_system_identifier_doi",
            },
            "identifierRegistration": {
              "@attributes": {"identifierType": "subitem_system_id_rg_doi_type"},
              "@value": "subitem_system_id_rg_doi",
            },
          },
          "junii2_mapping": "",
          "lido_mapping": "",
          "lom_mapping": "",
          "spase_mapping": ""
        },
        persistent_identifier_h: {
          "display_lang_type": "",
          "oai_dc_mapping": "",
          "jpcoar_mapping": {
            "identifier": {
              "@attributes": {"identifierType": "subitem_system_identifier_type"},
              "@value": "subitem_system_identifier",
            },
          },
          "junii2_mapping": "",
          "lido_mapping": "",
          "lom_mapping": "",
          "spase_mapping": ""
        },
        ranking_page_url: {
          "display_lang_type": "",
          "oai_dc_mapping": "",
          "jpcoar_mapping": {
            "identifier": {
              "@attributes": {"identifierType": "subitem_system_identifier_type"},
              "@value": "subitem_system_identifier",
            },
          },
          "junii2_mapping": "",
          "lido_mapping": "",
          "lom_mapping": "",
          "spase_mapping": ""
        },
        belonging_index_info: {
          "display_lang_type": "",
          "oai_dc_mapping": "",
          "jpcoar_mapping": "",
          "junii2_mapping": "",
          "lido_mapping": "",
          "lom_mapping": "",
          "spase_mapping": ""
        }
      };
    page_global.table_row_map['form'] = [];
    page_global.table_row_map['schema'] = {
      $schema: "http://json-schema.org/draft-04/schema#",
      type: "object",
      description: "",
      properties: {},
      required: []
    };

    // Keep the notes seperate from schema to avoid extracting later
    page_global.table_row_map['form'] = [];

    // コンテンツ本体
    if(page_global.upload_file) {
      page_global.table_row_map.schema.properties["filemeta"] = {
        type:"array",
        title: "Contents Body",
        items:{
          type: "object",
          properties: {
            filename: {
              type: "string",
              title: "Display Name"
            },
            displaytype: {
              type: "string",
              title: "Display Format",
              enum: ["detail","simple","preview"]
            },
            licensetype: {
              type: "string",
              title: "License",
              enum: ["license_free","license_0","license_1","license_2","license_3","license_4","license_5"]
            },
            licensefree: {
              type: "string"
            },
            accessrole: {
              type: "string",
              title: "Access",
              enum: ["open_access","open_date","open_login","open_no"]
            },
            accessdate: {
              type: "string",
              title: "Publish Date"
            },
            groups: {
              type: "string",
              title: "Group Name"
            }
          }
        }
      }
      page_global.table_row_map.form.push({
        key:"filemeta",
        title:"Contents Body",
        add: "New",
        style: {
          add: "btn-success"
        },
        items: [
          {
            key: "filemeta[].filename",
            type: "select",
            title: "Display Name",
            title_i18n:{ja:"表示名",en:"FileName"}
          },
          {
            key: "filemeta[].displaytype",
            type: "select",
            title: "Display Format",
            title_i18n:{ja:"表示形式",en:"Preview"},
            titleMap: [
              {value: "detail", name: "Detailed" },
              {value: "simple", name: "Simple" },
              {value: "preview", name: "Preview" }
            ]
          },
          {
            key: "filemeta[].licensetype",
            type: "select",
            title:" License",
            title_i18n:{ja:"ライセンス",en:"License"},
            titleMap: [
              {value: "license_free", name: "License Free" },
              {value: "license_0", name: "Creative Commons : Attribution" },
              {value: "license_1", name: "Creative Commons : Attribution-Share-Alike" },
              {value: "license_2", name: "Creative Commons : Attribution-No-Derivatives" },
              {value: "license_3", name: "Creative Commons : Attribution-Non-Commercial" },
              {value: "license_4", name: "Creative Commons : Attribution-NonCommercial-ShareAlike" },
              {value: "license_5", name: "Creative Commons : Attribution-NonCommercial-ShareAlike-NoDerivatives" }
            ]
          },
          {
            key: "filemeta[].licensefree",
            type: "textarea",
            notitle: true,
            condition: "model.filemeta[arrayIndex].licensetype == 'license_free'"
          },
          {
            title: "Check Plagiarism",
            title_i18n:{ja:"剽窃チェック",en:"Check Plagiarism"},
            type: "template",
            template: "<div class='text-center'><a class='btn btn-primary' href='/ezas/pdf-detect-weko.html' target='_blank' role='button'>{{ form.title }}</a></div>"
          },
          {
            key: "filemeta[].accessrole",
            type: "radios",
            title: "Access",
            title_i18n:{ja:"アクセス",en:"Access"},
            titleMap: [
              {value: "open_access", name: "Open Access" },
              {value: "open_date", name: "Specify Open Access Date" },
              {value: "open_login", name: "Only Logged In Users" },
              {value: "open_no", name: "Do Not Make Public" }
            ]
          },
          {
            key: "filemeta[].accessdate",
            title: "Publish Date",
            title_i18n:{ja:"公開日",en:"Opendate"},
            type: "template",
            format: "yyyy-MM-dd",
            templateUrl: "/static/templates/weko_deposit/datepicker.html",
            condition: "model.filemeta[arrayIndex].accessrole == 'open_date'"
          },
          {
            key: "filemeta[].groups",
            title: "Group",
            title_i18n:{ja:"グループ",en:"Group"},
            type: "text",
            condition: "model.filemeta[arrayIndex].accessrole == 'open_date' || model.filemeta[arrayIndex].accessrole == 'open_login'"
          }
        ]
      });
      if(src_mapping.hasOwnProperty('filemeta')) {
        page_global.table_row_map.mapping['filemeta'] = src_mapping['filemeta'];
      } else {
        page_global.table_row_map.mapping['filemeta'] = mapping_value;
      }
    }

    page_global.table_row_map.schema.properties["pubdate"] = {type:"string",title:"公開日",format:"datetime"}
    page_global.table_row_map.form.push({key:"pubdate",type:"template",title:"公開日",title_i18n:{ja:"公開日",en:"PubDate"},required: true,format: "yyyy-MM-dd",templateUrl: "/static/templates/weko_deposit/datepicker.html"});
    page_global.table_row_map.schema.required.push("pubdate");

    if(src_mapping.hasOwnProperty('pubdate')) {
      page_global.table_row_map.mapping['pubdate'] = src_mapping['pubdate'];
    } else {
      page_global.table_row_map.mapping['pubdate'] = mapping_value;
    }

//    System mapping

    if(src_mapping.hasOwnProperty('updated_date')) {
      page_global.table_row_map.mapping['updated_date'] = src_mapping['updated_date'];
    }

    if(src_mapping.hasOwnProperty('created_date')) {
      page_global.table_row_map.mapping['created_date'] = src_mapping['created_date'];
    }

    if(src_mapping.hasOwnProperty('persistent_identifier_doi')) {
      page_global.table_row_map.mapping['persistent_identifier_doi'] = src_mapping['persistent_identifier_doi'];
    }

    if(src_mapping.hasOwnProperty('persistent_identifier_h')) {
      page_global.table_row_map.mapping['persistent_identifier_h'] = src_mapping['persistent_identifier_h'];
    }

    if(src_mapping.hasOwnProperty('ranking_page_url')) {
      page_global.table_row_map.mapping['ranking_page_url'] = src_mapping['ranking_page_url'];
    }

    if(src_mapping.hasOwnProperty('belonging_index_info')) {
      page_global.table_row_map.mapping['belonging_index_info'] = src_mapping['belonging_index_info'];
    }

//    End system mapping
    // テーブルの行をトラバースし、マップに追加する
    err_input_id = []

    $.each(page_global.table_row, function(idx, row_id){
      var tmp = {}
      tmp.title = $('#txt_title_'+row_id).val();
      //add by ryuu. start
      tmp.title_i18n ={}
      tmp.title_i18n.ja = $('#txt_title_ja_'+row_id).val();
      tmp.title_i18n.en = $('#txt_title_en_'+row_id).val();
      //add by ryuu. end
      tmp.input_type = $('#select_input_type_'+row_id).val();
      tmp.input_value = "";
      tmp.input_minItems = $('#minItems_'+row_id).val();
      tmp.input_maxItems = $('#maxItems_'+row_id).val();
      tmp.option = {}
      tmp.option.required = $('#chk_'+row_id+'_0').is(':checked')?true:false;
      tmp.option.multiple = $('#chk_'+row_id+'_1').is(':checked')?true:false;
      tmp.option.hidden = $('#chk_'+row_id+'_4').is(':checked')?true:false;
      tmp.option.showlist = tmp.option.hidden?false:($('#chk_'+row_id+'_2').is(':checked')?true:false);
      tmp.option.crtf = tmp.option.hidden?false:($('#chk_'+row_id+'_3').is(':checked')?true:false);

      // Retrieve notes edited
      page_global.edit_notes[row_id] = $('#edit_notes_' + row_id).val();

      if(src_render.hasOwnProperty('meta_list')
          && src_render['meta_list'].hasOwnProperty(row_id)) {
        if(tmp.input_type == src_render['meta_list'][row_id]['input_type']) {
          if(src_mapping.hasOwnProperty(row_id)) {
            page_global.table_row_map.mapping[row_id] = src_mapping[row_id];
          } else {
            page_global.table_row_map.mapping[row_id] = mapping_value;
          }
        } else {
          page_global.table_row_map.mapping[row_id] = mapping_value;
        }
      } else {
        page_global.table_row_map.mapping[row_id] = mapping_value;
      }

      if(tmp.option.required) {
        page_global.table_row_map.schema.required.push(row_id);
      }
      if(tmp.input_type == 'text' || tmp.input_type == 'textarea') {
        if(tmp.option.multiple) {
          page_global.table_row_map.schema.properties[row_id] = {
            type: "array",
            title: tmp.title,
            minItems: tmp.input_minItems,
            maxItems: tmp.input_maxItems,
            items: {
              type: "object",
              properties: {
                interim: {type: "string"}    // [interim]は本当の意味を持たない
              }
            }
          }
          page_global.table_row_map.form.push({
            key: row_id,
            add: "New",
            title_i18n: tmp.title_i18n,
            style: {add:"btn-success"},
            items: [{
              key: row_id+'[].interim',
              type: tmp.input_type,
              notitle: true
            }]
          });
        } else {
          page_global.table_row_map.schema.properties[row_id] = {
            type: "string",
            title: tmp.title,
            format: tmp.input_type    // text|textarea
          }
          page_global.table_row_map.form.push({
            key: row_id,
            title: tmp.title,
            title_i18n: tmp.title_i18n,
            type: tmp.input_type    // text|textarea
          });
        }
      } else if(tmp.input_type == 'datetime') {
        if(tmp.option.multiple) {
          page_global.table_row_map.schema.properties[row_id] = {
            type: "array",
            title: tmp.title,
            minItems: tmp.input_minItems,
            maxItems: tmp.input_maxItems,
            items: {
              type: "object",
              properties: {
                interim: {type: "string"}    // [interim]は本当の意味を持たない
              }
            }
          }
          page_global.table_row_map.form.push({
            key: row_id,
            title_i18n: tmp.title_i18n,
            add: "New",
            style: {add:"btn-success"},
            items: [{
              key: row_id+'[].interim',
              type: "template",
              format: "yyyy-MM-dd",
              templateUrl: "/static/templates/weko_deposit/datepicker.html",
              notitle: true
            }]
          });
        } else {
          page_global.table_row_map.schema.properties[row_id] = {
            type: "string",
            title: tmp.title,
            format: "template"
          }
          page_global.table_row_map.form.push({
            key: row_id,
            title_i18n: tmp.title_i18n,
            type: "template",
            title: tmp.title,
            format: "yyyy-MM-dd",
            templateUrl: "/static/templates/weko_deposit/datepicker.html"
          });
        }
      } else if(tmp.input_type == 'checkboxes') {
        tmp.input_value = $("#schema_"+row_id).find(".select-value-setting").val();
        enum_tmp = []
        titleMap_tmp = []
        $.each(tmp.input_value.split('|'), function(i,v){
          enum_tmp.push(v);
          titleMap_tmp.push({value:v, name:v});
        })

        if(tmp.option.multiple) {
          // 選択式(プルダウン)(複数可)
          page_global.table_row_map.schema.properties[row_id] = {
            type: "array",
            title: tmp.title,
            minItems: tmp.input_minItems,
            maxItems: tmp.input_maxItems,
            items: {
              type: "object",
              properties: {
                "interim": {
                  type: "array",
                  items: {
                    type: "string",
                    enum: enum_tmp
                  }
                }
              }
            }
          }
          page_global.table_row_map.form.push({
            key: row_id,
            title_i18n: tmp.title_i18n,
            add: "New",
            style: {add:"btn-success"},
            items: [{
              key: row_id+'[].interim',
              type: tmp.input_type,         // checkboxes
              notitle: true,
              titleMap: titleMap_tmp
            }]
          });
        } else {
          // 選択式(プルダウン)
          page_global.table_row_map.schema.properties[row_id] = {
            type: "array",
            title: tmp.title,
            items: {
              type: "string",
              enum: enum_tmp
            }
          }
          page_global.table_row_map.form.push({
            key: row_id,
            title_i18n: tmp.title_i18n,
            type: tmp.input_type,         // checkboxes
            titleMap: titleMap_tmp
          });
        }
      } else if(tmp.input_type == 'radios' || tmp.input_type == 'select') {
        tmp.input_value = $("#schema_"+row_id).find(".select-value-setting").val();
        enum_tmp = []
        titleMap_tmp = []
        $.each(tmp.input_value.split('|'), function(i,v){
          enum_tmp.push(v);
          titleMap_tmp.push({value:v, name:v});
        })

        if(tmp.option.multiple) {
          page_global.table_row_map.schema.properties[row_id] = {
            type: "array",
            title: tmp.title,
            minItems: tmp.input_minItems,
            maxItems: tmp.input_maxItems,
            items: {
              type: "object",
              properties: {
                interim: {                  // [interim]は本当の意味を持たない
                  type: "string",
                  enum: enum_tmp
                }
              }
            }
          }
          page_global.table_row_map.form.push({
            key: row_id,
            title_i18n: tmp.title_i18n,
            add: "New",
            style: {add:"btn-success"},
            items: [{
              key: row_id+'[].interim',
              type: tmp.input_type,    // radios|select
              notitle: true,
              titleMap: titleMap_tmp
            }]
          });
        } else {
          page_global.table_row_map.schema.properties[row_id] = {
            type: "string",
            title: tmp.title,
            enum: enum_tmp
          }
          page_global.table_row_map.form.push({
            key: row_id,
            title_i18n: tmp.title_i18n,
            type: tmp.input_type,    // radios|select
            titleMap: titleMap_tmp
          });
        }
      } else if(tmp.input_type.indexOf('cus_') != -1) {
        editor = page_json_editor['schema_'+row_id];
        page_global.schemaeditor.schema[row_id] = editor.getValue();
        if(tmp.option.multiple) {
          page_global.table_row_map.schema.properties[row_id] = {
            type: "array",
            title: tmp.title,
            minItems: tmp.input_minItems,
            maxItems: tmp.input_maxItems,
            items: {
              type: "object",
              properties: page_global.schemaeditor.schema[row_id].properties,
              required: page_global.schemaeditor.schema[row_id].required
            }
          }
          //add by ryuu. start
          properties_obj[tmp.input_type.substr(4)].forms.title = tmp.title;
          properties_obj[tmp.input_type.substr(4)].forms.title_i18n = tmp.title_i18n;
          //add by ryuu. end
          if(Array.isArray(properties_obj[tmp.input_type.substr(4)].forms)) {
            properties_obj[tmp.input_type.substr(4)].forms.forEach(function(element){
              page_global.table_row_map.form.push(
                JSON.parse(JSON.stringify(element).replace(/parentkey/gi, row_id))
              );
            });
          } else {
            page_global.table_row_map.form.push(
              JSON.parse(JSON.stringify(properties_obj[tmp.input_type.substr(4)].forms).replace(/parentkey/gi, row_id))
            );
          }
        } else {
          page_global.table_row_map.schema.properties[row_id] = {
            type: "object",
            title: tmp.title,
            properties: page_global.schemaeditor.schema[row_id].properties,
            required: page_global.schemaeditor.schema[row_id].required
          }
          //add by ryuu. start
          properties_obj[tmp.input_type.substr(4)].form.title = tmp.title;
          properties_obj[tmp.input_type.substr(4)].form.title_i18n = tmp.title_i18n;
          //add by ryuu. end
          page_global.table_row_map.form.push(
            JSON.parse(JSON.stringify(properties_obj[tmp.input_type.substr(4)].form).replace(/parentkey/gi, row_id)));
        }
      }

      page_global.meta_list[row_id] = tmp;
    });
    //公開日
    var tmp_pubdate = {}
    tmp_pubdate.title = "公開日";
    tmp_pubdate.title_i18n = {}
    tmp_pubdate.title_i18n.ja = "公開日";
    tmp_pubdate.title_i18n.en = "PubDate";
    tmp_pubdate.input_type = "datetime";
    tmp_pubdate.input_value = "";
    tmp_pubdate.option = {}
    tmp_pubdate.option.required = $('#chk_pubdate_0').is(':checked') ? true : false;
    tmp_pubdate.option.multiple = $('#chk_pubdate_1').is(':checked') ? true : false;
    tmp_pubdate.option.hidden = $('#chk_pubdate_4').is(':checked') ? true : false;
    tmp_pubdate.option.showlist = tmp_pubdate.option.hidden ? false : ($('#chk_pubdate_2').is(':checked') ? true : false);
    tmp_pubdate.option.crtf = tmp_pubdate.option.hidden ? false : ($('#chk_pubdate_3').is(':checked') ? true : false);
    page_global.meta_fix["pubdate"] = tmp_pubdate;
	  page_global.meta_system = add_meta_system()
	  page_global.table_row_map.form = page_global.table_row_map.form.concat(get_form_system())
	  add_system_schema_property()
  }

  // add new meta table row
  $('#btn_new_itemtype_meta').on('click', function(){
    new_meta_row('item_'+$.now());
  });
  function new_meta_row(row_id) {
    var row_template = '<tr id="tr_' + row_id + '">'
        + '<td><input type="text" class="form-control" id="txt_title_' + row_id + '" value="">'
        + '  <div class="hide" id="text_title_JaEn_' + row_id + '">'
        +'     <p>' + "Japanese" + '：</p>'
        +'     <input type="text" class="form-control" id="txt_title_ja_' + row_id + '" value="">'
        +'     <p>' + "English" + '：</p>'
        +'     <input type="text" class="form-control" id="txt_title_en_' + row_id + '" value="">'
        + '  </div>'
        +'   <button type="button" class="btn btn-link" id="btn_link_' + row_id + '">' + "Localization Settings" + '</button>'
        +'</td>'
        + '<td><div class="form-inline"><div class="form-group">'
        + '  <label class="sr-only" for="select_input_type_'+row_id+'">select_input_type</label>'
        + '  <select class="form-control change_input_type" id="select_input_type_' + row_id + '" metaid="' + row_id + '">'
        + select_option
        + '  </select>'
        + '  </div></div>'
        + '  <div class="hide" id="arr_size_' + row_id + '">'
        + '    <div class="panel panel-default"><div class="panel-body">'
        + '    <form class="form-inline">'
        + '      <div class="form-group">'
        + '        <label for="minItems_'+row_id+'">minItems</label>'
        + '        <input type="number" class="form-control" id="minItems_'+row_id+'" placeholder="" value="1">'
        + '      </div>'
        + '      <div class="form-group">'
        + '        <label for="maxItems_'+row_id+'">maxItems</label>'
        + '        <input type="number" class="form-control" id="maxItems_'+row_id+'" placeholder="" value="9999">'
        + '      </div>'
        + '    </form>'
        + '    </div></div>'
        + '  </div>'
        + '  <div id="schema_' + row_id + '"></div>'
        + '</td>'
        + '<td>'
        + '  <div class="checkbox" id="chk_prev_' + row_id + '_0">'
        + '   <label><input type="checkbox" id="chk_' + row_id + '_0" value="required">' + "Required" + '</label>'
        + '  </div>'
        + '  <div class="checkbox" id="chk_prev_' + row_id + '_1">'
        + '    <label><input type="checkbox" id="chk_' + row_id + '_1" value="multiple">' + "Allow Multiple" + '</label>'
        + '  </div>'
        + '  <div class="checkbox" id="chk_prev_' + row_id + '_2">'
        + '    <label><input type="checkbox" id="chk_' + row_id + '_2" value="showlist">' +  "Show List" + '</label>'
        + '  </div>'
        + '  <div class="checkbox" id="chk_prev_' + row_id + '_3">'
        + '    <label><input type="checkbox" id="chk_' + row_id + '_3" value="crtf">' + "Specify Newline" + '</label>'
        + '  </div>'
        + '  <div class="checkbox" id="chk_prev_' + row_id + '_4">'
        + '    <label><input type="checkbox" id="chk_' + row_id + '_4" value="hidden">' + "Hide" + '</label>'
        + '  </div>'
        + '</td>'
        + '<td>'
        + '  <textarea type="button" class="form-control" rows="5" id="edit_notes_' + row_id + '">' + "" + '</textarea>'
        + '</td>'
        + '<td>'
        + '  <div class="btn-group-vertical" role="group" aria-label="' + "Replace" + '">'
        + '    <button type="button" class="btn btn-default sortable_up" id="btn_up_' + row_id + '" metaid="' + row_id + '">↑</button>'
        + '    <button type="button" class="btn btn-default sortable_down" id="btn_down_' + row_id + '" metaid="' + row_id + '">↓</button>'
        + '  </div>'
        + '</td>'
        + '<td>'
          + '  <button type="button" class="btn btn-danger" id="btn_del_' + row_id + '"><span class="glyphicon glyphicon-remove"></span></button>'
        + '</td>'
        + '</tr>';
    $('#tbody_itemtype').append(row_template);
    page_global.table_row.push(row_id);
    initSortedBtn();

     //add by ryuu. start
     //多言語linkをクリック
     $('#tbody_itemtype').on('click', 'tr td #btn_link_'+row_id, function(){
      if($('#text_title_JaEn_' + row_id).hasClass('hide')) {
        $('#text_title_JaEn_' + row_id).removeClass('hide');
      } else {
        $('#text_title_JaEn_' + row_id).addClass('hide');
      }
    });
    //add by ryuu. end

    // Dynamic additional click event
    // メタ項目の削除関数をダイナミックに登録する
    $('#tbody_itemtype').on('click', 'tr td #btn_del_'+row_id, function(){
      page_global.table_row.splice($.inArray(row_id,page_global.table_row),1);
      $('#tr_' + row_id).remove();
      initSortedBtn();
    });
    // チェックボックス「複数可」が選択状態になると、サイズのセットボックスを表示する
    $('#tbody_itemtype').on('click', 'tr td #chk_'+row_id+'_1', function(){
      if($('#chk_'+row_id+'_1').is(':checked')) {
        $('#arr_size_' + row_id).removeClass('hide');
      } else {
        $('#arr_size_' + row_id).addClass('hide');
      }
    });
    // チェックボックス「非表示」が選択状態になると、
    $('#tbody_itemtype').on('click', 'tr td #chk_'+row_id+'_4', function(){
      if($('#chk_'+row_id+'_4').is(':checked')) {
        $('#chk_prev_' + row_id + '_2').addClass('disabled');
        $('#chk_' + row_id + '_2').attr('disabled', true);
        $('#chk_prev_' + row_id + '_3').addClass('disabled');
        $('#chk_' + row_id + '_3').attr('disabled', true);
      } else {
        $('#chk_prev_' + row_id + '_2').removeClass('disabled');
        $('#chk_' + row_id + '_2').attr('disabled', false);
        $('#chk_prev_' + row_id + '_3').removeClass('disabled');
        $('#chk_' + row_id + '_3').attr('disabled', false);
      }
    });
  }

  $('#tbody_itemtype').on('click', '.sortable_up', function(){
    var cur_row_id = $(this).attr('metaid');
    var up_row_idx = $.inArray(cur_row_id,page_global.table_row);
    if(up_row_idx === 0) {
      // first row
      return;
    }
    up_row_idx = up_row_idx-1;
    var up_row_id = page_global.table_row[up_row_idx];
    $('#tr_'+cur_row_id).after($('#tr_'+up_row_id));
    page_global.table_row.splice(up_row_idx,1);
    var cur_row_idx = $.inArray(cur_row_id,page_global.table_row);
    if(cur_row_idx == page_global.table_row.length-1) {
      page_global.table_row.push(up_row_id);
    } else {
      page_global.table_row.splice(cur_row_idx+1,0,up_row_id);
    }
    initSortedBtn();
  })

  $('#tbody_itemtype').on('click', '.sortable_down', function(){
    var cur_row_id = $(this).attr('metaid');
    var down_row_idx = $.inArray(cur_row_id,page_global.table_row);
    if(down_row_idx === page_global.table_row.length-1) {
      // last row
      return;
    }
    down_row_idx = down_row_idx+1;
    var down_row_id = page_global.table_row[down_row_idx];
    $('#tr_'+cur_row_id).before($('#tr_'+down_row_id));
    page_global.table_row.splice(down_row_idx,1);
    var cur_row_idx = $.inArray(cur_row_id,page_global.table_row);
    page_global.table_row.splice(cur_row_idx,0,down_row_id);
    initSortedBtn();
  })

  function initSortedBtn() {
    $('.sortable_up').removeClass('disabled');
    $('.sortable_down').removeClass('disabled');
    $('#btn_up_'+page_global.table_row[0]).addClass('disabled');
    $('#btn_down_'+page_global.table_row[page_global.table_row.length-1]).addClass('disabled');
  }

  $('#chk_upload_file').on('change', function(){
    if($('#chk_upload_file').is(':checked')) {
      // page_global.upload_file = true;
      page_global.upload_file = false;
    } else {
      page_global.upload_file = false;
    }
  });

  // itemtype select input change
  $('#tbody_itemtype').on('change', '.change_input_type', function(){
    var meta_id = $(this).attr('metaid');
    if($(this).val().indexOf('cus_') != -1) {
      product = properties_obj[$(this).val().substr(4)].schema;
      $('#chk_prev_' + meta_id + '_1').removeClass('disabled');
      $('#chk_' + meta_id + '_1').attr('disabled', false);
      render_object('schema_'+meta_id, product);
    } else if('checkboxes' == $(this).val() || 'radios' == $(this).val()
            || 'select' == $(this).val()){
      $('#chk_prev_' + meta_id + '_1').addClass('disabled');
      $('#chk_' + meta_id + '_1').attr('disabled', true);
      $('#chk_' + meta_id + '_1').attr('checked', false);
      render_select('schema_'+meta_id, '');
    } else {
      $('#chk_prev_' + meta_id + '_1').removeClass('disabled');
      $('#chk_' + meta_id + '_1').attr('disabled', false);
      render_empty('schema_'+meta_id);
    }
  });

  function render_empty(elementId) {
    $('#'+elementId).empty();
  }

  function render_text(elementId, initval) {
    $('#'+elementId).html('<input type="text" '
      + 'class="form-control select-value-setting" '
      + 'value="' + initval + '">');
  }

  function render_select(elementId, initval) {
    $('#'+elementId).html('<div class="panel panel-default"><div class="panel-body">'
      + '<input type="text" class="form-control select-value-setting" '
      + 'value="' + initval + '" placeholder="' + 'Separate options with the | character' + '"></div></div>');
  }

  function render_object(elementId, initschema) {
    element = document.getElementById(elementId);
    var editor = new JSONSchemaEditor(element, {
      startval: initschema,
      editor: false
    });
    page_json_editor[elementId] = editor;
  }

  function send(url, data){
    $.ajax({
      method: 'POST',
      url: url,
      async: true,
      contentType: 'application/json',
      dataType: 'json',
      data: JSON.stringify(data),
      success: function(data,textStatus) {
        if('redirect_url' in data){
          window.location.href = data.redirect_url
        }
        else {
          $('.modal-body').text(data.msg);
          $('#myModal').modal('show');
        }
      },
      error: function(textStatus,errorThrown){
        $('.modal-body').text('Error: ' + JSON.stringify(textStatus));
        $('#myModal').modal('show');
      }
    });
  }

  getPropUrl = '/admin/itemtypes/properties/list?lang=' + $('#lang-code').val();
  select_option = '';
  // 作成したメタデータ項目タイプの取得
  $.ajax({
    method: 'GET',
    url: getPropUrl,
    async: false,
    success: function(data, status){
      properties_obj = data;

      defProps = data.defaults;
      Object.keys(defProps).forEach(function(row_id){
         property_default[defProps[row_id].value] = defProps[row_id].name
      })
      isSelected = true;
      Object.keys(defProps).forEach(function(key) {
        if (isSelected) {
          select_option = select_option + '<option value="' + defProps[key].value + '" selected>' + defProps[key].name + '</option>';
          isSelected = false;
        } else {
          select_option = select_option + '<option value="' + defProps[key].value + '">' + defProps[key].name + '</option>';
        }
      });

      odered = {}
      others = ''
      for (var key in data) {
        if (key == 'defaults') continue;

        option = '<option value="cus_' + key + '">' + data[key].name + '</option>'
        if (data[key].sort != null) {
          odered[data[key].sort] = option;
        } else {
          others = others + option;
        }
      }

      Object.keys(odered).forEach(function(key) {
        select_option = select_option + odered[key];
      });
      select_option = select_option + others;

    },
    error: function(status, error){
      console.log(error);
    }
  });

  if($('#item-type-lists').val().length > 0) {
    $.get('/admin/itemtypes/' + $('#item-type-lists').val() + '/render', function(data, status){
      Object.assign(src_render ,data);
      page_global.upload_file = false;    // data.upload_file;
      $('#chk_upload_file').attr('checked', data.upload_file);
      $.each(data.table_row, function(idx, row_id){
        new_meta_row(row_id);
        $('#txt_title_'+row_id).val(data.meta_list[row_id].title);
        //add by ryuu. start
        $('#txt_title_ja_'+row_id).val(data.meta_list[row_id].title_i18n.ja);
        $('#txt_title_en_'+row_id).val(data.meta_list[row_id].title_i18n.en);
        //add by ryuu. end
        $('#select_input_type_'+row_id).val(data.meta_list[row_id].input_type);
        $('#minItems_'+row_id).val(data.meta_list[row_id].input_minItems);
        $('#maxItems_'+row_id).val(data.meta_list[row_id].input_maxItems);
        $('#chk_'+row_id+'_0').attr('checked', data.meta_list[row_id].option.required);
        $('#chk_'+row_id+'_1').attr('checked', data.meta_list[row_id].option.multiple);
        $('#chk_'+row_id+'_2').attr('checked', data.meta_list[row_id].option.showlist);
        $('#chk_'+row_id+'_3').attr('checked', data.meta_list[row_id].option.crtf);
        $('#chk_'+row_id+'_4').attr('checked', data.meta_list[row_id].option.hidden);

        // Add the notes for the row here
        if(row_id in data.edit_notes) {
          $('#edit_notes_' + row_id).val(data.edit_notes[row_id]);
        }

        if(data.meta_list[row_id].option.hidden) {
          $('#chk_prev_' + row_id + '_2').addClass('disabled');
          $('#chk_' + row_id + '_2').attr('disabled', true);
          $('#chk_prev_' + row_id + '_3').addClass('disabled');
          $('#chk_' + row_id + '_3').attr('disabled', true);
        }

        if(data.meta_list[row_id].option.multiple) {
          $('#arr_size_' + row_id).removeClass('hide');
        }

        if(data.meta_list[row_id].input_type.indexOf('cus_') != -1) {
          render_object('schema_'+row_id, properties_obj[data.meta_list[row_id].input_type.substr(4)].schema);
        } else if('checkboxes' == data.meta_list[row_id].input_type || 'radios' == data.meta_list[row_id].input_type
                || 'select' == data.meta_list[row_id].input_type){
          $('#chk_prev_' + row_id + '_1').addClass('disabled');
          $('#chk_' + row_id + '_1').attr('disabled', true);
          render_select('schema_'+row_id, data.meta_list[row_id].input_value);
        } else {
          render_empty('schema_'+row_id);
        }
      });
      if($('input[type=radio][name=item_type]:checked').val() === 'deleted') {
        $('div.metadata-content *').not('[id=btn_restore_itemtype_schema]').prop('disabled', true);
      }
    });
    $.get('/api/itemtypes/' + $('#item-type-lists').val() + '/mapping', function(data, status){
      Object.assign(src_mapping, data);
    });
  }
  $('input[type=radio][name=item_type][value=normal]').click()
  if ($("#item-type-lists option:selected").hasClass('normal_type')) {
      $('input[type=radio][name=item_type][value=normal]').click()
  } else if ($("#item-type-lists option:selected").hasClass('harvesting_type')) {
      $('input[type=radio][name=item_type][value=harvesting]').click()
  } else if ($("#item-type-lists option:selected").hasClass('deleted_type')) {
      $('input[type=radio][name=item_type][value=deleted]').click()
  }

  $('#btn_delete_item').on('click', function(){
    var selected_item_type = $("#item-type-lists :selected");
    var is_harvesting_type = selected_item_type.hasClass("harvesting_type");
    var is_belonging_item = selected_item_type.hasClass("belonging_item");
    if (is_harvesting_type) {
      alert($("#msg_for_harvesting").val());
    } else if (is_belonging_item) {
      alert($("#msg_for_belonging_item").val());
    } else {
      $("#item_type_delete_confirmation").modal("show");
    }
  });

  $('#item_type_delete_continue').on('click', function(){
    $("#item_type_delete_confirmation").modal("hide");
    send_uri('/admin/itemtypes/delete/' + $('#item-type-lists').val(), {},
      function(data){
        window.location.href = "/admin/itemtypes";  // Error/Success flash set from server side
      },
      function(errmsg){
        window.location.href = "/admin/itemtypes";
        //alert(JSON.stringify(errmsg));
    });
  });

  $('#btn_restore_itemtype_schema').on('click', function(){
    var restore_itemtype = $("#item-type-lists :selected");
    if (restore_itemtype.val() !== '' && restore_itemtype.hasClass("deleted_type")) {
      send_uri('/admin/itemtypes/restore/' + restore_itemtype.val(), {},
        function(data){
          restore_itemtype.removeAttr("selected");
          restore_itemtype.hide();
          restore_itemtype.removeClass("deleted_type");
          restore_itemtype.addClass("normal_type");
          $('#itemtype_name').val('');
          alert(data.msg);
        },
        function(errmsg){
          alert(data.msg);
      });
    }
  });

  function send_uri(url, data, handleSuccess, handleError){
    $.ajax({
      method: 'POST',
      url: url,
      async: true,
      contentType: 'application/json',
      dataType: 'json',
      data: JSON.stringify(data),
      success: function(data,textStatus){
        handleSuccess(data);
      },
      error: function(textStatus,errorThrown){
        handleError(textStatus);
      }
    });
  }

  function add_meta_system(){
    var result = {}
    Object.keys(meta_system_info).forEach(function(key){
      result[key] = {
        title : meta_system_info[key].title,
        title_i18n : meta_system_info[key].title_i18n,
        input_type : meta_system_info[key].input_type,
        input_value : "",
        option : meta_system_info[key].option
      }
    })
    return result
  }

  function new_meta_row_default(row_id) {
    var row_template = '<tr id="tr_' + row_id + '">'
        + '<td><label type="text"  id="txt_title_' + row_id + '" value="" disabled="true"></label>'
        + '  <div class="hide" id="text_title_JaEn_' + row_id + '">'
        +'     <p>' + "Japanese" + '：</p>'
        +'     <label type="text" class="text"  id="txt_title_ja_' + row_id + '" value="" disabled="true"></label>'
        +'     <p>' + "English" + '：</p>'
        +'     <label type="text" class="text" id="txt_title_en_' + row_id + '" value="" disabled="true"></label>'
        + '  </div>'
        +'   <button type="button" class="btn btn-link" id="btn_link_' + row_id + '">' + "Localization Settings" + '</button>'
        +'</td>'
        + '<td><div class="form-inline"><div class="form-group">'
        + '  <label id="select_input_type_' + row_id + '" metaid="' + row_id + '" disabled="true" style="font-weight: 400">'
        + '  </label>'
        + '  </div></div>'
        + '  <div id="schema_' + row_id + '"></div>'
        + '</td>'
        + '<td>'
        + '  <div class="checkbox" id="chk_prev_' + row_id + '_0">'
        + '   <label><input type="checkbox" id="chk_' + row_id + '_0" value="required">' + "Required" + '</label>'
        + '  </div>'
        + '  <div class="checkbox" id="chk_prev_' + row_id + '_1">'
        + '    <label><input type="checkbox" id="chk_' + row_id + '_1" value="multiple">' + "Allow Multiple" + '</label>'
        + '  </div>'
        + '  <div class="checkbox" id="chk_prev_' + row_id + '_2">'
        + '    <label><input type="checkbox" id="chk_' + row_id + '_2" value="showlist">' +  "Show List" + '</label>'
        + '  </div>'
        + '  <div class="checkbox" id="chk_prev_' + row_id + '_3">'
        + '    <label><input type="checkbox" id="chk_' + row_id + '_3" value="crtf">' + "Specify Newline" + '</label>'
        + '  </div>'
        + '  <div class="checkbox" id="chk_prev_' + row_id + '_4">'
        + '    <label><input type="checkbox" id="chk_' + row_id + '_4" value="hidden">' + "Hide" + '</label>'
        + '  </div>'
        + '</td>'
        + '<td>'
        + '</td>'
        + '<td>'
        + '</td>'
        + '<td>'
        + '</td>'
        + '</tr>';
    $('#tbody_itemtype').append(row_template);
//    initSortedBtn();

     //add by ryuu. start
     //多言語linkをクリック
     $('#tbody_itemtype').on('click', 'tr td #btn_link_'+row_id, function(){
      if($('#text_title_JaEn_' + row_id).hasClass('hide')) {
        $('#text_title_JaEn_' + row_id).removeClass('hide');
      } else {
        $('#text_title_JaEn_' + row_id).addClass('hide');
      }
    });
    //add by ryuu. end

    // Dynamic additional click event
    // メタ項目の削除関数をダイナミックに登録する
    // チェックボックス「複数可」が選択状態になると、サイズのセットボックスを表示する
    $('#tbody_itemtype').on('click', 'tr td #chk_'+row_id+'_1', function(){
      if($('#chk_'+row_id+'_1').is(':checked')) {
        $('#arr_size_' + row_id).removeClass('hide');
      } else {
        $('#arr_size_' + row_id).addClass('hide');
      }
    });
    // チェックボックス「非表示」が選択状態になると、
  }

  function create_system_data(){
    let result = {}
    let system_row = Object.keys(meta_system_info);
    result.system_row = system_row
    let form = get_form_system()
    result.form = form
    return result
  }

  function get_form_system(){
    let result = new Array()
    let list_key = Object.keys(meta_system_info)
    for(i = 0; i< list_key.length; ++i){
      let row_id = list_key[i]
      let item = new Object()
      if(meta_system_info[row_id].input_type.indexOf('cus_') != -1) {
        item = {...properties_obj[meta_system_info[row_id].input_type.substr(4)].form};
        item.title = meta_system_info[row_id].title
        item.title_i18n = meta_system_info[row_id].title_i18n
        item.key = row_id
      } else {
        item.type = meta_system_info[row_id].input_type
        item.title = meta_system_info[row_id].title
        item.title_i18n = meta_system_info[row_id].title_i18n
        item.key = row_id
      }
      result.push(item)
      item = {}

    }
    return result
  }

  function add_system_schema_property() {
    let list_key = Object.keys(meta_system_info)
    for(i = 0; i< list_key.length; ++i){
      let row_id = list_key[i]
      let item = new Object()
      if(meta_system_info[row_id].input_type.indexOf('cus_') != -1) {
        item = {...properties_obj[meta_system_info[row_id].input_type.substr(4)].schema};
        item.title = meta_system_info[row_id].title
      } else {
        item.type = ''
        item.title = meta_system_info[row_id].title
        item.format = ''
      }
      page_global.table_row_map.schema.properties[row_id] = {...item}
      item = {}
    }
  }

});
