require.config({
  baseUrl: "/static/",
  paths: {
    jquery: "node_modules/jquery/jquery",
    bootstrap: "node_modules/bootstrap-sass/assets/javascripts/bootstrap",
    angular: "node_modules/angular/angular",
    typeahead: 'node_modules/typeahead.js/dist/typeahead.jquery',
    bloodhound: 'node_modules/typeahead.js/dist/bloodhound',
    clipboard: 'node_modules/clipboard/dist/clipboard',
  },
  shim: {
    angular: {
      exports: 'angular'
    },
    jquery: {
      exports: "$"
    },
    bootstrap: {
      deps: ["jquery"]
    },
    clipboard: {
      exports: "Clipboard"
    }
  }
});

require([
  "jquery",
  "bootstrap"
], function() {
  $('#btn_back').on('click', function(){
    window.history.back();
  });

  $('#public_status_btn').on('click', function(){
     var status = $(this).val();
     var data = {'public_status': status};
     var urlHref = window.location.href.split('/')
     const url = urlHref[0] + '//' + urlHref[2] + '/records/' + urlHref[4] + '/pubstatus'
     $.ajax({
       url: url,
       type: 'POST',
       contentType:'application/json',
       data: JSON.stringify(data),
       dataType:'json'
     });
    if (status == 'Public') {
      $(this).text('Change to Public');
      $(this).val('Private');
      $('#public_status').text('Private');
    } else {
      $(this).text('Change to Private');
      $(this).val('Public');
      $('#public_status ').text('Public');
    };
  });

});
