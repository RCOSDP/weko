//require(["jquery", "bootstrap"], function() {});
$(document).ready(function () {
  $('#myModal').modal({
    show: false
  })

  if (!String.prototype.endsWith) {
    String.prototype.endsWith = function (search, this_len) {
      if (this_len === undefined || this_len > this.length) {
        this_len = this.length;
      }
      return this.substring(this_len - search.length, this_len) === search;
    };
  }

  if (!String.prototype.startsWith) {
    Object.defineProperty(String.prototype, 'startsWith', {
      value: function (search, rawPos) {
        var pos = rawPos > 0 ? rawPos | 0 : 0;
        return this.substring(pos, pos + search.length) === search;
      }
    });
  }

  var page_global = {
    src_mapping_name:'',
    dst_mapping_name:'',
    showDiag: false,
    hasError: false,
    itemtype_prop:null,
    schema_prop:{},
    jpcoar_prop:null,
    mapping_prop:null,
    sub_itemtype_list:[],
    sub_jpcoar_list:[],
    sub_mapping_list:{},
    meta_system:null,
  }
  page_global.src_mapping_name = $('#item-type-lists').val();
  page_global.dst_mapping_name = $('#item-type-lists').val();
  page_global.meta_system = JSON.parse($('#meta_system').text());
  page_global.mapping_prop = JSON.parse($('#hide_mapping_prop').text());

  initPropertiesItems()

  function addAlert(message) {
      $('#alerts').append(
          '<div class="alert alert-light" id="alert-style">' +
          '<button type="button" class="close" data-dismiss="alert">' +
          '&times;</button>' + message + '</div>');
       }

   function addError(message,err_items) {
    message += '<br/>'
     err_items.forEach(function(items){
       message += '[' + items[0] + ' && ' + items[1] + ']' + '<br/>'
     })
    $('#errors').append(
        '<div class="alert alert-danger alert-dismissable">' +
        '<button type="button" class="close" data-dismiss="alert" aria-hidden="true">' +
        '&times;</button>' + message + '</div>');
     }

  function initPropertiesItems(){
    $(".list-group-prop-items").each(function( index ) {
      if ($(this).children(".list_jpcoar_mapping").length > 1 && $("#is-system-admin").val() === 'True'){
        $(this).children(".list_jpcoar_mapping").find("button").prop("disabled", false);
      }
    });
  }

  $("#item-type-lists").change(function (ev) {
    page_global.dst_mapping_name = $(this).val();
    if(page_global.showDiag) {
      $('.modal-title').text('Present');
      $('.modal-body').text('Would you like to cancel your changes?');
      $('#btn_submit').addClass('hide');
      $('#btn_confirm').removeClass('hide');
      $('#myModal').modal('show');
    } else {
      $('#mapping-submit').addClass('disabled');
      window.location.href = '/admin/itemtypes/mapping/' + page_global.dst_mapping_name + '?mapping_type=' + $('#jpcoar_lists').val();
    }
  });
  $('#myModal').on('hide.bs.modal', function (e) {
    $('#item-type-lists').val(page_global.src_mapping_name);
  })
  $('#btn_confirm').on('click', function(ev) {
    window.location.href = '/admin/itemtypes/mapping/' + page_global.dst_mapping_name + '?mapping_type=' + $('#jpcoar_lists').val();
  });
  $("#jpcoar_lists").change(function (ev) {
    $('li.list-group-item').addClass('hide');
    $('li.list_'+$(this).val()).removeClass('hide');
    // $('#sub_children_lists div.sub_child_list').remove();
    // $('#jpcoar-props-lists').find('.jpcoar-prop-list').remove();
    if($('li.list_'+$(this).val()).find('input[type="radio"]:checked').length > 0) {
      $('li.list_'+$(this).val()).find('input[type="radio"]:checked').trigger('click');
    } else {
      reset_sub_children_lists();
      // let new_sub_info = $('div.sub_children_list').clone(true);
      // new_sub_info.removeClass('sub_children_list hide').addClass('sub_child_list');
      // new_sub_info.appendTo('#sub_children_lists');
    }
  });
  $('input.max-width-64[type="text"]').on('focusout', function(ev){
    if($(this).val().length > 0) {
      $(this).parent().removeClass('has-error');
    } else {
      $(this).parent().addClass('has-error');
    }
  });
  $('button[type="button"]').on('click', function(ev){
    action = this.dataset.action;
    page_global.showDiag = true;
    if('add' == action) {
      ul_key = '#ul_' + this.parentElement.dataset.key;
      li_key = ul_key+' li.list_'+$('#jpcoar_lists').val();
      li_key_last = ul_key+' li.list_'+$('#jpcoar_lists').val()+':last';
      if($(li_key).length == 1) {
        $(li_key).find('select[name="parent_list"]').find('option:first').remove();
        $(li_key).find('.btn-danger').removeAttr('disabled');
      }
      $(li_key_last).clone(true).appendTo(ul_key);
      // li_key_btn = ul_key+' li.list_'+$('#jpcoar_lists').val()+' input.btn-danger[type="button"]';
      // $(li_key_btn).removeAttr('disabled');
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
      ul_key = '#ul_' + this.parentElement.dataset.key;
      li_key = ul_key+' li.list_'+$('#jpcoar_lists').val();
      let parent_li = $(this).parents('.list-group-item');
      let is_checked = parent_li.find('input[type="radio"]').is(':checked');
      itemtype_key = parent_li.find('input[type="radio"]').val();
      mapping_key = parent_li.find('select').val();
      if(remove_mapping_parent_item(itemtype_key, mapping_key)) {
        $(this).parents('.list-group-item').remove();
        if(is_checked) {
          reset_sub_children_lists();
        }
        $('#preview_mapping').text(JSON.stringify(page_global.mapping_prop, null, 4));
        if($(li_key).length == 1) {
          $(li_key).find('select[name="parent_list"]').prepend('<option value=""></option>');
          $(li_key).find('.btn-danger').attr('disabled', true);
        }
      }
    }
    if('del_child' == action) {
      let parent_li = $(this).parents('.sub_child_list');
      itemtype_key = $('input[type="radio"]:checked').val();
      mapping_key = parent_li.find('select[name="sub_jpcoar_list"]').val();
      enableSelectOption(mapping_key);
      if(remove_mapping_child_item(itemtype_key, mapping_key)) {
        $(this).parents('.sub_child_list').remove();
        $('#preview_mapping').text(JSON.stringify(page_global.mapping_prop, null, 4));
      }
      if($('div.sub_child_list').length == 1) {
        $('div.sub_child_list').find('fieldset').attr('disabled', true);
      }
      saveMappingData();
      disableSubAddButton();
    }
    if('del_sub_child' == action) {
      $(this).parents('.sub_child_itemtype_list').removeClass('sub_child_itemtype_list').addClass('sub_child_itemtype_del');
      $(this).parents('.sub_children_itemtype_list').find('.sub_child_itemtype_list:last').find('.sub_itemtype_link').find('.form-group').addClass('hide');
      $(this).parents('.sub_children_itemtype_list').find('.sub_child_itemtype_list:last').find('.sub_itemtype_link').find('input[type="text"]').val("");
      if($(this).parents('.sub_children_itemtype_list').find('.sub_child_itemtype_list').length == 1) {
        $(this).parents('.sub_children_itemtype_list').find('.sub_child_itemtype_list').find('.sub_itemtype_link').addClass('hide');
      }
      $(this).parents('.sub_child_itemtype_del').remove();
      saveMappingData();
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
        if(mapping_key.length == 0) {
          page_global.mapping_prop[itemtype_key][schema_name] = mapping_key;
          return true;
        }
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
          let length_sub_jpcoar_arr = sub_jpcoar_arr.length;
          for(let idx=0; idx<length_sub_jpcoar_arr; idx++) {
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
    saveMappingData();
  });
  $('input[type="radio"]').on('click', function(ev){
    $('tr').removeClass('active');
    $(this).parents('tr').addClass('active');
    item_type_key = $(this).val();
    jpcoar_key = $(this).parents('.form-inline').find('select').val();
    if(jpcoar_key.length == 0) {
      remove_mapping_parent_item(item_type_key, jpcoar_key);
      reset_sub_children_lists();
      $('#preview_mapping').text(JSON.stringify(page_global.mapping_prop, null, 4));
      return;
    }
    display_sub_lists(item_type_key, jpcoar_key);
    display_parent_prop(jpcoar_key);
    if($('div.sub_child_list').length == 1) {
      $('div.sub_child_list').find('fieldset').attr('disabled', true);
    }
    disableSubAddButton();
    disableSubSelectOption();
  });
  function reset_sub_children_lists() {
    $('#sub-item-type-lists-label').text('Itemtype');
    $('#sub-jpcoar-lists-label').text('Schema');
    $('#sub_children_lists div.sub_child_list').remove();
    $('#jpcoar-props-lists').find('.jpcoar-prop-list').remove();
    let new_sub_info = $('div.sub_children_list').clone(true);
    new_sub_info.removeClass('sub_children_list hide').addClass('sub_child_list');
    new_sub_info.appendTo('#sub_children_lists');
  }
  function display_parent_prop(jpcoar_key) {
    $('#jpcoar-props-lists').find('.jpcoar-prop-list').remove();
    let itemtype_key = $('input[type="radio"]:checked').val();
    let schema_name_str = $('#jpcoar_lists').val();
    let sub_jpcoar_type = page_global.schema_prop[schema_name_str][jpcoar_key]['type'];
    if(sub_jpcoar_type.hasOwnProperty('attributes')) {
      let setting_prop = {};
      if(page_global.mapping_prop.hasOwnProperty(itemtype_key)) {
        if(page_global.mapping_prop[itemtype_key].hasOwnProperty(schema_name_str)) {
          if(page_global.mapping_prop[itemtype_key][schema_name_str].hasOwnProperty(jpcoar_key)) {
            if(page_global.mapping_prop[itemtype_key][schema_name_str][jpcoar_key].hasOwnProperty('@attributes')) {
              setting_prop = page_global.mapping_prop[itemtype_key][schema_name_str][jpcoar_key]['@attributes'];
            }
          }
        }
      }
      sub_jpcoar_type.attributes.forEach(function (element) {
        if(element.hasOwnProperty('restriction')) {
          let new_jpcoar_prop = $('.jpcoar-prop-select-temp').clone(true);
          new_jpcoar_prop.find('label').text(element.name);
          new_jpcoar_prop.find('p').text(element.use);
          if(element.restriction.hasOwnProperty('enumeration')) {
            element.restriction.enumeration.forEach(function (option) {
              new_jpcoar_prop.find('select').append('<option value="'+option+'">'+option+'</option>');
            });
            if(setting_prop.hasOwnProperty(element.name)) {
              new_jpcoar_prop.find('select').val(setting_prop[element.name]);
            }
          }
          new_jpcoar_prop.removeClass('jpcoar-prop-select-temp hide').addClass('jpcoar-prop-list jpcoar-prop-select-list');
          new_jpcoar_prop.appendTo('#jpcoar-props-lists');
        } else {
          let new_jpcoar_prop = $('.jpcoar-prop-text-temp').clone(true);
          new_jpcoar_prop.find('label').text(element.name);
          new_jpcoar_prop.find('p').text(element.use);
          if(setting_prop.hasOwnProperty(element.name)) {
            new_jpcoar_prop.find('input[type="text"]').val(setting_prop[element.name]);
          }
          new_jpcoar_prop.removeClass('jpcoar-prop-text-temp hide').addClass('jpcoar-prop-list jpcoar-prop-text-list');
          new_jpcoar_prop.appendTo('#jpcoar-props-lists');
        }
      });
    }
  }
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
    $('#sub-item-type-lists-label').text($('#label_item_' + item_type_key).text().trim());
    // jpcoar sub_list logic
    sub_jpcoar_items = page_global.schema_prop[schema_name_str][jpcoar_key];
    page_global.sub_jpcoar_list=[];
    if(schema_name_str === "jpcoar_mapping"){
      make_list_jpcoar(sub_jpcoar_items, jpcoar_key);
    }else{
      make_list_ddi(sub_jpcoar_items, jpcoar_key);
    }
    $('#sub-jpcoar-lists-label').text(jpcoar_key);
    $('#sub_children_lists div.sub_child_list').remove();
    let re = /\s*;\s*|\s*,\s*|\s*-\s*|\s*:\s*/g;
    if(Object.keys(page_global.sub_mapping_list).length > 0) {
      for(let key in page_global.sub_mapping_list) {
        let value = page_global.sub_mapping_list[key];
        let new_sub_info = $('div.sub_children_list').clone(true);
        if(value.startsWith("=")){
          new_sub_info.find('select[name="sub_itemtype_list"]').empty();
          new_sub_info.find('select[name="sub_itemtype_list"]').addClass('hide');
          new_sub_info.find('input[name="sub_itemtype_text"]').removeClass('hide');
          new_sub_info.find('input[name="sub_itemtype_text"]').val(value.substr(1));
        }else if (page_global.sub_itemtype_list.length > 0) {
          let sub_itemtype_sub_keys = value.split(re);
          if (sub_itemtype_sub_keys.length > 1) {
            let sub_itemtype_sub_info = new_sub_info.find('.sub_child_itemtype_list').clone(true);
            new_sub_info.find('.sub_children_itemtype_list').empty();
            sub_itemtype_sub_keys.forEach(function (sub_val) {
              let split_str = value.substr(value.indexOf(sub_val) + sub_val.length, 1);
              let sub_itemtype_sub_info_temp = sub_itemtype_sub_info.clone(true);
              sub_itemtype_sub_info_temp.find('select[name="sub_itemtype_list"]').empty();
              let find_select_sub_itemtype_list = sub_itemtype_sub_info_temp.find('select[name="sub_itemtype_list"]');
              let options = "";
              page_global.sub_itemtype_list.forEach(function (element) {
                let display_name = element[1].length > 0 ? element[1] : $('#sub-item-type-lists-label').text();
                if (element[0].endsWith(sub_val)) {
                  options += '<option value="' + element[0] + '" selected>' + display_name + '</option>';
                } else {
                  options += '<option value="' + element[0] + '">' + display_name + '</option>';
                }
              });
              find_select_sub_itemtype_list.append(options);
              if (split_str.length > 0) {
                sub_itemtype_sub_info_temp.find('input[type="text"]').val(split_str);
                sub_itemtype_sub_info_temp.find('input[type="text"]').parent().removeClass('has-error');
              }
              sub_itemtype_sub_info_temp.find('.sub_itemtype_link').removeClass('hide');
              sub_itemtype_sub_info_temp.appendTo(new_sub_info.find('.sub_children_itemtype_list'));
            });
            new_sub_info.find('.sub_child_itemtype_list:last').find('.sub_itemtype_link').find('.form-group').addClass('hide');
          } else {
            new_sub_info.find('select[name="sub_itemtype_list"]').empty();
            let find_select_sub_itemtype_list = new_sub_info.find('select[name="sub_itemtype_list"]');
            let options = "";
            page_global.sub_itemtype_list.forEach(function (element) {
              let display_name = element[1].length > 0 ? element[1] : $('#sub-item-type-lists-label').text();
              if (element[0].endsWith(value)) {
                options += '<option value="' + element[0] + '" selected>' + display_name + '</option>';
              } else {
                options += '<option value="' + element[0] + '">' + display_name + '</option>';
              }
            });
            find_select_sub_itemtype_list.append(options);
          }
          if (page_global.sub_itemtype_list.length == 1) {
            new_sub_info.find('select[name="sub_itemtype_list"]').attr('disabled', true);
          }
        }
        if (page_global.sub_jpcoar_list.length > 0) {
          new_sub_info.find('select[name="sub_jpcoar_list"]').empty();
          let find_select_sub_jpcoar_list = new_sub_info.find('select[name="sub_jpcoar_list"]');
          let options = "";
          page_global.sub_jpcoar_list.forEach(function (element) {
            options += '<option value="' + element + '">' + element + '</option>';
          });
          find_select_sub_jpcoar_list.append(options);
          new_sub_info.find('select[name="sub_jpcoar_list"]').val(key);
          if (page_global.sub_jpcoar_list.length == 1) {
            new_sub_info.find('select[name="sub_jpcoar_list"]').attr('disabled', true);
          }
        }
        new_sub_info.removeClass('sub_children_list hide').addClass('sub_child_list');
        new_sub_info.appendTo('#sub_children_lists');
        new_sub_info.find('select[name="sub_itemtype_list"]').change();
      }
    } else {
      let new_sub_info = $('div.sub_children_list').clone(true);
      if(page_global.sub_itemtype_list.length > 0) {
        new_sub_info.find('select[name="sub_itemtype_list"]').empty();
        let find_select_sub_itemtype_list = new_sub_info.find('select[name="sub_itemtype_list"]');
        let options = "";
        page_global.sub_itemtype_list.forEach(function(element){
          let display_name = element[1].length>0?element[1]:$('#sub-item-type-lists-label').text();
          options += '<option value="'+element[0]+'">'+display_name+'</option>';
        });
        find_select_sub_itemtype_list.append(options);
        if(page_global.sub_itemtype_list.length == 1) {
          new_sub_info.find('select[name="sub_itemtype_list"]').attr('disabled', true);
        }
      }
      if(page_global.sub_jpcoar_list.length > 0) {
        new_sub_info.find('select[name="sub_jpcoar_list"]').empty();
        let find_select_sub_jpcoar_list = new_sub_info.find('select[name="sub_jpcoar_list"]');
        let options = "";
        page_global.sub_jpcoar_list.forEach(function(element){
          options += '<option value="'+element+'">'+element+'</option>';
        });
        find_select_sub_jpcoar_list.append(options);
        if(page_global.sub_jpcoar_list.length == 1) {
          new_sub_info.find('select[name="sub_jpcoar_list"]').attr('disabled', true);
        }
      }
      new_sub_info.removeClass('sub_children_list hide').addClass('sub_child_list');
      new_sub_info.appendTo('#sub_children_lists');
      new_sub_info.find('select[name="sub_itemtype_list"]').change();
    }
  }
  function make_list_mapping(entries, jpcoar_key) {
    if(typeof entries == "string") {
      page_global.sub_mapping_list[jpcoar_key] = entries;
    } else if(typeof entries == "object") {
      for (let key in entries) {
        let value = entries[key];
        if (!key.startsWith('@')) {
          make_list_mapping(value, [jpcoar_key, key].join('.'));
        } else {
          if (key === '@value') {
            page_global.sub_mapping_list[jpcoar_key] = value;
          }
          if (key === '@attributes') {
            for (let attr_key in value) {
              let attr_value = value[attr_key];
              page_global.sub_mapping_list[[jpcoar_key, '@' + attr_key].join('.')] = attr_value;
            }
          }
        }
      }
    }
  }
  function make_list_itemtype(entries, base_key, base_title) {
    if(entries['type'] == 'object' && entries['properties']) {
      for (let key in entries['properties']) {
        let value = entries['properties'][key];
        if(!value['title']) {
          page_global.sub_itemtype_list.push([base_key, base_title.slice(1)]);
        } else {
          make_list_itemtype(value, [base_key, key].join('.'), [base_title, value['title']].join('.'));
        }
      }
    } else if(entries['type'] == 'array' && entries['items']['properties']) {
      for (let key in entries['items']['properties']) {
        let value = entries['items']['properties'][key];
        if(!value['title']) {
          page_global.sub_itemtype_list.push([base_key, base_title.slice(1)]);
        } else {
          make_list_itemtype(value, [base_key, key].join('.'), [base_title, value['title']].join('.'));
        }
      }
    } else {
      page_global.sub_itemtype_list.push([base_key, base_title.slice(1)]);
    }
    return;
  }
  function make_list_jpcoar(entries, base_key) {
    if(Object.keys(entries).length > 1) {
      for (let key in entries) {
        let value = entries[key];
        if('type' == key) {
          if(value.hasOwnProperty('attributes')) {
            make_list_jpcoar_prop(value.attributes, base_key);
          }
          continue;
        } else {
          make_list_jpcoar(value, [base_key, key].join('.'));
        }
      }
    } else {
      page_global.sub_jpcoar_list.push(base_key);
      if(entries.hasOwnProperty('type')) {
        if(entries.type.hasOwnProperty('attributes')) {
          make_list_jpcoar_prop(entries.type.attributes, base_key);
        }
      }
    }
    return;
  }

  function make_list_ddi(entries, base_key) {
    if(Object.keys(entries).length > 1) {
      for (let key in entries) {
        let value = entries[key];
        if('type' == key) {
          if(value.hasOwnProperty('attributes')) {
            make_list_ddi_prop(value.attributes, base_key);
          }
          continue;
        } else {
          make_list_ddi(value, [base_key, key].join('.'));
        }
      }
    } else {
      page_global.sub_jpcoar_list.push(base_key);
      if(entries.hasOwnProperty('type')) {
        if(entries.type.hasOwnProperty('attributes')) {
          make_list_ddi_prop(entries.type.attributes, base_key);
        }
      }
    }
    return;
  }

//    function make_list_jpcoar_level(entries, base_key) {
//      if(Object.keys(entries).length > 1) {
//        for(const [key, value] of Object.entries(entries)) {
//          if('type' == key) {
//            if(value.hasOwnProperty('attributes')) {
//              make_list_jpcoar_prop(value.attributes, base_key);
//            }
//            continue;
//          } else {
//            make_list_jpcoar_level(value, [base_key, key].join('.'));
//          }
//        }
//      } else {
//        page_global.sub_jpcoar_list.push(base_key);
//        if(entries.hasOwnProperty('type')) {
//          if(entries.type.hasOwnProperty('attributes')) {
//            make_list_jpcoar_prop(entries.type.attributes, base_key);
//          }
//        }
//      }
//      return;
//    }
  function make_list_jpcoar_prop(attr_list, base_key){
    attr_list.forEach(function (element) {
      page_global.sub_jpcoar_list.push([base_key, '@' + element.name].join('.'));
    });
  }

  function make_list_ddi_prop(attr_list, base_key){
    attr_list.forEach(function (element) {
      page_global.sub_jpcoar_list.push([base_key, '@'+element.name].join('.'));
    });

    let j = 0;
    let length_sub_jpcoar_list = page_global.sub_jpcoar_list.length;
    for(let i = 0; i < length_sub_jpcoar_list; i++){
      if(page_global.sub_jpcoar_list[i] === base_key){
        j++;
      }
    }

    if(j == 0){
      page_global.sub_jpcoar_list.push([base_key].join('.'));
    }
  }

  $('#sub_mapping-add').on('click', function(ev){
    page_global.showDiag = true;
    let new_sub_info = $('div.sub_children_list').clone(true);
    if(page_global.sub_itemtype_list.length > 0) {
      new_sub_info.find('select[name="sub_itemtype_list"]').empty();
      let find_select_sub_itemtype_list = new_sub_info.find('select[name="sub_itemtype_list"]');
      let options = "";
      page_global.sub_itemtype_list.forEach(function(element){
        let display_name = element[1].length>0?element[1]:$('#sub-item-type-lists-label').text();
        options += '<option value="'+element[0]+'">'+display_name+'</option>';
      });
      find_select_sub_itemtype_list.append(options);
    }
    if(page_global.sub_jpcoar_list.length > 0) {
        new_sub_info.find('select[name="sub_jpcoar_list"]').empty();
        let currentSubList = getCurrentSubJPCOARList();
        let isSelected = false;
        let find_select_sub_jpcoar_list = new_sub_info.find('select[name="sub_jpcoar_list"]');
        let options = "";
        page_global.sub_jpcoar_list.forEach(function(element){
          let isDisabled = false;
          let selected = "";
          currentSubList.forEach(function(selectedValue){
            if (element == selectedValue) {
              isDisabled = true;
              return;
            }
          });
          if (!isSelected && !isDisabled){
            selected = "selected";
            isSelected = true;
          }
          options += '<option ' + selected + ' value="'+element+'">'+element+'</option>';
        });
        find_select_sub_jpcoar_list.append(options);
      }
    new_sub_info.removeClass('sub_children_list hide').addClass('sub_child_list');
    new_sub_info.appendTo('#sub_children_lists');
    $('div.sub_child_list').find('fieldset').removeAttr('disabled');
    saveMappingData();
    disableSubSelectOption();
    disableSubAddButton();
  });

  $('#sub_mapping-add2').on('click', function(ev){
    page_global.showDiag = true;
    let new_sub_info = $('div.sub_children_list').clone(true);
    new_sub_info.find('input[type="text"]').removeClass('hide');
    new_sub_info.find('select[name="sub_itemtype_list"]').addClass('hide');
    if(page_global.sub_jpcoar_list.length > 0) {
        new_sub_info.find('select[name="sub_jpcoar_list"]').empty();
        let currentSubList = getCurrentSubJPCOARList();
        let isSelected = false;
        let find_select_sub_jpcoar_list = new_sub_info.find('select[name="sub_jpcoar_list"]');
        let options = "";
        page_global.sub_jpcoar_list.forEach(function(element){
          let isDisabled = false;
          let selected = "";
          currentSubList.forEach(function(selectedValue){
            if (element == selectedValue) {
              isDisabled = true;
              return;
            }
          });
          if (!isSelected && !isDisabled){
            selected = "selected";
            isSelected = true;
          }
          options += '<option ' + selected + ' value="'+element+'">'+element+'</option>';
        });
        find_select_sub_jpcoar_list.append(options);
      }
    new_sub_info.removeClass('sub_children_list hide').addClass('sub_child_list');
    new_sub_info.appendTo('#sub_children_lists');
    $('div.sub_child_list').find('fieldset').removeAttr('disabled');
    saveMappingData();
    disableSubSelectOption();
    disableSubAddButton();
  });

  $('select[name="sub_itemtype_list"], select[name="sub_jpcoar_list"]').on('change', function(ev){
    saveMappingData();
  });

  function saveMappingData(){
    if(page_global.mapping_prop == null) {
      mapping_str = $('#hide_mapping_prop').text();
      page_global.mapping_prop = JSON.parse(mapping_str);
    }
    let jpcoar_type = $("#jpcoar_lists").val(); 
    let itemtype_key = $('input[type="radio"]:checked').val(); 
    let jpcoar_parent_key = '';
    if(itemtype_key === undefined) return;
    page_global.showDiag = true; 
    ul_key = '#ul_' + itemtype_key;
    li_key = ul_key+' li.list_'+jpcoar_type;
    if($(li_key).length == 1) {
      if(page_global.mapping_prop.hasOwnProperty(itemtype_key)) {
        if(page_global.mapping_prop[itemtype_key].hasOwnProperty(jpcoar_type)) {
          page_global.mapping_prop[itemtype_key][jpcoar_type] = '';
        }
      }
    }
    sub_itemtype_list = [];
    $('div .sub_child_list').each(function (index, element) {
      sub_temp_itemtype = {
        sub_jpcoar: null,
        sub_itemtypes: null
      };
      sub_temp_itemtype.sub_jpcoar = $(element).find('select[name="sub_jpcoar_list"]').val();
      if($(element).find('.sub_child_itemtype_list').length > 1) {
        sub_temp_itemtype.sub_itemtypes = [];
        $(element).find('.sub_child_itemtype_list').each(function (idx, elm) { 
          sub_itemtype_key = {
            itemtype_key: null,
            itemlink_key: null
          };
          if(!$(elm).find('input[name="sub_itemtype_text"]').hasClass('hide')){
            sub_itemtype_key.itemtype_key = '=' + $(elm).find('input[name="sub_itemtype_text"]').val();
          }else{
            sub_itemtype_key.itemtype_key = $(elm).find('select[name="sub_itemtype_list"]').val();
          }
          sub_itemtype_key.itemlink_key = $(elm).find('.sub_itemtype_link input[type="text"]').val();
          sub_temp_itemtype.sub_itemtypes.push(sub_itemtype_key);
        });
      } else {
        if(!$(element).find('input[name="sub_itemtype_text"]').hasClass('hide')){
          sub_temp_itemtype.sub_itemtypes = '=' + $(element).find('input[name="sub_itemtype_text"]').val();
        }else{
          sub_temp_itemtype.sub_itemtypes = $(element).find('select[name="sub_itemtype_list"]').val();
        }
      }
      sub_itemtype_list.push(sub_temp_itemtype);
    });
    sub_itemtype_list.forEach(function (element) {
      if(element.sub_jpcoar && element.sub_jpcoar.length > 0) {
        let sub_itemtypes = element.sub_itemtypes;
        let sub_jpcoar = element.sub_jpcoar;
        let sub_jpcoar_arr = sub_jpcoar.split('.');
        jpcoar_parent_key = sub_jpcoar_arr[0];
        if(page_global.mapping_prop[itemtype_key] == "") {
          page_global.mapping_prop[itemtype_key] = {};
        }
        if(!page_global.mapping_prop.hasOwnProperty(itemtype_key)) {
          page_global.mapping_prop[itemtype_key] = {};
          page_global.mapping_prop[itemtype_key][jpcoar_type] = {};
        }
        if(!page_global.mapping_prop[itemtype_key].hasOwnProperty(jpcoar_type)) {
          page_global.mapping_prop[itemtype_key][jpcoar_type] = {};
        }
        cur_obj = page_global.mapping_prop[itemtype_key];
        if(typeof cur_obj[jpcoar_type] != 'object') {
          cur_obj[jpcoar_type] = {};
        }
        cur_obj = cur_obj[jpcoar_type];
        let length_sub_jpcoar_arr = sub_jpcoar_arr.length;
        for(let idx = 0; idx < length_sub_jpcoar_arr; idx++) {
          if(idx < length_sub_jpcoar_arr -1) {
            if(sub_jpcoar_arr[idx].startsWith('@')) {
              if(!cur_obj.hasOwnProperty('@attributes')) {
                cur_obj['@attributes'] = {};
              }
              cur_obj['@attributes'][sub_jpcoar_arr[idx].substr(1)] = {};
            } else {
              if(!cur_obj.hasOwnProperty(sub_jpcoar_arr[idx])) {
                cur_obj[sub_jpcoar_arr[idx]] = {};
              }
              if(!sub_jpcoar_arr[idx+1].startsWith('@')) {
                cur_obj = cur_obj[sub_jpcoar_arr[idx]];
              }
            }
          } else {
            sub_sub_itemtype = '';
            if(typeof sub_itemtypes == 'object') {
              if(sub_itemtypes.length > 0) {
                sub_itemtypes.forEach(function (elm)  {                  
                  if(!elm.itemtype_key.startsWith("=")){
                    if(elm.itemtype_key.indexOf('.') != -1){
                      let index = elm.itemtype_key.indexOf('.') + 1;
                      sub_sub_itemtype_e = elm.itemtype_key.slice(index) + elm.itemlink_key;
                    }else{
                    sub_sub_itemtype_e = elm.itemtype_key + elm.itemlink_key;
                    }
                  sub_sub_itemtype = sub_sub_itemtype + sub_sub_itemtype_e;
                }
                });
              }
            } else {
              // sub_sub_itemtype = sub_itemtypes.split('.').pop();
              if(!sub_itemtypes.startsWith("=") && sub_itemtypes.indexOf('.') != -1){
                let index = sub_itemtypes.indexOf('.') + 1;
                sub_sub_itemtype = sub_itemtypes.slice(index);
              }else{
                sub_sub_itemtype = sub_itemtypes;
              }
            }
            if(sub_jpcoar_arr[idx].startsWith('@')) {
              if(typeof cur_obj[sub_jpcoar_arr[idx-1]] == 'object') {
                if(!cur_obj[sub_jpcoar_arr[idx-1]].hasOwnProperty('@attributes')) {
                  cur_obj[sub_jpcoar_arr[idx-1]]['@attributes'] = {};
                }
                cur_obj[sub_jpcoar_arr[idx-1]]['@attributes'][sub_jpcoar_arr[idx].substr(1)] = sub_sub_itemtype;
              } else {
                let temp_str = cur_obj[sub_jpcoar_arr[idx-1]];
                cur_obj[sub_jpcoar_arr[idx-1]] = {
                  '@attributes': {
                  }
                };
                cur_obj[sub_jpcoar_arr[idx-1]]['@attributes'][sub_jpcoar_arr[idx].substr(1)] = sub_sub_itemtype;
                if(temp_str.length > 0) {
                  cur_obj[sub_jpcoar_arr[idx-1]]['@value'] = temp_str;
                }
              }
            } else {
              if(typeof cur_obj[sub_jpcoar_arr[idx]] == 'object') {
                if(sub_sub_itemtype.length > 0 && sub_sub_itemtype != itemtype_key) {
                  cur_obj[sub_jpcoar_arr[idx]]['@value'] = sub_sub_itemtype;
                } else {
                  if(cur_obj[sub_jpcoar_arr[idx]].hasOwnProperty('@value')) {
                    delete cur_obj[sub_jpcoar_arr[idx]]['@value'];
                  }else{
                    cur_obj[sub_jpcoar_arr[idx]]['@value']='interim';
                  }
                }
              } else {
                if(sub_sub_itemtype.length > 0 && sub_sub_itemtype != itemtype_key) {
                  cur_obj[sub_jpcoar_arr[idx]] = {'@value':sub_sub_itemtype};
                } else {
                  cur_obj[sub_jpcoar_arr[idx]] = {'@value': 'interim'};
                }
              }
            }
          }
        }
      }
    });
    $('#preview_mapping').text(JSON.stringify(page_global.mapping_prop, null, 4));
  }

  $('#mapping-submit').on('click', function(){
    let error_flag = false;
    $('.sub_child_itemtype_list').each(function () {
      let warning_elm  = $(this).find('.sub_itemtype_text_warning');
      if(!warning_elm.hasClass('hide')){
        warning_elm.addClass('hide');
      }
      let sub_itemtype_text_elm = $(this).find('input[name="sub_itemtype_text"]') ; 
      if(!sub_itemtype_text_elm.hasClass('hide') && sub_itemtype_text_elm.val().length == 0) {
        warning_elm.removeClass('hide');
        sub_itemtype_text_elm.focus();
        error_flag = true ;
      }
    }
    ) 
    saveMappingData();
    if (error_flag){
      return;
    }
    var data = {
      item_type_id: parseInt($('#item-type-lists').val()),
      mapping: page_global.mapping_prop,
      mapping_type: $('#jpcoar_lists').val()
    };
    send('/admin/itemtypes/mapping', data);
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
        page_global.showDiag = false;
        $('html,body').scrollTop(0);
        if ("duplicate" in data) {
          addError(data.msg, data.err_items);
        } else {
          addAlert(data.msg);
        }
        //$('.modal-body').text(data.msg);
        //$('#myModal').modal('show');
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
      url: '/admin/itemtypes/mapping/schema/jpcoar_mapping',
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
  var previous;
  $('select[name="sub_jpcoar_list"]').on('focus', function () {
    // Store the current value on focus and on change
    previous = this.value;
  }).on('change', function (ev) {
    enableSelectOption(previous);
    disableSubSelectOption();
    previous = this.value;
  });

  function enableSelectOption(value) {
    $('select[name="sub_jpcoar_list"] option').each(function () {
      if (this.value == value) {
        $(this).prop("disabled", false);
      }
    });
  }

  function getCurrentSubJPCOARList() {
    let currentList = [];
    $('select[name="sub_jpcoar_list"]').each(function () {
      if (currentList.indexOf(this.value) < 0) {
        currentList.push(this.value);
      }
    });
    return currentList;
  }

  function disableSubSelectOption() {
    let currentSubList = getCurrentSubJPCOARList();
    $('select[name="sub_jpcoar_list"]').each(function () {
      let currentValue = this.value;
      $('option', this).each(function () {
        let optionValue = $(this).val();
        let currentOption = $(this);
        if (currentValue != optionValue) {
          currentSubList.forEach(function (selectedValue) {
            if (optionValue == selectedValue) {
              currentOption.prop("disabled", true);
              return;
            }
          });
        }// End if currentValue
      }); // End Option each
    }); // End sub_jpcoar_list each
  }

  function disableSubAddButton() {
    if(page_global.sub_jpcoar_list.length > 0) {
      let selectSize = $("select[name='sub_jpcoar_list']").size() - 1;
      if (selectSize >= page_global.sub_jpcoar_list.length){
        $("#sub_mapping-add").prop("disabled", true);
        $("#sub_mapping-add2").prop("disabled", true);
      } else {
        $("#sub_mapping-add").prop("disabled", false);
        $("#sub_mapping-add2").prop("disabled", false);
      }
    } else {
      $("#sub_mapping-add").prop("disabled", true);
      $("#sub_mapping-add2").prop("disabled", true);    
    }
  }
});
