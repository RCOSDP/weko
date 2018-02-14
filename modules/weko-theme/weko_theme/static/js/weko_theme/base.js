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
});
