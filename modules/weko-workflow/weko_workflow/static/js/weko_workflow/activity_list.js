require([
  "jquery",
  "bootstrap"
  ], function() {
    $('.tb-todo').removeClass('hide');
    $('.tb-todo').each(function(index){
      $(this).children(':first-child').text(index+1);
    });
    $('.activity_tab').on('click', function(){
      $('.activity_li').removeClass('active');
      $(this).parent().addClass('active');
      tab_name = $(this).data('show-tab');
      if('all' == tab_name) {
        $('.tb-all').removeClass('hide');
      } else {
        $('.tb-all').addClass('hide');
        $('.tb-'+tab_name).removeClass('hide');
      }
      $('.tb-'+tab_name).each(function(index){
        $(this).children(':first-child').text(index+1);
      });
    });
});
