require([
  "jquery",
  "bootstrap",
  "typeahead.js",
  "bloodhound",
  "node_modules/angular/angular",

  // "node_modules/invenio-csl-js/dist/invenio-csl-js",
], function(typeahead, Bloodhound) {
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

  $('a#btn_edit').on('click', function () {
      let post_uri = "/api/items/prepare_edit_item";
      let pid_val = $(this).data('pid-value');
      let community = $(this).data('community');
      let post_data = {
          pid_value: pid_val
      };
      if(community){
        post_uri = post_uri+"?community="+ community;
      }
      $.ajax({
          url: post_uri,
          method: 'POST',
          async: true,
          contentType: 'application/json',
          data: JSON.stringify(post_data),
          success: function (res, status) {
              if (0 == res.code) {
                  let uri = res.data.redirect.replace('api/', '')
                  document.location.href = uri;
              } else {
                  alert(res.msg);
              }
          },
          error: function (jqXHE, status) {}
      });
  });
  angular.element(document).ready(function() {
    angular.bootstrap(document.getElementById("invenio-csl"), [
        'invenioCsl',
      ]
    );
  });

  $('a#btn_edit_disabled').tooltip();
});
