  require([
    "jquery",
    "bootstrap"
    ], function() {
    $('#myModal').modal({
      show: false
    })
    var page_global = {
      src_mapping_name:'',
      dst_mapping_name:'',
      showDiag: false,
      itemtype_prop:null,
      schema_prop:{},
      jpcoar_prop:null,
      mapping_prop:null,
      sub_itemtype_list:[],
      sub_jpcoar_list:[],
      sub_mapping_list:{}
    }
    page_global.src_mapping_name = $('#item-type-lists').val();
    page_global.dst_mapping_name = $('#item-type-lists').val();

    $("#item-type-lists").change(function (ev) {
      page_global.dst_mapping_name = $(this).val();
      if(page_global.showDiag) {
        $('.modal-title').text('提示');
        $('.modal-body').text('編集内容をキャンセルしてもよろしいですか？');
        $('#btn_submit').addClass('hide');
        $('#btn_confirm').removeClass('hide');
        $('#myModal').modal('show');
      } else {
        window.location.href = '/itemtypes/mapping/' + page_global.dst_mapping_name + '?mapping_type=' + $('#jpcoar_lists').val();
      }
    });
    $('#myModal').on('hide.bs.modal', function (e) {
      $('#item-type-lists').val(page_global.src_mapping_name);
    })
    $('#btn_confirm').on('click', function(ev) {
      window.location.href = '/itemtypes/mapping/' + page_global.dst_mapping_name + '?mapping_type=' + $('#jpcoar_lists').val();
    });
    $("#jpcoar_lists").change(function (ev) {
      $('li.list-group-item').addClass('hide');
      $('li.list_'+$(this).val()).removeClass('hide');
      $('#sub_children_lists div.sub_child_list').remove();
      $('#sub_children_lists hr').remove();
      if($('li.list_'+$(this).val()).find('input[type="radio"]:checked').length > 0) {
        $('li.list_'+$(this).val()).find('input[type="radio"]:checked').trigger('click');
      } else {
        let new_sub_info = $('div.sub_children_list').clone(true);
        new_sub_info.removeClass('sub_children_list hide').addClass('sub_child_list');
        new_sub_info.appendTo('#sub_children_lists');
      }
    });
    $('input[type="text"]').on('focusout', function(ev){
      if($(this).val().length > 0) {
        $(this).parent().removeClass('has-error');
      } else {
        $(this).parent().addClass('has-error');
      }
    });
    $('input[type="button"]').on('click', function(ev){
      action = this.dataset.action;
      page_global.showDiag = true;
      if('add' == action) {
        ul_key = '#ul_' + this.parentElement.dataset.key;
        li_key = ul_key+' li.list_'+$('#jpcoar_lists').val()+':last';
        $(li_key).clone(true).appendTo(ul_key);
      }
      if('add_child' == action) {
        let parent_li = $(this).parents('.sub_child_list');
        parent_li.find('.sub_child_itemtype_list:last').clone(true)
                 .appendTo(parent_li.find('.sub_children_itemtype_list'));
        if(parent_li.find('.sub_child_itemtype_list').length > 1) {
          parent_li.find('.sub_itemtype_link').removeClass('hide');
          parent_li.find('.sub_itemtype_link').find('.form-group').removeClass('hide');
        }
        parent_li.find('.sub_itemtype_link:last').find('.form-group').addClass('hide');
      }
      if('del' == action) {
        // mapping json info also need delete
        let parent_li = $(this).parents('.list-group-item');
        let is_checked = parent_li.find('input[type="radio"]').is(':checked');
        itemtype_key = parent_li.find('input[type="radio"]').val();
        mapping_key = parent_li.find('select').val();
        if(remove_mapping_parent_item(itemtype_key, mapping_key)) {
          $(this).parents('.list-group-item').remove();
          if(is_checked) {
            $('#sub-item-type-lists-label').text('Itemtype');
            $('#sub-jpcoar-lists-label').text('Schema');
            $('#sub_children_lists div.sub_child_list').remove();
            $('#sub_children_lists hr').remove();
            let new_sub_info = $('div.sub_children_list').clone(true);
            new_sub_info.removeClass('sub_children_list hide').addClass('sub_child_list');
            new_sub_info.appendTo('#sub_children_lists');
          }
          $('#preview_mapping').text(JSON.stringify(page_global.mapping_prop, null, 4));
        }
      }
      if('del_child' == action) {
        let parent_li = $(this).parents('.sub_child_list');
        itemtype_key = $('input[type="radio"]:checked').val();
        mapping_key = parent_li.find('select[name="sub_jpcoar_list"]').val();
        if(remove_mapping_child_item(itemtype_key, mapping_key)) {
          $(this).parents('.sub_child_list').remove();
          $('#preview_mapping').text(JSON.stringify(page_global.mapping_prop, null, 4));
        }
        if($('div.sub_child_list').length == 1) {
          $('div.sub_child_list').find('fieldset').attr('disabled', true);
        }
      }
      if('del_sub_child' == action) {
        $(this).parents('.sub_child_itemtype_list').removeClass('sub_child_itemtype_list').addClass('sub_child_itemtype_del');
        $(this).parents('.sub_children_itemtype_list').find('.sub_child_itemtype_list:last').find('.sub_itemtype_link').find('.form-group').addClass('hide');
        $(this).parents('.sub_children_itemtype_list').find('.sub_child_itemtype_list:last').find('.sub_itemtype_link').find('input[type="text"]').val("");
        if($(this).parents('.sub_children_itemtype_list').find('.sub_child_itemtype_list').length == 1) {
          $(this).parents('.sub_children_itemtype_list').find('.sub_child_itemtype_list').find('.sub_itemtype_link').addClass('hide');
        }
        $(this).parents('.sub_child_itemtype_del').remove();
      }
    });
    function remove_mapping_parent_item(itemtype_key, mapping_key) {
      if(page_global.mapping_prop == null) {
        mapping_str = $('#hide_mapping_prop').text();
        page_global.mapping_prop = JSON.parse(mapping_str);
      }
      schema_name = $('#jpcoar_lists').val();
      if(page_global.mapping_prop.hasOwnProperty(itemtype_key)) {
        if(page_global.mapping_prop[itemtype_key].hasOwnProperty(schema_name)) {
          if(page_global.mapping_prop[itemtype_key][schema_name].hasOwnProperty(mapping_key)) {
            return delete page_global.mapping_prop[itemtype_key][schema_name][mapping_key];
          }
        }
      }
      return true;
    }
    function remove_mapping_child_item(itemtype_key, mapping_key) {
      if(page_global.mapping_prop == null) {
        mapping_str = $('#hide_mapping_prop').text();
        page_global.mapping_prop = JSON.parse(mapping_str);
      }
      schema_name = $('#jpcoar_lists').val();
      sub_jpcoar_arr = mapping_key.split('.');
      sub_sub_jpcoar = sub_jpcoar_arr.length>1?sub_jpcoar_arr.pop():'';
      if(page_global.mapping_prop.hasOwnProperty(itemtype_key)) {
        if(page_global.mapping_prop[itemtype_key].hasOwnProperty(schema_name)) {
          if(sub_sub_jpcoar.length == 0) {
            if(page_global.mapping_prop[itemtype_key][schema_name].hasOwnProperty(sub_jpcoar_arr)) {
              return delete page_global.mapping_prop[itemtype_key][schema_name][sub_jpcoar_arr];
            }
          } else {
            let cur_obj = page_global.mapping_prop[itemtype_key][schema_name];
            for(let idx=0; idx<sub_jpcoar_arr.length; idx++) {
              if(cur_obj.hasOwnProperty(sub_jpcoar_arr[idx])) {
                cur_obj = cur_obj[sub_jpcoar_arr[idx]];
                continue;
              }
              break;
            }
            if(cur_obj.hasOwnProperty(sub_sub_jpcoar)) {
              delete cur_obj[sub_sub_jpcoar];
            }
          }
        }
      }
      return true;
    }
    $('select[name="parent_list"]').on('change', function(ev){
      $(this).parent().find('input[type="radio"]').trigger('click');
    });
    $('input[type="radio"]').on('click', function(ev){
      $('tr').removeClass('active');
      $(this).parents('tr').addClass('active');
      item_type_key = $(this).val();
      jpcoar_key = $(this).parents('.form-inline').find('select').val();
      display_sub_lists(item_type_key, jpcoar_key);
      if($('div.sub_child_list').length == 1) {
        $('div.sub_child_list').find('fieldset').attr('disabled', true);
      }
    });
    function display_sub_lists(item_type_key, jpcoar_key) {
      if(page_global.itemtype_prop == null) {
        item_type_str = $('#hide_itemtype_prop').text();
        page_global.itemtype_prop = JSON.parse(item_type_str);
      }
      schema_name_str = $('#jpcoar_lists').val();
      if(!page_global.schema_prop.hasOwnProperty(schema_name_str)) {
        schema_str = $('#hide_'+schema_name_str).text();
        page_global.schema_prop[schema_name_str] = JSON.parse(schema_str);
      }
      if(page_global.mapping_prop == null) {
        mapping_str = $('#hide_mapping_prop').text();
        page_global.mapping_prop = JSON.parse(mapping_str);
      }
      page_global.sub_mapping_list={}
      if(page_global.mapping_prop.hasOwnProperty(item_type_key)) {
        if(page_global.mapping_prop[item_type_key].hasOwnProperty(schema_name_str)) {
          if(page_global.mapping_prop[item_type_key][schema_name_str].hasOwnProperty(jpcoar_key)) {
            make_list_mapping(page_global.mapping_prop[item_type_key][schema_name_str][jpcoar_key],jpcoar_key);
          }
        }
      }
      // item_type sub_list logic
      sub_itemtype_items = page_global.itemtype_prop[item_type_key];
      page_global.sub_itemtype_list=[];
      make_list_itemtype(sub_itemtype_items, item_type_key, '');
      $('#sub-item-type-lists-label').text(sub_itemtype_items['title']);
      // jpcoar sub_list logic
      sub_jpcoar_items = page_global.schema_prop[schema_name_str][jpcoar_key];
      page_global.sub_jpcoar_list=[];
      make_list_jpcoar(sub_jpcoar_items, jpcoar_key);
      $('#sub-jpcoar-lists-label').text(jpcoar_key);
      $('#sub_children_lists div.sub_child_list').remove();
      $('#sub_children_lists hr').remove();
      let re = /\s*;\s*|\s*,\s*|\s*-\s*|\s*:\s*/g;
      if(Object.keys(page_global.sub_mapping_list).length > 0) {
        Object.entries(page_global.sub_mapping_list).forEach(([key, value]) => {
          let new_sub_info = $('div.sub_children_list').clone(true);
          if(page_global.sub_itemtype_list.length > 0) {
            let sub_itemtype_sub_keys = value.split(re);
            if(sub_itemtype_sub_keys.length > 1) {
              let sub_itemtype_sub_info = new_sub_info.find('.sub_child_itemtype_list').clone(true);
              new_sub_info.find('.sub_children_itemtype_list').empty();
              sub_itemtype_sub_keys.forEach(function(sub_val){
                let split_str = value.substr(value.indexOf(sub_val)+sub_val.length, 1);
                let sub_itemtype_sub_info_temp = sub_itemtype_sub_info.clone(true);
                sub_itemtype_sub_info_temp.find('select[name="sub_itemtype_list"]').empty();
                page_global.sub_itemtype_list.forEach(function(element){
                  let display_name = element[1].length>0?element[1]:$('#sub-item-type-lists-label').text();
                  if(element[0].endsWith(sub_val)) {
                    sub_itemtype_sub_info_temp.find('select[name="sub_itemtype_list"]').append('<option value="'+element[0]+'" selected>'+display_name+'</option>');
                  } else {
                    sub_itemtype_sub_info_temp.find('select[name="sub_itemtype_list"]').append('<option value="'+element[0]+'">'+display_name+'</option>');
                  }
                });
                if(split_str.length > 0) {
                  sub_itemtype_sub_info_temp.find('input[type="text"]').val(split_str);
                  sub_itemtype_sub_info_temp.find('input[type="text"]').parent().removeClass('has-error');
                }
                sub_itemtype_sub_info_temp.find('.sub_itemtype_link').removeClass('hide');
                sub_itemtype_sub_info_temp.appendTo(new_sub_info.find('.sub_children_itemtype_list'));
              });
              new_sub_info.find('.sub_child_itemtype_list:last').find('.sub_itemtype_link').find('.form-group').addClass('hide');
            } else {
              new_sub_info.find('select[name="sub_itemtype_list"]').empty();
              page_global.sub_itemtype_list.forEach(function(element){
                let display_name = element[1].length>0?element[1]:$('#sub-item-type-lists-label').text();
                if(element[0].endsWith(value)) {
                  new_sub_info.find('select[name="sub_itemtype_list"]').append('<option value="'+element[0]+'" selected>'+display_name+'</option>');
                } else {
                  new_sub_info.find('select[name="sub_itemtype_list"]').append('<option value="'+element[0]+'">'+display_name+'</option>');
                }
              });
            }
          }
          if(page_global.sub_jpcoar_list.length > 0) {
            new_sub_info.find('select[name="sub_jpcoar_list"]').empty();
            page_global.sub_jpcoar_list.forEach(function(element){
              new_sub_info.find('select[name="sub_jpcoar_list"]').append('<option value="'+element+'">'+element+'</option>');
            });
            new_sub_info.find('select[name="sub_jpcoar_list"]').val(key);
          }
          new_sub_info.removeClass('sub_children_list hide').addClass('sub_child_list');
          new_sub_info.appendTo('#sub_children_lists');
          new_sub_info.after("<hr>");
        });
      } else {
        let new_sub_info = $('div.sub_children_list').clone(true);
        if(page_global.sub_itemtype_list.length > 0) {
          new_sub_info.find('select[name="sub_itemtype_list"]').empty();
          page_global.sub_itemtype_list.forEach(function(element){
            let display_name = element[1].length>0?element[1]:$('#sub-item-type-lists-label').text();
            new_sub_info.find('select[name="sub_itemtype_list"]').append('<option value="'+element[0]+'">'+display_name+'</option>');
          });
        }
        if(page_global.sub_jpcoar_list.length > 0) {
          new_sub_info.find('select[name="sub_jpcoar_list"]').empty();
          page_global.sub_jpcoar_list.forEach(function(element){
            new_sub_info.find('select[name="sub_jpcoar_list"]').append('<option value="'+element+'">'+element+'</option>');
          });
        }
        new_sub_info.removeClass('sub_children_list hide').addClass('sub_child_list');
        new_sub_info.appendTo('#sub_children_lists');
      }
    }
    function make_list_mapping(entries, jpcoar_key) {
      if(typeof entries == "string") {
        page_global.sub_mapping_list[jpcoar_key] = entries;
      } else if(typeof entries == "object") {
        Object.entries(entries).forEach(([key, value]) => {
          if(!key.startsWith('@')) {
            make_list_mapping(value, [jpcoar_key, key].join('.'));
          }
        });
      }
    }
    function make_list_itemtype(entries, base_key, base_title) {
      if(entries['type'] == 'object') {
        for(const [key, value] of Object.entries(entries['properties'])) {
          make_list_itemtype(value, [base_key, key].join('.'), [base_title, value['title']].join('.'));
        }
      } else if(entries['type'] == 'array') {
        for(const [key, value] of Object.entries(entries['items']['properties'])) {
          make_list_itemtype(value, [base_key, key].join('.'), [base_title, value['title']].join('.'));
        }
      } else {
        page_global.sub_itemtype_list.push([base_key, base_title.slice(1)]);
      }
      return;
    }
    function make_list_jpcoar(entries, base_key) {
      if(Object.keys(entries).length > 1) {
        for(const [key, value] of Object.entries(entries)) {
          if('type' == key) continue;
          make_list_jpcoar(value, [base_key, key].join('.'));
        }
      } else {
        page_global.sub_jpcoar_list.push(base_key);
      }
      return;
    }

    $('#sub_mapping-add').on('click', function(ev){
      page_global.showDiag = true;
      let new_sub_info = $('div.sub_children_list').clone(true);
      if(page_global.sub_itemtype_list.length > 0) {
        new_sub_info.find('select[name="sub_itemtype_list"]').empty();
        page_global.sub_itemtype_list.forEach(function(element){
          let display_name = element[1].length>0?element[1]:$('#sub-item-type-lists-label').text();
          new_sub_info.find('select[name="sub_itemtype_list"]').append('<option value="'+element[0]+'">'+display_name+'</option>');
        });
      }
      if(page_global.sub_jpcoar_list.length > 0) {
          new_sub_info.find('select[name="sub_jpcoar_list"]').empty();
          page_global.sub_jpcoar_list.forEach(function(element){
            new_sub_info.find('select[name="sub_jpcoar_list"]').append('<option value="'+element+'">'+element+'</option>');
          });
        }
      new_sub_info.removeClass('sub_children_list hide').addClass('sub_child_list');
      new_sub_info.appendTo('#sub_children_lists');
      new_sub_info.after("<hr>");
      $('div.sub_child_list').find('fieldset').removeAttr('disabled');
    });
    $('#sub_mapping-create').on('click', function(ev){
      if(page_global.mapping_prop == null) {
        mapping_str = $('#hide_mapping_prop').text();
        page_global.mapping_prop = JSON.parse(mapping_str);
      }
      page_global.showDiag = true;
      sub_itemtype_list = [];
      $('div .sub_child_list').each((index, element) => {
        sub_temp_itemtype = {
          sub_jpcoar: null,
          sub_itemtypes: null
        };
        sub_temp_itemtype.sub_jpcoar = $(element).find('select[name="sub_jpcoar_list"]').val();
        if($(element).find('.sub_child_itemtype_list').length > 1) {
          sub_temp_itemtype.sub_itemtypes = [];
          $(element).find('.sub_child_itemtype_list').each((idx, elm) => {
            sub_itemtype_key = {
              itemtype_key: null,
              itemlink_key: null
            };
            sub_itemtype_key.itemtype_key = $(elm).find('select[name="sub_itemtype_list"]').val();
            sub_itemtype_key.itemlink_key = $(elm).find('input[type="text"]').val();
            sub_temp_itemtype.sub_itemtypes.push(sub_itemtype_key);
          });
        } else {
          sub_temp_itemtype.sub_itemtypes = $(element).find('select[name="sub_itemtype_list"]').val();
        }
        sub_itemtype_list.push(sub_temp_itemtype);
      });
      let jpcoar_type = $("#jpcoar_lists").val();
      let itemtype_key = $('input[type="radio"]:checked').val();
      sub_itemtype_list.forEach(function(element){
        if(element.sub_jpcoar && element.sub_jpcoar.length > 0) {
          let sub_itemtypes = element.sub_itemtypes;
          let sub_jpcoar = element.sub_jpcoar;
          // sub_itemtype_arr = sub_itemtype.split('.');
          let sub_jpcoar_arr = sub_jpcoar.split('.');
          // sub_sub_itemtype = sub_itemtype_arr.length>1?sub_itemtype_arr.pop():'';
          if(!page_global.mapping_prop.hasOwnProperty(itemtype_key)) {
            page_global.mapping_prop[itemtype_key] = {};
            page_global.mapping_prop[itemtype_key][jpcoar_type] = {};
          }
          cur_obj = page_global.mapping_prop[itemtype_key];
          if(typeof cur_obj[jpcoar_type] != 'object') {
            cur_obj[jpcoar_type] = {};
          }
          cur_obj = cur_obj[jpcoar_type];
          for(let idx = 0; idx < sub_jpcoar_arr.length; idx++) {
            if(idx < sub_jpcoar_arr.length -1) {
              if(!cur_obj.hasOwnProperty(sub_jpcoar_arr[idx])) {
                cur_obj[sub_jpcoar_arr[idx]] = {};
              }
            } else {
              sub_sub_itemtype = '';
              if(typeof sub_itemtypes == 'object') {
                if(sub_itemtypes.length > 0) {
                  sub_itemtypes.forEach(elm => {
                    sub_sub_itemtype = sub_sub_itemtype + elm.itemtype_key.split('.').pop() + elm.itemlink_key;
                  });
                }
              } else {
                sub_sub_itemtype = sub_itemtypes.split('.').pop();
              }
              if(typeof cur_obj[sub_jpcoar_arr[idx]] == 'object') {
                if(sub_sub_itemtype.length > 0) {
                  cur_obj[sub_jpcoar_arr[idx]]['@value'] = sub_sub_itemtype;
                }
              } else {
                cur_obj[sub_jpcoar_arr[idx]] = sub_sub_itemtype;
              }
            }
            cur_obj = cur_obj[sub_jpcoar_arr[idx]];
          }
        }
      });
      $('#preview_mapping').text(JSON.stringify(page_global.mapping_prop, null, 4));
    });

    $('#mapping-submit').on('click', function(){
      var data = {
        item_type_id: parseInt($('#item-type-lists').val()),
        mapping: page_global.mapping_prop
      };
      send('/itemtypes/mapping', data);
    });

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
    if(!page_global.schema_prop.hasOwnProperty('jpcoar_mapping')) {
      $.ajax({
        method: 'GET',
        url: '/itemtypes/mapping/schema/jpcoar_mapping',
        async: true,
        contentType: 'application/json',
        dataType: 'json',
        success: function(data,textStatus){
          page_global.schema_prop['jpcoar_mapping'] = data.jpcoar_mapping;
        },
        error: function(textStatus,errorThrown){
        }
      });
    }
});
