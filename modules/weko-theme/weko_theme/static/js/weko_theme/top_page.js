require([
  "jquery",
  ], function() {
    $(document).ready(function() {
        //add by ryuu. for redemine #3359 start
        //検索ボタンをクリックすると、画面の検索条件を表示するまま
        var url = window.location.href;
        if(url.indexOf('search_type') != -1 && url.indexOf('q=') != -1 ){
          var indexTo = url.indexOf('&search_type');
          var indexFrom = url.indexOf('q=');
          var searchKey = url.substring(indexFrom,indexTo).replace('q=','');
          $("#q").attr("value",searchKey)；
        }
        //add by ryuu. for redemine #3359 end
        //入力あったら、入力値入って展開したまま
        $('#search_detail_metadata :input:not(:checkbox)').each(function(){
          if ($(this).attr('id') in sessionStorage){
            var input = sessionStorage.getItem($(this).attr('id'), '');
            if (input !== null && input !== ''){
              $(this).val(input);
              $('#search_detail_metadata').collapse('show');
            }
          }
        })

        //詳細検索の表示と隠す
        $('#detail_search_main').on('click', function(){
          $('#search_detail_metadata').collapse('show');
          $('#search_detail').addClass('expanded');
          var isExpanded = !$('#search_detail').hasClass('expanded');
          $('#search_detail').toggleClass('expanded', isExpanded);
          if (!isExpanded) {
              $('#search_detail_metadata').collapse('hide');
          }
        });

        //入力値をseesionStorageに保存する
        $('#detail-search-btn').on('click', function(){
          $('#search_detail_metadata :input:not(:checkbox)').each(function(){
            sessionStorage.setItem($(this).attr('id'), $(this).val());
          })
        });

         //入力内容を削除
        $('#clear-search-btn').on('click', function(){
          $('#search_detail_metadata :input:not(:checkbox)').each(function(){
            $(this).val('');
            sessionStorage.setItem($(this).attr('id'), '');
          })
          $('#search_detail_metadata').collapse('hide');
        });

    });
});
