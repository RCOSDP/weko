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
      $('.tb-todo').addClass('hide');
      $('.tb-wait').addClass('hide');
      $('.tb-all').addClass('hide');
      $('.tb-'+tab_name).each(function(index){
        $(this).removeClass('hide');
        $(this).children(':first-child').text(index+1);
      });
    });
});
