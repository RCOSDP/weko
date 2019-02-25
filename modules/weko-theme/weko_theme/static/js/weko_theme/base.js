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

      // Chunk Design
      alert($('#grid-info').html());
//      alert($('#grid-info').innerHTML);
//      alert($('#grid-body-left').innerHTML);
//      alert($('#grid-body-right').innerHTML);



    });
});
