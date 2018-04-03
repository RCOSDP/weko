require([
  "jquery",
  ], function() {
    $('body').on('load', function(event, data) {

    });

    function GetUrlParam(sParam){
      var sPageURL = window.location.search.substring(1);
      var sURLVariables = sPageURL.split('&');
      for (var i = 0; i< sURLVariables.length; i++){
        var sParameterName = sURLVariables[i].split('=');
        if (sParameterName[0] == sParam){
          return sParameterName[1];
        }
      }
      return '0';
    }

    function ArrangeSearch(){
     //ラジオボタン
      var SearchType = GetUrlParam('search_type');
      if (SearchType == '0'){
        $('#search_type_fulltext').prop('checked', true);
      }else{
        $('#search_type_keyword').prop('checked', true);
      }
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

    //フォーム提出
    function SearchSubmit(){
      $('#search-form').submit(function(event){
        var que = ''
        var query = ''
        $('#search_detail_metadata :input:not(:checkbox), #q').each(function(){
          if ($(this).val() !== ''){
            query += $(this).serialize() + '&';
          }
        });
        window.location.href = ('search?page=1&size=20&' + query).slice(0,-1);
        // process the form
//        $.ajax({
//            type        : 'POST', // define the type of HTTP verb we want to use (POST for our form)
//            url         : '/search', // the url where we want to POST
//            data        : query, // our data object
////            dataType    : 'json', // what type of data do we expect back from the server
////                        encode          : true,
//            success     : function(data){
//              alert(data);
//            }
//        })
//            // using the done promise callback
//            .done(function(data) {
//              alert(data);
//              // log data to the console so we can see
//              console.log(data);
//              window.location.reload(true);
//              // here we will handle errors and validation messages
//            })
//            .fail(function(data){
//              alert("fail");
//              var myJSO = JSON.stringify(data);
//              alert(myJSO);
//              window.location.reload(true);
//            });

        // stop the form from submitting the normal way and refreshing the page
        event.preventDefault();
      })
    }

    $(document).ready(function() {
      //入力あったら、入力値入って展開したまま
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
        });
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
        $('#search_detail_metadata :input:not(:checkbox), #q').each(function(){
          if ($(this).val() !== ''){
            sessionStorage.setItem($(this).attr('id'), $(this).val());
          }else{
            sessionStorage.removeItem($(this).attr('id'));
          }
        })
        SearchSubmit();
      });

       //クリアボタン：入力内容を削除
      $('#clear-search-btn').on('click', function(){
        $('#search_detail_metadata :input:not(:checkbox)').each(function(){
          $(this).val('');
          sessionStorage.removeItem($(this).attr('id'));
//            sessionStorage.setItem($(this).attr('id'), '');
        })
      });

    });
});
