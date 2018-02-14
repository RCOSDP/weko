  require([
    "jquery",
    "bootstrap"
    ], function() {
    $('#myModal').modal({
      show: false
    })

    page_global = {
      cur_index_id: 0
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
        online_issn: $('#online_issn').val(),
        display_type: $('input[name="display_type"]:checked').val(),
        select_index_list_display: $('input[name="select_index_list_display"]:checked').val()==1?true:false,
        select_index_list_name: $('#select_index_list_name_ja').val(),
        select_index_list_name_english: $('#select_index_list_name_en').val()
      }
      if($('#publish_repos').is(':checked')) {
        data.public_date = $('#publish_date').val();
      }

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

    function getItemsByIndex(indexid) {
      page_global.cur_index_id = indexid;
      $.get('/indextree/detail/'+indexid, function(data, status){
        $('#inputTitle_ja').val(data.index_name);
        $('#inputTitle_en').val(data.index_name_english);
        $('#inputComment').val(data.comment);
        $('#publish_repos').prop('checked', data.public_state);
        $('#pubdate_recursive').prop('checked', data.recursive_public_state);
        if(data.public_state) {
          $('#publish_date').removeClass("hide");
          $('#publish_date').val(data.public_date);
        } else {
          $('#publish_date').addClass("hide");
          $('#publish_date').val('');
        }
        $('#rss_display').prop('checked', data.rss_display);
        $('#online_issn').val(data.online_issn);
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
      });
    }

    function refreshIndexTree() {
      $.get('/indextree/jsonmapping', function(data, status){
        var element = document.getElementById('index_tree');
        var editor = new JSONTreeView(element, {
            data: data,
            onClick: function(node){
              getItemsByIndex(node.id);
            }
        });
      });
    }
    refreshIndexTree();
});
