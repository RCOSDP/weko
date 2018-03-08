require([
  "jquery",
  "bootstrap"
  ], function() {
    $('#btn_edit_start').on('click', function(){
      window.location.href = '/itemtypes/';
    });
    $('#btn_edit_stop').on('click', function(){
      window.location.href = '/';
    });

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

});
