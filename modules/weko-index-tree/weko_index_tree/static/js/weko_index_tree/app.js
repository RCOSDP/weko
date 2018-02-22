require([
  "jquery",
  "bootstrap"
  ], function() {
  $('#myModal').modal({
    show: false
  })

  page_global = {
    cur_index_id: 0,
    access_role_name: [0,1,2,3,5,6],
    exclusive_access_role_name: [4],
    acl_role_name: [0,1,2,3,4,5,6],
    exclusive_acl_role_name: [],
    access_group_name: [],
    exclusive_access_group_name: [9],
    acl_group_name: [9],
    exclusive_acl_group_name: [],
    exclusive_acl_room_auth: [],
    exclusive_tree_room_auth: [2,3]

  }
  page_default = {
    role_name_list : {0:'システム管理者',1:'主担',2:'モデレータ',3:'一般',4:'ゲスト',5:'事務局',6:'管理者'},
    access_role_name: [0,1,2,3,5,6],
    exclusive_access_role_name: [4],
    acl_role_name: [0,1,2,3,4,5,6],
    exclusive_acl_role_name: [],
    group_name_list : {9:'非会員'},
    access_group_name: [],
    exclusive_access_group_name: [9],
    acl_group_name: [9],
    exclusive_acl_group_name: [],
    exclusive_acl_room_auth: [],
    exclusive_tree_room_auth: [2,3]
  }

  $('input[name="access_room_auth"]').on('change', function(){
    let element_id = this.id;
    if($('#'+element_id).is(':checked')) {
      if($.inArray(parseInt(this.value), page_global.exclusive_tree_room_auth) != -1) {
        page_global.exclusive_tree_room_auth.splice(
          $.inArray(parseInt(this.value), page_global.exclusive_tree_room_auth), 1);
      }
    } else {
      if($.inArray(parseInt(this.value), page_global.exclusive_tree_room_auth) == -1) {
        page_global.exclusive_tree_room_auth.push(parseInt(this.value));
      }
    }
  });
  $('input[name="acl_room_auth"]').on('change', function(){
    let element_id = this.id;
    if($('#'+element_id).is(':checked')) {
      if($.inArray(parseInt(this.value), page_global.exclusive_acl_room_auth) != -1) {
        page_global.exclusive_acl_room_auth.splice(
          $.inArray(parseInt(this.value), page_global.exclusive_acl_room_auth), 1);
      }
    } else {
      if($.inArray(parseInt(this.value), page_global.exclusive_acl_room_auth) == -1) {
        page_global.exclusive_acl_room_auth.push(parseInt(this.value));
      }
    }
  });

  $('#btn_up_acl_group').on('click', function(){
    let select_val = $('#exclusive_acl_group_name').val();
    if(select_val === null) return;
    move_list(select_val, page_global.exclusive_acl_group_name, page_global.acl_group_name);
    initMulselect('acl_group_name');
  })
  $('#btn_down_acl_group').on('click', function(){
    let select_val = $('#acl_group_name').val();
    if(select_val === null) return;
    move_list(select_val, page_global.acl_group_name, page_global.exclusive_acl_group_name);
    initMulselect('acl_group_name');
  })
  $('#btn_up_access_group').on('click', function(){
    let select_val = $('#exclusive_access_group_name').val();
    if(select_val === null) return;
    move_list(select_val, page_global.exclusive_access_group_name, page_global.access_group_name);
    initMulselect('access_group_name');
  })
  $('#btn_down_access_group').on('click', function(){
    let select_val = $('#access_group_name').val();
    if(select_val === null) return;
    move_list(select_val, page_global.access_group_name, page_global.exclusive_access_group_name);
    initMulselect('access_group_name');
  })

  $('#btn_up_acl_role').on('click', function(){
    let select_val = $('#exclusive_acl_role_name').val();
    if(select_val === null) return;
    move_list(select_val, page_global.exclusive_acl_role_name, page_global.acl_role_name);
    initMulselect('acl_role_name');
  })
  $('#btn_down_acl_role').on('click', function(){
    let select_val = $('#acl_role_name').val();
    if(select_val === null) return;
    move_list(select_val, page_global.acl_role_name, page_global.exclusive_acl_role_name);
    initMulselect('acl_role_name');
  })
  $('#btn_up_access_role').on('click', function(){
    let select_val = $('#exclusive_access_role_name').val();
    if(select_val === null) return;
    move_list(select_val, page_global.exclusive_access_role_name, page_global.access_role_name);
    initMulselect('access_role_name');
  })
  $('#btn_down_access_role').on('click', function(){
    let select_val = $('#access_role_name').val();
    if(select_val === null) return;
    move_list(select_val, page_global.access_role_name, page_global.exclusive_access_role_name);
    initMulselect('access_role_name');
  })
  function move_list(select_vals, list_from, list_to) {
    select_vals.splice(',').forEach(function(key){
      list_to.push(
        list_from.splice($.inArray(parseInt(key),list_from), 1));
    });
    list_to.sort();
  }
  function initMulselect(compont_name) {
    if('access_role_name' == compont_name) {
      $('#access_role_name').empty();
      page_global.access_role_name.forEach(function(key){
        $('#access_role_name').append('<option value="'+key+'">'+page_default.role_name_list[key]+'</option>');
      });
      $('#exclusive_access_role_name').empty();
      page_global.exclusive_access_role_name.forEach(function(key){
        $('#exclusive_access_role_name').append('<option value="'+key+'">'+page_default.role_name_list[key]+'</option>');
      });
    }
    if('acl_role_name' == compont_name) {
      $('#acl_role_name').empty();
      page_global.acl_role_name.forEach(function(key){
        if(0 == key || 6 == key) {
          $('#acl_role_name').append('<option value="'+key+'" disabled>'+page_default.role_name_list[key]+'</option>');
        } else {
          $('#acl_role_name').append('<option value="'+key+'">'+page_default.role_name_list[key]+'</option>');
        }
      });
      $('#exclusive_acl_role_name').empty();
      page_global.exclusive_acl_role_name.forEach(function(key){
        $('#exclusive_acl_role_name').append('<option value="'+key+'">'+page_default.role_name_list[key]+'</option>');
      });
    }
    if('access_group_name' == compont_name) {
      $('#access_group_name').empty();
      page_global.access_group_name.forEach(function(key){
        $('#access_group_name').append('<option value="'+key+'">'+page_default.group_name_list[key]+'</option>');
      });
      $('#exclusive_access_group_name').empty();
      page_global.exclusive_access_group_name.forEach(function(key){
        $('#exclusive_access_group_name').append('<option value="'+key+'">'+page_default.group_name_list[key]+'</option>');
      });
    }
    if('acl_group_name' == compont_name) {
      $('#acl_group_name').empty();
      page_global.acl_group_name.forEach(function(key){
        $('#acl_group_name').append('<option value="'+key+'">'+page_default.group_name_list[key]+'</option>');
      });
      $('#exclusive_acl_group_name').empty();
      page_global.exclusive_acl_group_name.forEach(function(key){
        $('#exclusive_acl_group_name').append('<option value="'+key+'">'+page_default.group_name_list[key]+'</option>');
      });
    }
  }

  $('#publish_repos').on('change', function(){
    if($('#publish_repos').is(':checked')) {
      $('#publish_date').removeClass("hide");
    } else {
      $('#publish_date').addClass("hide");
    }
  });

  $('input[name="select_index_list_display"]').on('click', function(){
    if($(this).val() == '1') {
      $('#select_index_list_display').prop('disabled', false);
    } else {
      $('#select_index_list_display').prop('disabled', true);
    }
  });

  $('#index-tree-submit').on('click', function(){
    var data = {
      index_tree: $('#index-tree').val()
    };
    send('/indextree/edit', data,
      function(data){
        refreshIndexTree();
        $('.modal-body').text(data.msg);
        $('#myModal').modal('show');
      },
      function(errmsg){
        $('.modal-body').text('Error: ' + errmsg);
        $('#myModal').modal('show');
      }
    );
  });

  $('#index-detail-submit').on('click', function(){
    var data = {
      index_name: $('#inputTitle_ja').val(),
      index_name_english: $('#inputTitle_en').val(),
      comment: $('#inputComment').val(),
      public_state: $('#publish_repos').is(':checked'),
      recursive_public_state: $('#pubdate_recursive').is(':checked'),
      rss_display: $('#rss_display').is(':checked'),
      create_cover_flag: $('#create_cover_flag').is(':checked'),
      create_cover_recursive: $('#create_cover_recursive').is(':checked'),
      harvest_public_state: $('#harvest_public_state').is(':checked'),
      online_issn: $('#online_issn').val(),
      biblio_flag: $('#biblio_flag').is(':checked'),
      display_type: $('input[name="display_type"]:checked').val(),
      select_index_list_display: $('input[name="select_index_list_display"]:checked').val()==1?true:false,
      select_index_list_name: $('#select_index_list_name_ja').val(),
      select_index_list_name_english: $('#select_index_list_name_en').val(),
      exclusive_acl_role: page_global.exclusive_acl_role_name.toString(),
      acl_role: page_global.acl_role_name.toString(),
      exclusive_acl_room_auth: page_global.exclusive_acl_room_auth.toString(),
      exclusive_acl_group: page_global.exclusive_acl_group_name.toString(),
      acl_group: page_global.acl_group_name.toString(),
      exclusive_access_role: page_global.exclusive_access_role_name.toString(),
      access_role: page_global.access_role_name.toString(),
      aclRoleIds_recursive: $('#aclRoleIds_recursive').is(':checked'),
      exclusive_tree_room_auth: page_global.exclusive_tree_room_auth.toString(),
      aclRoomAuth_recursive: $('#aclRoomAuth_recursive').is(':checked'),
      exclusive_access_group: page_global.exclusive_access_group_name.toString(),
      access_group: page_global.access_group_name.toString(),
      aclGroupIds_recursive: $('#aclGroupIds_recursive').is(':checked'),
      opensearch_uri: $('#opensearch_uri').val()
    }
    if($('#publish_repos').is(':checked')) {
      data.public_date = $('#publish_date').val();
    }
    //$('#attachment_form').submit();
    send('/indextree/detail/'+page_global.cur_index_id, data,
      function(data){
        $('.modal-body').text('Success');
        $('#myModal').modal('show');
      },
      function(errmsg){
        $('.modal-body').text('Error: ' + errmsg);
        $('#myModal').modal('show');
      });
  });

  function send(url, data, handleSuccess, handleError){
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

  function getItemsByIndex(node) {
    page_global.cur_index_id = node.id;
    $.get('/indextree/detail/'+page_global.cur_index_id, function(data, status){
      if(data.mod_user_id > 0) {
        $('#inputTitle_ja').val(data.index_name);
        $('#inputTitle_en').val(data.index_name_english);
      } else {
        $('#inputTitle_ja').val(node.title);
        $('#inputTitle_en').val('');
      }
      $('#inputComment').val(data.comment);
      $('#publish_repos').prop('checked', data.public_state);
      $('#pubdate_recursive').prop('checked', data.recursive_public_state);
      if(data.public_state) {
        let pub_date = new Date(data.public_date);
        $('#publish_date').removeClass("hide");
        $('#publish_date').val(pub_date.getFullYear()
                           +'-'+(pub_date.getMonth()>8?'':'0')+(pub_date.getMonth()+1)
                           +'-'+(pub_date.getDate()>9?'':'0')+pub_date.getDate());
      } else {
        $('#publish_date').addClass("hide");
        $('#publish_date').val('');
      }
      $('#rss_display').prop('checked', data.rss_display);
      $('#create_cover_flag').prop('checked', data.create_cover_flag);
      $('#create_cover_recursive').prop('checked', data.create_cover_recursive);
      $('#harvest_public_state').prop('checked', data.harvest_public_state);
      $('#online_issn').val(data.online_issn);
      $('#biblio_flag').prop('checked', data.biblio_flag);
      if(0 == data.display_type) {
        $('#display_type_0').prop('checked', true);
        $('#display_type_1').prop('checked', false);
      } else {
        $('#display_type_1').prop('checked', true);
        $('#display_type_0').prop('checked', false);
      }
      if(data.select_index_list_display) {
        $('#select_index_list_display_0').prop('checked', true);
        $('#select_index_list_display_1').prop('checked', false);
        $('#select_index_list_display').prop('disabled', false);
        $('#select_index_list_name_ja').val(data.select_index_list_name);
        $('#select_index_list_name_en').val(data.select_index_list_name_english);
      } else {
        $('#select_index_list_display_0').prop('checked', false);
        $('#select_index_list_display_1').prop('checked', true);
        $('#select_index_list_display').prop('disabled', true);
        $('#select_index_list_name_ja').val('');
        $('#select_index_list_name_en').val('');
      }
      if(data.mod_user_id > 0) {
        page_global.exclusive_acl_role_name = data.exclusive_acl_role.length>0?data.exclusive_acl_role.split(','):[];
        page_global.acl_role_name = data.acl_role.length>0?data.acl_role.split(','):[];
      } else {
        page_global.exclusive_acl_role_name = page_default.exclusive_acl_role_name;
        page_global.acl_role_name = page_default.acl_role_name;
      }
      if(data.mod_user_id > 0) {
        page_global.exclusive_acl_group_name = data.exclusive_acl_group.length>0?data.exclusive_acl_group.split(','):[];
        page_global.acl_group_name = data.acl_group.length>0?data.acl_group.split(','):[];
      } else {
        page_global.exclusive_acl_group_name = page_default.exclusive_acl_group_name;
        page_global.acl_group_name = page_default.acl_group_name;
      }
      if(data.mod_user_id > 0) {
        page_global.exclusive_access_role_name = data.exclusive_access_role.length>0?data.exclusive_access_role.split(','):[];
        page_global.access_role_name = data.access_role.length>0?data.access_role.split(','):[];
      } else {
        page_global.exclusive_access_role_name = page_default.exclusive_access_role_name;
        page_global.access_role_name = page_default.access_role_name;
      }
      if(data.mod_user_id > 0) {
        page_global.exclusive_access_group_name = data.exclusive_access_group.length>0?data.exclusive_access_group.split(','):[];
        page_global.access_group_name = data.access_group.length>0?data.access_group.split(','):[];
      } else {
        page_global.exclusive_access_group_name = page_default.exclusive_access_group_name;
        page_global.access_group_name = page_default.access_group_name;
      }
      initMulselect('access_role_name');
      initMulselect('acl_role_name');
      initMulselect('access_group_name');
      initMulselect('acl_group_name');
      if(data.exclusive_acl_room_auth.length > 0) {
        page_global.exclusive_acl_room_auth = data.exclusive_acl_room_auth.split(',');
      } else {
        page_global.exclusive_acl_room_auth = page_default.exclusive_acl_room_auth;
      }
      if(data.exclusive_tree_room_auth.length > 0) {
        page_global.exclusive_tree_room_auth = data.exclusive_tree_room_auth.split(',');
      } else {
        page_global.exclusive_tree_room_auth = page_default.exclusive_tree_room_auth;
      }
      $('input[name="acl_room_auth"]').prop('checked', true);
      $('input[name="access_room_auth"]').prop('checked', true);
      page_global.exclusive_acl_room_auth.forEach(function(element){
        $('#acl_room_auth'+element).prop('checked', false);
      });
      page_global.exclusive_tree_room_auth.forEach(function(element){
        $('#access_room_auth'+element).prop('checked', false);
      });
      $('#aclRoleIds_recursive').prop('checked', data.aclRoleIds_recursive);
      $('#aclRoomAuth_recursive').prop('checked', data.aclRoomAuth_recursive);
      $('#aclGroupIds_recursive').prop('checked', data.aclGroupIds_recursive);
      if(data.thumbnail_mime_type.length > 0) {
        $('#thumbnail_upload').addClass('hide');
        $('#thumbnail_edit').removeClass('hide');
      } else {
        $('#thumbnail_upload').removeClass('hide');
        $('#thumbnail_edit').addClass('hide');
      }
      $('#attachment_form').prop('action', '/indextree/thumbnail/'+page_global.cur_index_id);
      $('#thumbnail_img').prop('src', '/indextree/thumbnail/'+page_global.cur_index_id);
    });
  }

  function refreshIndexTree() {
    $.get('/indextree/jsonmapping', function(data, status){
      if(data.length <= 0) return;
      getItemsByIndex(data[0]);
      var element = document.getElementById('index_tree');
      var editor = new JSONTreeView(element, {
          data: data,
          onClick: function(node){
            getItemsByIndex(node);
          }
      });
    });
  }

  refreshIndexTree();
});
