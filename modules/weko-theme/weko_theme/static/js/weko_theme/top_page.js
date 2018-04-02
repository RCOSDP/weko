require([
  "jquery",
  ], function() {
    $('body').on('load', function(event, data) {

    });

    $(document).ready(function() {
      //入力あったら、入力値入って展開したまま
      function ArrangeSearch(){
        var btn = sessionStorage.getItem('btn', '');
        if (btn !== null && btn !== ''){
          if (btn == 'detail-search'){
            $('#search_detail_metadata :input:not(:checkbox), #q').each(function(){
              if ($(this).attr('id') in sessionStorage){
                var input = sessionStorage.getItem($(this).attr('id'), '');
                if (input !== null && input !== ''){
                  $(this).val(input);
                  if (!$('#search_detail').hasClass('expanded')){
                    $('#top-search-btn').addClass('hidden');
                    $('#search_simple').removeClass('input-group');
                    $('#search_detail_metadata').collapse('show');
                  }else{
                    $('#search_detail_metadata').collapse('hide');
                  }
                }
              }
            });
          }else{
            if (btn == 'simple-search'){
              if ($('#q').attr('id') in sessionStorage){
                var input = sessionStorage.getItem($('#q').attr('id'), '');
                if (input !== null && input !== ''){
                  $('#search_detail_metadata').collapse('hide');
                  $('#q').val(input);
                }
              }
            }
          }
        }
      }

      ArrangeSearch();

      //簡易検索ボタン
      $('#top-search-btn').on('click', function(){
        sessionStorage.setItem('btn', 'simple-search');
        if ($('#q').val() !== ''){
          sessionStorage.setItem($('#q').attr('id'), $('#q').val());
        }else{
          sessionStorage.removeItem($('#q').attr('id'));
        }
        $('#search_detail_metadata :input:not(:checkbox)').each(function(){
          $(this).val('');
          sessionStorage.removeItem($(this).attr('id'));
//            sessionStorage.setItem($(this).attr('id'), '');
        })
      });

      //詳細検索の表示と隠すボタン
      $('#detail_search_main').on('click', function(){
        $('#top-search-btn').toggleClass('hidden','show');
        $('#search_simple').toggleClass('input-group');
        $('#search_detail_metadata').collapse('show');
        $('#search_detail').addClass('expanded');
        var isExpanded = !$('#search_detail').hasClass('expanded');
        $('#search_detail').toggleClass('expanded', isExpanded);
        if (!isExpanded) {
          $('#search_detail_metadata').collapse('hide');
        }
      });

      //詳細検索ボタン：入力値をseesionStorageに保存する
      $('#detail-search-btn').on('click', function(){
        sessionStorage.setItem('btn', 'detail-search');
        $('#search_detail_metadata :input:not(:checkbox), #q').each(function(){
          if ($(this).val() !== ''){
            sessionStorage.setItem($(this).attr('id'), $(this).val());
          }else{
            sessionStorage.removeItem($(this).attr('id'));
          }
        })
      });

       //クリアボタン：入力内容を削除
      $('#clear-search-btn').on('click', function(){
        $('#search_detail_metadata :input:not(:checkbox)').each(function(){
          $(this).val('');
          sessionStorage.removeItem($(this).attr('id'));
//            sessionStorage.setItem($(this).attr('id'), '');
        })
      });

      //ラジオボタン
      $('#search_type_fulltext search_type_keyword').on('click', function(){
        $(this).prop('checked', true);
      });

    });
});
