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
      itemtype_prop:null,
      schema_prop:{},
      jpcoar_prop:null,
      mapping_prop:null,
      sub_itemtype_list:[],
      sub_jpcoar_list:[],
      sub_mapping_list:{}
    }
    page_global.src_mapping_name = $('#item-type-lists').val();

    $("#item-type-lists").change(function (ev) {
      page_global.dst_mapping_name = $('#item-type-lists').val();
      $('.modal-title').text('提示');
      $('.modal-body').text('編集内容をキャンセルしてもよろしいですか？');
      $('#btn_submit').addClass('hide');
      $('#btn_confirm').removeClass('hide');
      $('#myModal').modal('show');
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
      if($('li.list_'+$(this).val()).find('input[type="radio"]:checked').length > 0) {
        $('li.list_'+$(this).val()).find('input[type="radio"]:checked').trigger('click');
      } else {
        let new_sub_info = $('div.sub_children_list').clone(true);
        new_sub_info.removeClass('sub_children_list hide').addClass('sub_child_list');
        new_sub_info.appendTo('#sub_children_lists');
      }
    });
    $('input[type="button"]').on('click', function(ev){
      action = this.dataset.action;
      if('add' == action) {
        ul_key = '#ul_' + this.parentElement.dataset.key;
        li_key = ul_key+' li.list_'+$('#jpcoar_lists').val()+':last';
        $(li_key).clone(true).appendTo(ul_key);
      }
      if('del' == action) {
        // mapping json info also need delete
        $(this).parents('.list-group-item').remove();
      }
      if('del_child' == action) {
        $(this).parents('.sub_child_list').remove();
        if($('div.sub_child_list').length == 1) {
          $('div.sub_child_list').find('fieldset').attr('disabled', true);
        }
      }
    });
    $('select[name="parent_list"]').on('change', function(ev){
      $(this).parent().find('input[type="radio"]').trigger('click');
    });
    $('input[type="radio"]').on('click', function(ev){
      $('tr').removeClass('active');
      $(this).parents('tr').addClass('active');
      item_type_key = $(this).val();
      jpcoar_key = $(this).parents('.form-inline').find('select').val();
      display_sub_lists(item_type_key, jpcoar_key);
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
      if(Object.keys(page_global.sub_mapping_list).length > 0) {
        Object.entries(page_global.sub_mapping_list).forEach(([key, value]) => {
          let new_sub_info = $('div.sub_children_list').clone(true);
          if(page_global.sub_itemtype_list.length > 0) {
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
          if(page_global.sub_jpcoar_list.length > 0) {
            new_sub_info.find('select[name="sub_jpcoar_list"]').empty();
            page_global.sub_jpcoar_list.forEach(function(element){
              new_sub_info.find('select[name="sub_jpcoar_list"]').append('<option value="'+element+'">'+element+'</option>');
            });
            new_sub_info.find('select[name="sub_jpcoar_list"]').val(key);
          }
          new_sub_info.removeClass('sub_children_list hide').addClass('sub_child_list');
          new_sub_info.appendTo('#sub_children_lists');
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
          make_list_mapping(value, [jpcoar_key, key].join('.'));
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
      sub_children_list = $('#sub_children_lists div.row:last').clone(true);
      sub_children_list.addClass('sub_child_list');
      sub_children_list.appendTo('#sub_children_lists');
      $('div.sub_child_list').find('fieldset').removeAttr('disabled');
    });
    $('#sub_mapping-create').on('click', function(ev){
      if(page_global.mapping_prop == null) {
        mapping_str = $('#hide_mapping_prop').text();
        page_global.mapping_prop = JSON.parse(mapping_str);
      }
      sub_itemtype_list = [];
      $('select[name="sub_itemtype_list"]').each(function(index){
        sub_itemtype_list.push([$(this).val(), '']);
      });
      $('select[name="sub_jpcoar_list"]').each(function(index){
        sub_itemtype_list[index][1] = $(this).val();
      });
      jpcoar_type = $("#jpcoar_lists").val();
      sub_itemtype_list.forEach(function(element){
        if(element[0].length > 0) {
          sub_itemtype = element[0];
          sub_jpcoar = element[1];
          sub_itemtype_arr = sub_itemtype.split('.');
          sub_jpcoar_arr = sub_jpcoar.split('.');
          sub_sub_itemtype = sub_itemtype_arr.length>1?sub_itemtype_arr.pop():'';
          if(!page_global.mapping_prop.hasOwnProperty(sub_itemtype_arr[0])) {
            page_global.mapping_prop[sub_itemtype_arr[0]] = {};
            page_global.mapping_prop[sub_itemtype_arr[0]][jpcoar_type] = {};
          }
          cur_obj = page_global.mapping_prop[sub_itemtype_arr[0]];
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
              cur_obj[sub_jpcoar_arr[idx]] = sub_sub_itemtype;
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
});
