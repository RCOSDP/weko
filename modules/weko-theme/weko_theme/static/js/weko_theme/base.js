require([
  "jquery",
  "bootstrap"
  ], function() {
    $(document).ready(function() {
      $('#btn_edit_start').on('click', function(){
        window.location.href = '/schema/list/';
      });
      $('#btn_edit_stop').on('click', function(){
        window.location.href = '/';
      });

      // Make the header and footer non-editable
      $('#header').find('.ql-editor').
        attr('contenteditable', 'false');
      $('#footer').find('.ql-editor').
        attr('contenteditable', 'false');

      // bind change event to select
      $("select[name='index_link']").on('change', function () {
        if ($(this).val()) {
          var url = '/search?search_type=2&q=' + $(this).val();
          window.location = url;
        }
      });

      adminHeight = $('#index-height').text();
      if(adminHeight != null && adminHeight != '') {
        $('.index-body').css('height',adminHeight);
      }
    });
});
