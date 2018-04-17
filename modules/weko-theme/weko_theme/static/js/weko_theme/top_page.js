require([
  "jquery",
  ], function() {
    $('body').on('load', function(event, data) {

    });

    //urlからパラメタ―の値を取得
    function GetUrlParam(sParam){
      var sURL = window.location.search.substring(1);
      var sURLVars = sURL.split('&');
      for (var i = 0; i< sURLVars.length; i++){
        var sParamArr = sURLVars[i].split('=');
        if (sParamArr[0] == sParam){
          return decodeURIComponent(sParamArr[1]);
        }
      }
      return false;
    }

    //urlからパラメタ―のキーを取得する
    function IsParamKey(sParam){
      var sURL = window.location.search.substring(1);
      var sURLVars = sURL.split('&');
      for (var i = 0; i< sURLVars.length; i++){
        var sParamArr = sURLVars[i].split('=');
        if (sParamArr[0] == sParam){
          return true;
        }
      }
      return false;
    }

    //サーチ入力の表示
    function ArrangeSearch(){
      var btn = sessionStorage.getItem('btn', false);
      var SearchType = GetUrlParam('search_type');
      var input = '';
      var IsRec = window.location.pathname.includes('records');

      $('#search_detail_metadata :input:not(:checkbox), #q, #search_type :input').each(function(){
        if (IsRec){
          input = sessionStorage.getItem($(this).attr('id'), '');
        }else{
          if (SearchType){
            if (IsParamKey($(this).attr('id'))){
              input = GetUrlParam($(this).attr('id'));
            }
          }else{
            sessionStorage.removeItem($(this).attr('id'));
          }
        }

        //詳細展開 値入力残
        if (btn){
          if (btn == 'detail-search'){
            if (IsParamKey($(this).attr('id')) || IsRec){
              if (input && input !== ''){
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
          }else{
            if (btn == 'simple-search'){
              input = sessionStorage.getItem('q', false);
              if (input){
                $('#search_detail_metadata').collapse('hide');
                $('#q').val(input);
              }
            }
          }
        }else{
          $('#search_type_fulltext').prop('checked', true);
        }
      });

      //サーチラジオボタンの位置
      if (SearchType){
        if (SearchType == '0'){
          $('#search_type_fulltext').prop('checked', true);
        }else{
          $('#search_type_keyword').prop('checked', true);
        }
      }else{
        if (IsRec){
          var search_type = sessionStorage.getItem('search_type', false)
          if (search_type && search_type == '1'){
            $('#search_type_keyword').prop('checked', true);
          }else{
            $('#search_type_fulltext').prop('checked', true);
          }
        }else{
          $('#search_type_fulltext').prop('checked', true);
          sessionStorage.removeItem('search_type');
        }
      }

    }

    //Url query コントロール
    function SearchSubmit(){
      if ($('#search_type_fulltext').prop('checked')){
        sessionStorage.setItem('search_type', '0');
      }else{
        sessionStorage.setItem('search_type', '1');
      }
      $('#search-form').submit(function(event){
        var query= '';
        $('#search_type :input:checked').each(function(){
          query += $(this).serialize() + '&';
        });
        query += $('#q').serialize().replace(/\+/g,'%20') + '&';
        var btn = sessionStorage.getItem('btn', '');
        if (btn == 'detail-search'){
          $('#search_detail_metadata :input:not(:checkbox)').each(function(){
            if ($(this).val() !== ''){
              query += $(this).serialize().replace(/\+/g,'%20') + '&';
            }
          });
        }
        window.location.href = ('/search?page=1&size=20&' + query).slice(0,-1);
        // stop the form from submitting the normal way and refreshing the page
        event.preventDefault();
      })
    }

    $(document).ready(function() {

      ArrangeSearch();

      //簡易検索ボタン
      $('#top-search-btn').on('click', function(){
        sessionStorage.setItem('btn', 'simple-search');
        SearchSubmit();
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
        SearchSubmit();
      });

       //クリアボタン：入力内容を削除
      $('#clear-search-btn').on('click', function(){
        $('#search_detail_metadata :input:not(:checkbox)').each(function(){
          $(this).val('');
        })
      });

      //アイテム検索結果 (search_ui/static/templates/itemlist.html)
      $('#search_detail_metadata :input:not(:checkbox), #q').on('change', function(){
        $('#search_detail_metadata :input:not(:checkbox), #q').each(function(){
          if ($(this).val() !== ''){
            sessionStorage.setItem($(this).attr('id'), $(this).val());
          }else{
            sessionStorage.removeItem($(this).attr('id'));
          }
        });
      });

//      #search_type :input[name="search_type"]

    });
});
