require([
  'jquery',
  'bootstrap'
],function () {
  $("#item-type-lists").change(function (ev) {
    window.location.href = '/items/' + $(this).val();
  });
});
