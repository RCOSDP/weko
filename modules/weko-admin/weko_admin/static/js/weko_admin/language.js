
$(document).ready(function () {

  const urlLoad = '/api/admin/load_lang';
  const urlUpdate = '/api/admin/save_lang';

  // $.ajax({
  //   url: url,
  //   type: 'POST',
  //   contentType:'application/json',
  //   data: JSON.stringify(data),
  //   dataType:'json'
  // });

  // $.ajax({
  //   url: url,
  //   type: 'GET',
  //   contentType:'application/json',
  //   data: JSON.stringify(data),
  //   dataType:'json'
  // });

  const results = [
    {
      lang_code: "eng",
      lang_name: "English",
      is_registered: true,
      sequence: 0,
    },
    {
      lang_code: "vie",
      lang_name: "Vietnamese",
      is_registered: false,
      sequence: 0,
    },
    {
      lang_code: "jpn",
      lang_name: "Japanese",
      is_registered: false,
      sequence: 0,
    }
  ]

  let leftOption = '';
  let rightOption = '';

  for (let index = 0; index < results.length; index++) {
    const element = results[index];
    if (element.is_registered) {
      rightOption += `<option value="${element.lang_code}">${element.lang_name}</option>`;
      continue;
    }
    leftOption += `<option value="${element.lang_code}">${element.lang_name}</option>`;
  }
  $('#leftSelect').append(leftOption);
  $('#rightSelect').append(rightOption);


  $.ajax({
    url: urlLoad,
    type: 'GET',
    success: function (data) {

    }
  });

  $('#moveRight').on('click', function () {
    $('#leftSelect').find('option:selected').detach().prop("selected", false).appendTo($('#rightSelect'));
  });

  $('#moveLeft').on('click', function () {
    $('#rightSelect').find('option:selected').detach().prop("selected", false).appendTo($('#leftSelect'));
  });

  $('#moveTop').on('click', function () {
    $('#rightSelect').find('option:selected').detach().prependTo($('#rightSelect'));
  });

  $('#moveUp').on('click', function () {
    $('#rightSelect').find('option:selected').each(function () {
      $(this).prev(':not(:selected)').detach().insertAfter($(this));
    });
  });

  $('#moveDown').on('click', function () {
    $($('#rightSelect').find('option:selected').get().reverse()).each(function () {
      $(this).next(':not(:selected)').detach().insertBefore($(this));
    });
  });

  $('#moveBottom').on('click', function () {
    $('#rightSelect').find('option:selected').detach().appendTo($('#rightSelect'));
  });

  $('#btn_commit_lg').on('click', function () {
    const children = $('#leftSelect').children();
    const selectedChildren = $('#rightSelect').children();
    const map = {};
    for (let ele of results) {
      map[ele.lang_code] = ele;
    }
    for (let index = 0; index < children.length; index++) {
      const element = map[children[index].value];
      element.is_registered = false;
      element.sequence = 0;
    }
    for (let index = 0; index < selectedChildren.length; index++) {
      const element = map[selectedChildren[index].value];
      element.is_registered = true;
      element.sequence = index;
    }

    $.ajax({
      url: urlUpdate,
      type: 'POST',
      contentType: 'application/json; charset=UTF-8',
      data: JSON.stringify(results),
      success: function (data) {
      }
    });
  });
});