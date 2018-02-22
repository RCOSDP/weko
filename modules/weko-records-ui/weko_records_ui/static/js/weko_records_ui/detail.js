require([
  "jquery",
  "bootstrap"
  ], function() {
    $('#btn_back').on('click', function(){
      window.history.back();
    });
  }
});
