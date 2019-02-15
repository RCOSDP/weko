  require([
    "jquery",
    "bootstrap"
  ],function() {
    src_render = {};
    src_mapping = {};
    page_global = {
      upload_file: false,
      table_row: [],        // 追加した行番号を保存する元々順番()
      table_row_map: {},    // 生成したschemaとformの情報を保存する
      meta_list: {},        // 追加した行の情報を保存する(セットした詳細情報)
      /////add by ryuu.0313 start
      meta_fix: {},
      /////add by ryuu.0313 end
      schemaeditor: {       // objectの場合
        schema:{}           //   生成したschemaの情報を保存する
      }
    };
    properties_obj = {}     // 作成したメタデータ項目タイプ
    select_option = '';
    page_json_editor = {}   //   一時的editorオブジェクトの保存
    url_update_schema = '/itemtypes/register';
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
      url_update_schema = '/itemtypes/'+$('#item-type-lists').val()+'/register';
    }

    $('.radio_versionup').on('click', function(){
      if($(this).val() == 'upt') {
        url_update_schema = '/itemtypes/'+$('#item-type-lists').val()+'/register';
      } else {
        url_update_schema = '/itemtypes/register';
      }
    });

    $('#item-type-lists').on('change', function(){
      window.location.href = '/itemtypes/' + $('#item-type-lists').val();
    });

    $('input[type=radio][name=item_type]').on ('change', function(){
        if (this.value === 'normal') {
            $('option.normal_type').show()
            $('option.harvesting_type').hide()
        } else {
            $('option.normal_type').hide()
            $('option.harvesting_type').show()
        }
    });

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
      page_global.table_row_map['mapping'] = {};
      page_global.table_row_map['form'] = [];
      page_global.table_row_map['schema'] = {
        $schema: "http://json-schema.org/draft-04/schema#",
        type: "object",
        description: "",
        properties: {},
        required: []
      };

      // コンテンツ本体
      if(page_global.upload_file) {
        page_global.table_row_map.schema.properties["filemeta"] = {
          type:"array",
          title:"コンテンツ本体",
          items:{
            type: "object",
            properties: {
              filename: {
                type: "string",
                title: "表示名"
              },
              displaytype: {
                type: "string",
                title: "表示形式",
                enum: ["detail","simple","preview"]
              },
              licensetype: {
                type: "string",
                title: "ライセンス",
                enum: ["license_free","license_0","license_1","license_2","license_3","license_4","license_5"]
              },
              licensefree: {
                type: "string"
              },
              accessrole: {
                type: "string",
                title: "アクセス",
                enum: ["open_access","open_date","open_login","open_no"]
              },
              accessdate: {
                type: "string",
                title: "公開日"
              },
              groups: {
                type: "string",
                title: "グループ名"
              }
            }
          }
        }
        page_global.table_row_map.form.push({
          key:"filemeta",
          title:"コンテンツ本体",
          add: "New",
          style: {
            add: "btn-success"
          },
          items: [
            {
              key: "filemeta[].filename",
              type: "select",
              title: "表示名",
              title_i18n:{ja:"表示名",en:"FileName"}
            },
            {
              key: "filemeta[].displaytype",
              type: "select",
              title: "表示形式",
              title_i18n:{ja:"表示形式",en:"Preview"},
              titleMap: [
                {value: "detail", name: "詳細表示"},
                {value: "simple", name: "簡易表示"},
                {value: "preview", name: "プレビュー"}
              ]
            },
            {
              key: "filemeta[].licensetype",
              type: "select",
              title: "ライセンス",
              title_i18n:{ja:"ライセンス",en:"License"},
              titleMap: [
                {value: "license_free", name: "自由入力"},
                {value: "license_0", name: "Creative Commons : 表示"},
                {value: "license_1", name: "Creative Commons : 表示 - 継承"},
                {value: "license_2", name: "Creative Commons : 表示 - 改変禁止"},
                {value: "license_3", name: "Creative Commons : 表示 - 非営利"},
                {value: "license_4", name: "Creative Commons : 表示 - 非営利 - 継承"},
                {value: "license_5", name: "Creative Commons : 表示 - 非営利 - 改変禁止"}
              ]
            },
            {
              key: "filemeta[].licensefree",
              type: "textarea",
              notitle: true,
              condition: "model.filemeta[arrayIndex].licensetype == 'license_free'"
            },
            {
              title: '剽窃チェック',
              title_i18n:{ja:"剽窃チェック",en:"Check Plagiarism"},
              type: "template",
              template: "<div class='text-center'><a class='btn btn-primary' href='/ezas/pdf-detect-weko.html' target='_blank' role='button'>{{ form.title }}</a></div>"
            },
            {
              key: "filemeta[].accessrole",
              type: "radios",
              title: "アクセス",
              title_i18n:{ja:"アクセス",en:"Access"},
              titleMap: [
                {value: "open_access", name: "オープンアクセス"},
                {value: "open_date", name: "オープンアクセス日を指定する"},
                {value: "open_login", name: "ログインユーザのみ"},
                {value: "open_no", name: "公開しない"}
              ]
            },
            {
              key: "filemeta[].accessdate",
              title: "公開日",
              title_i18n:{ja:"公開日",en:"Opendate"},
              type: "template",
              format: "yyyy-MM-dd",
              templateUrl: "/static/templates/weko_deposit/datepicker.html",
              condition: "model.filemeta[arrayIndex].accessrole == 'open_date'"
            },
            {
              key: "filemeta[].groups",
              title: "グループ",
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

      // タイトルなどを追加する
      page_global.table_row_map.schema.properties["title_ja"] = {type:"string",title:"タイトル",format:"text"}
      page_global.table_row_map.schema.properties["title_en"] = {type:"string",title:"タイトル(英)",format:"text"}
      page_global.table_row_map.form.push({type:"fieldset",title:"タイトル",title_i18n:{ja:"タイトル",en:"Title"},items:[{type:"text",key:"title_ja",title:"タイトル",title_i18n:{ja:"タイトル",en:"Title"},required:true},{type:"text",key:"title_en",title:"タイトル(英)",title_i18n:{ja:"タイトル(英)",en:"Title(English)"},required:true}]});
      page_global.table_row_map.schema.properties["lang"] = {type:"string",title:"言語",format:"select",enum:["en","ja"]}
      page_global.table_row_map.form.push({key:"lang",type:"select",title:"言語",title_i18n:{ja:"言語",en:"Language"},required: true,titleMap:{"en":"英語","ja":"日本語"}});
      page_global.table_row_map.schema.properties["pubdate"] = {type:"string",title:"公開日",format:"datetime"}
      page_global.table_row_map.form.push({key:"pubdate",type:"template",title:"公開日",title_i18n:{ja:"公開日",en:"PubDate"},required: true,format: "yyyy-MM-dd",templateUrl: "/static/templates/weko_deposit/datepicker.html"});
      page_global.table_row_map.schema.properties["keywords"] = {type:"string",title:"キーワード",format:"text"}
      page_global.table_row_map.schema.properties["keywords_en"] = {type:"string",title:"キーワード(英)",format:"text"}
      page_global.table_row_map.form.push({type:"fieldset",title:"キーワード",title_i18n:{ja:"キーワード",en:"keywords"},items:[{type:"text",key:"keywords",title:"キーワード",title_i18n:{ja:"キーワード",en:"keywords"},required:true},{type:"text",key:"keywords_en",title:"キーワード(英)",title_i18n:{ja:"キーワード(英)",en:"keywords(English)"},required:true}]});
      page_global.table_row_map.schema.required.push("title_ja");
      page_global.table_row_map.schema.required.push("title_en");
      page_global.table_row_map.schema.required.push("lang");
      page_global.table_row_map.schema.required.push("pubdate");

      if(src_mapping.hasOwnProperty('title_ja')) {
        page_global.table_row_map.mapping['title_ja'] = src_mapping['title_ja'];
      } else {
        page_global.table_row_map.mapping['title_ja'] = mapping_value;
      }
      if(src_mapping.hasOwnProperty('title_en')) {
        page_global.table_row_map.mapping['title_en'] = src_mapping['title_en'];
      } else {
        page_global.table_row_map.mapping['title_en'] = mapping_value;
      }
      if(src_mapping.hasOwnProperty('lang')) {
        page_global.table_row_map.mapping['lang'] = src_mapping['lang'];
      } else {
        page_global.table_row_map.mapping['lang'] = mapping_value;
      }
      if(src_mapping.hasOwnProperty('pubdate')) {
        page_global.table_row_map.mapping['pubdate'] = src_mapping['pubdate'];
      } else {
        page_global.table_row_map.mapping['pubdate'] = mapping_value;
      }
      if(src_mapping.hasOwnProperty('keywords')) {
        page_global.table_row_map.mapping['keywords'] = src_mapping['keywords'];
      } else {
        page_global.table_row_map.mapping['keywords'] = mapping_value;
      }
      if(src_mapping.hasOwnProperty('keywords_en')) {
        page_global.table_row_map.mapping['keywords_en'] = src_mapping['keywords_en'];
      } else {
        page_global.table_row_map.mapping['keywords_en'] = mapping_value;
      }

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

        if(src_render.hasOwnProperty('meta_list')
            && src_render['meta_list'].hasOwnProperty(row_id)) {
          if(tmp.input_type == src_render['meta_list'][row_id]['input_type']) {
            if(src_mapping.hasOwnProperty('keywords_en')) {
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
      //////add by ryuu. 0313 start
      //タイトル
      var tmp_title_ja = {}
        tmp_title_ja.title = "タイトル";
        //add by ryuu. start
        tmp_title_ja.title_i18n ={}
        tmp_title_ja.title_i18n.ja = "タイトル";
        tmp_title_ja.title_i18n.en = "Title";
        //add by ryuu. end
        tmp_title_ja.input_type = "text";
        tmp_title_ja.input_value = "";
        tmp_title_ja.option = {}
        tmp_title_ja.option.required = $('#chk_title_0').is(':checked')?true:false;
        tmp_title_ja.option.multiple = $('#chk_title_1').is(':checked')?true:false;
        tmp_title_ja.option.hidden = $('#chk_title_4').is(':checked')?true:false;
        tmp_title_ja.option.showlist = tmp_title_ja.option.hidden?false:($('#chk_title_2').is(':checked')?true:false);
        tmp_title_ja.option.crtf = tmp_title_ja.option.hidden?false:($('#chk_title_3').is(':checked')?true:false);
        //タイトル(英)
        var tmp_title_en = {}
        tmp_title_en.title = "タイトル(英)";
        //add by ryuu. start
        tmp_title_en.title_i18n ={}
        tmp_title_en.title_i18n.ja = "タイトル(英)";
        tmp_title_en.title_i18n.en = "Title(English)";
        //add by ryuu. end
        tmp_title_en.input_type = "text";
        tmp_title_en.input_value = "";
        tmp_title_en.option = {}
        tmp_title_en.option.required = $('#chk_title_en_0').is(':checked')?true:false;
        tmp_title_en.option.multiple = $('#chk_title_en_1').is(':checked')?true:false;
        tmp_title_en.option.hidden = $('#chk_title_en_4').is(':checked')?true:false;
        tmp_title_en.option.showlist = tmp_title_en.option.hidden?false:($('#chk_title_en_2').is(':checked')?true:false);
        tmp_title_en.option.crtf = tmp_title_en.option.hidden?false:($('#chk_title_en_3').is(':checked')?true:false);

        //言語
        var tmp_lang = {}
        tmp_lang.title = "言語";
        //add by ryuu. start
        tmp_lang.title_i18n ={}
        tmp_lang.title_i18n.ja = "言語";
        tmp_lang.title_i18n.en = "Language";
        //add by ryuu. end
        tmp_lang.input_type = "text";
        tmp_lang.input_value = "";
        tmp_lang.option = {}
        tmp_lang.option.required = $('#chk_lang_0').is(':checked')?true:false;
        tmp_lang.option.multiple = $('#chk_lang_1').is(':checked')?true:false;
        tmp_lang.option.hidden = $('#chk_lang_4').is(':checked')?true:false;
        tmp_lang.option.showlist = tmp_lang.option.hidden?false:($('#chk_lang_2').is(':checked')?true:false);
        tmp_lang.option.crtf = tmp_lang.option.hidden?false:($('#chk_lang_3').is(':checked')?true:false);

        //公開日
        var tmp_pubdate = {}
        tmp_pubdate.title = "公開日";
        //add by ryuu. start
        tmp_pubdate.title_i18n ={}
        tmp_pubdate.title_i18n.ja = "公開日";
        tmp_pubdate.title_i18n.en = "PubDate";
        //add by ryuu. end
        tmp_pubdate.input_type = "datetime";
        tmp_pubdate.input_value = "";
        tmp_pubdate.option = {}
        tmp_pubdate.option.required = $('#chk_pubdate_0').is(':checked')?true:false;
        tmp_pubdate.option.multiple = $('#chk_pubdate_1').is(':checked')?true:false;
        tmp_pubdate.option.hidden = $('#chk_pubdate_4').is(':checked')?true:false;
        tmp_pubdate.option.showlist = tmp_pubdate.option.hidden?false:($('#chk_pubdate_2').is(':checked')?true:false);
        tmp_pubdate.option.crtf = tmp_pubdate.option.hidden?false:($('#chk_pubdate_3').is(':checked')?true:false);

        //キーワード
        var tmp_keywords_ja = {}
        tmp_keywords_ja.title = "キーワード";
        //add by ryuu. start
        tmp_keywords_ja.title_i18n ={}
        tmp_keywords_ja.title_i18n.ja = "キーワード";
        tmp_keywords_ja.title_i18n.en = "keywords";
        //add by ryuu. end
        tmp_keywords_ja.input_type = "text";
        tmp_keywords_ja.input_value = "";
        tmp_keywords_ja.option = {}
        tmp_keywords_ja.option.required = $('#chk_keyword_0').is(':checked')?true:false;
        tmp_keywords_ja.option.multiple = $('#chk_keyword_1').is(':checked')?true:false;
        tmp_keywords_ja.option.hidden = $('#chk_keyword_4').is(':checked')?true:false;
        tmp_keywords_ja.option.showlist = tmp_keywords_ja.option.hidden?false:($('#chk_keyword_2').is(':checked')?true:false);
        tmp_keywords_ja.option.crtf = tmp_keywords_ja.option.hidden?false:($('#chk_keyword_3').is(':checked')?true:false);

        //キーワード(英)
        var tmp_keywords_en = {}
        tmp_keywords_en.title = "キーワード(英)";
        //add by ryuu. start
        tmp_keywords_en.title_i18n ={}
        tmp_keywords_en.title_i18n.ja = "キーワード(英)";
        tmp_keywords_en.title_i18n.en = "keywords(English)";
        //add by ryuu. end
        tmp_keywords_en.input_type = "text";
        tmp_keywords_en.input_value = "";
        tmp_keywords_en.option = {}
        tmp_keywords_en.option.required = $('#chk_keyword_en_0').is(':checked')?true:false;
        tmp_keywords_en.option.multiple = $('#chk_keyword_en_1').is(':checked')?true:false;
        tmp_keywords_en.option.hidden = $('#chk_keyword_en_4').is(':checked')?true:false;
        tmp_keywords_en.option.showlist = tmp_keywords_en.option.hidden?false:($('#chk_keyword_en_2').is(':checked')?true:false);
        tmp_keywords_en.option.crtf = tmp_keywords_en.option.hidden?false:($('#chk_keyword_en_3').is(':checked')?true:false);
        //設定
        page_global.meta_fix["title_ja"] = tmp_title_ja;
        page_global.meta_fix["title_en"] = tmp_title_en;
        page_global.meta_fix["lang"] = tmp_lang;
        page_global.meta_fix["pubdate"] = tmp_pubdate;
        page_global.meta_fix["keywords"] = tmp_keywords_ja;
        page_global.meta_fix["keywords_en"] = tmp_keywords_en;

      //////add by ryuu. 0313 end
    }

    // add new meta table row
    $('#btn_new_itemtype_meta').on('click', function(){
      new_meta_row('item_'+$.now());
    });
    function new_meta_row(row_id) {
      var row_template = '<tr id="tr_' + row_id + '">'
          + '<td><input type="text" class="form-control" id="txt_title_' + row_id + '" value="">'
          + '  <div class="hide" id="text_title_JaEn_' + row_id + '">'
          +'     <p>日本語：</p>'
          +'     <input type="text" class="form-control" id="txt_title_ja_' + row_id + '" value="">'
          +'     <p>英語：</p>'
          +'     <input type="text" class="form-control" id="txt_title_en_' + row_id + '" value="">'
          + '  </div>'
          +'   <button type="button" class="btn btn-link" id="btn_link_' + row_id + '">多言語設定</button>'
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
          + '   <label><input type="checkbox" id="chk_' + row_id + '_0" value="required">必須</label>'
          + '  </div>'
          + '  <div class="checkbox" id="chk_prev_' + row_id + '_1">'
          + '    <label><input type="checkbox" id="chk_' + row_id + '_1" value="multiple">複数可</label>'
          + '  </div>'
          + '  <div class="checkbox" id="chk_prev_' + row_id + '_2">'
          + '    <label><input type="checkbox" id="chk_' + row_id + '_2" value="showlist">一覧表示</label>'
          + '  </div>'
          + '  <div class="checkbox" id="chk_prev_' + row_id + '_3">'
          + '    <label><input type="checkbox" id="chk_' + row_id + '_3" value="crtf">改行指定</label>'
          + '  </div>'
          + '  <div class="checkbox" id="chk_prev_' + row_id + '_4">'
          + '    <label><input type="checkbox" id="chk_' + row_id + '_4" value="hidden">非表示</label>'
          + '  </div>'
          + '</td>'
          + '<td>'
          + '  <div class="btn-group-vertical" role="group" aria-label="入替">'
          + '    <button type="button" class="btn btn-default sortable_up" id="btn_up_' + row_id + '" metaid="' + row_id + '">↑</button>'
          + '    <button type="button" class="btn btn-default sortable_down" id="btn_down_' + row_id + '" metaid="' + row_id + '">↓</button>'
          + '  </div>'
          + '</td>'
          + '<td>'
          + '  <button type="button" class="btn btn-danger" id="btn_del_' + row_id + '">削除</button>'
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
        + 'value="' + initval + '" placeholder="選択肢を「|」区切りで入力して下さい"></div></div>');
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
        success: function(data,textStatus){
          $('.modal-body').text(data.msg);
          $('#myModal').modal('show');
        },
        error: function(textStatus,errorThrown){
          $('.modal-body').text('Error: ' + JSON.stringify(textStatus));
          $('#myModal').modal('show');
        }
      });
    }

    select_option = '';
    // 作成したメタデータ項目タイプの取得
    $.ajax({
      method: 'GET',
      url: '/itemtypes/property/list',
      async: false,
      success: function(data, status){
        properties_obj = data;

        defProps = data.defaults;
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
      $.get('/itemtypes/' + $('#item-type-lists').val() + '/render', function(data, status){
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
    }
});
