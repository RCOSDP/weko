require([
  'jquery',
],function () {
  $("#item-type-lists").change(function (ev) {
    window.location.href = '/items/' + $(this).val();
  });
});
