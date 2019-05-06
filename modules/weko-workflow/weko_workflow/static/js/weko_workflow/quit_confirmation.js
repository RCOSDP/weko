require([
  "jquery",
  "bootstrap"
], function() {
  $("#btn_quit").click(function () {
    console.log('#btn_quit');
    $("#action_quit_confirmation").modal("show");
  });
  $('#btn_cancel').on('click', function(){
    console.log('#btn-cancel');
    if ($rootScope === undefined) {
      console.log('root undefined');
    } else {
      console.log('root defined');
    }
  });
});
