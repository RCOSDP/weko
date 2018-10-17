require([
  "jquery",
  "bootstrap"
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
        if(sParam){
        }
      }
      return false;
    }

//    set dispaly of property area

    function setDisplay(){
//    if input show
      if($('#subject').val()!=""){
        $('#subject_scheme').removeClass('hidden');
      }else{
        $('#subject_scheme').addClass('hidden');
      }
//contents date
      if($('#filedate_from').val()!=""&&$('#filedate_to').val()!=""){
        $('#contents_property').removeClass('hidden');
      }else{
        $('#contents_property').addClass('hidden');
      }
//ID
      if($('#id').val()!=""){
        $('#id_attr').removeClass('hidden');
      }else{
        $('#id_attr').addClass('hidden');
      }
//rights
      if($('#rights_ANY').is(":checked")){
        $('#rights').removeClass('hidden');
      }else{
        $('#rights').val('');
        $('#rights').addClass('hidden');
      }
    }

    //サーチ入力の表示
    function ArrangeSearch(){
      var btn = sessionStorage.getItem('btn');
      var SearchType = GetUrlParam('search_type');
      var input = '';
      var IsRec = window.location.pathname.includes('records');

//      $('#search_detail_metadata :input:not(:checkbox), #q, #search_type :input').each(function(){
      $('#search_detail_metadata :input:not(:checkbox), #q, #search_type :input').each(function(){
        if (IsRec){
          input = sessionStorage.getItem($(this).attr('id'));
        }else{
          if (SearchType && SearchType != '2'){
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
                //type is text
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
//      type is checkbox radio
      $('#search_detail_metadata :input:not(:text)').each(function(){
        if (IsRec){
          input = sessionStorage.getItem($(this).attr('id'));
        }else{
          if (SearchType && SearchType != '2'){
            input = sessionStorage.getItem($(this).attr('id'));
          }else{
            sessionStorage.removeItem($(this).attr('id'));
          }
        }
        //詳細展開 値入力残
        if (btn){
          if (btn == 'detail-search'){
            if (true || IsRec){
              if (input && input !== ''){
                //type is checkbox
                $(this).attr('checked',true);
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
        if (SearchType == '0' || SearchType == '2'){
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
      setDisplay();
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
        if($('#community').val()){
          query += $('#community').serialize().replace(/\+/g,'%20') + '&';
        }
        var btn = sessionStorage.getItem('btn', '');
        if (btn == 'detail-search'){
          $('#search_detail_metadata :input:not(:checkbox)').each(function(){
            if ($(this).val() !== ''){
              query += $(this).serialize().replace(/\+/g,'%20') + '&';
            }
          });
          // 件名・分類取得
          var obj=document.getElementsByName('sbjscheme');
          var str = "";
          for(var data of obj){
            if(data.checked){
              str+= data.value + ",";
            }
          }
          if(str != ""){
            query += '&sbjscheme='+ str;
          }
          //
          var obj=document.getElementsByName('id_attr');
          var str_id_attr = "";
          for(var data of obj){
            if(data.checked){
              str_id_attr+= data.value + ",";
            }
          }
          if(str_id_attr != ""){
            query += '&id_attr='+ str_id_attr;
          }
          // itemType
          var obj=document.getElementsByName('itemtype');
          var str_ite = "";
          for(var data of obj){
            if(data.checked){
              str_ite+= data.value + ",";
            }
          }
          if(str_ite != ""){
            query += '&itemtype='+ str_ite;
          }
          //resource type
          var obj=document.getElementsByName('resourceType');
          var str_re = "";
          for(var data of obj){
            if(data.checked){
              str_re+= data.value + ",";
            }
          }
          if(str_re != ""){
            query += '&type='+ str_re;
          }
          //
          var obj=document.getElementsByName('lang');
          var str_lang = "";
          for(var data of obj){
            if(data.checked){
              str_lang+= data.value + ",";
            }
          }
          if(str_lang != ""){
            query += '&lang='+ str_lang;
          }

          var obj=document.getElementsByName('contents_property');
          var str_contents_property = "";
          for(var data of obj){
            if(data.checked){
              str_contents_property+= data.value + ",";
            }
          }
          if(str_contents_property != ""){
            query += '&fd_attr='+ str_contents_property;
          }

          var obj=document.getElementsByName('rights');
          var str_rights = "";
          for(var data of obj){
            if(data.checked){
              if(data.value =="ANY"){
                query = query.replace("&rights=ANY","");
              }
            }
          }
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
        setDisplay();
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
        $('#search_detail_metadata :input:not(:text)').each(function(){
          $(this).attr('checked',false);
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

      //アイテム検索結果 (search_ui/static/templates/itemlist.html)
      $('#search_detail_metadata :input:not(:text)').on('click', function(){
        $('#search_detail_metadata :input:not(:text)').each(function(){
          if ($(this).is(":checked")){
            sessionStorage.setItem($(this).attr('id'), $(this).val());
          }else{
            sessionStorage.removeItem($(this).attr('id'));
          }
        });
      });

      $('#clear-search-btn').on('click', function(){
        $('#search_detail_metadata :input:not(:checkbox)').each(function(){
          $(this).val('');
        })
        $('#search_detail_metadata :input:not(:text)').each(function(){
          $(this).attr('checked',false);
        })
      });
//
      $('#subject').on('change', function(){
        if($('#subject').val()!=""){
          $('#subject_scheme').removeClass('hidden');
        }else{
          $('#subject_scheme :input:not(:text)').each(function(){
           //type is checkbox
            $(this).attr('checked',false);
          });
          $('#subject_scheme').addClass('hidden');
        }
      });

      $('#filedate_from').on('blur', function(){
        if($('#filedate_from').val()!=""){
          $('#contents_property').removeClass('hidden');
        }else{
          $('#contents_property :input:not(:text)').each(function(){
           //type is checkbox
            $(this).attr('checked',false);
          });
          $('#contents_property').addClass('hidden');
        }
      });

       $('#id').on('change', function(){
        if($('#id').val()!=""){
          $('#id_attr').removeClass('hidden');
        }else{
          $('#id_attr :input:not(:text)').each(function(){
           //type is checkbox
            $(this).attr('checked',false);
          });
          $('#id_attr').addClass('hidden');
        }
      });
      $('#search_detail_metadata :input:radio').on('click', function(){
        if($('#rights_ANY').is(":checked")){
          $('#rights').removeClass('hidden');
        }else{
          $('#rights').val('');
          $('#rights').addClass('hidden');
        }
      });

    });
});
