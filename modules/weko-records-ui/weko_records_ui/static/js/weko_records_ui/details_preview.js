$(document).ready(function () {
  $('.weko-collapse').click(
    function(e) {
      /*e.preventDefault();*/
      e.stopPropagation();
      e.stopImmediatePropagation();
      var targetId = $(this).attr('data-target');
      var elementClass = $(this).attr('class');
      console.log('Triggered ' + targetId);
      if(elementClass.indexOf('weko-collapsed') !== -1) {
        $(targetId).collapse('show');
        $(this).removeClass('weko-collapsed');
      }
      else {
        $(targetId).collapse('hide');
        $(this).addClass('weko-collapsed');

      }
  });
});
