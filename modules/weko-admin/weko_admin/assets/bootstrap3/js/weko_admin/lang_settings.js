
$(document).ready(function () {

  const urlLoad = '/api/admin/load_lang';
  const urlUpdate = '/api/admin/save_lang';

  const moveRight = $('#moveRight');
  const moveLeft = $('#moveLeft')
  const moveTop = $('#moveTop')
  const moveUp = $('#moveUp')
  const moveDown = $('#moveDown')
  const moveBottom = $('#moveBottom')
  const saveBtn = $('#btn_commit_lg')
  const leftSelect = $('#leftSelect');
  const rightSelect = $('#rightSelect');

  moveTop.prop("disabled", true);
  moveUp.prop("disabled", true);
  moveDown.prop("disabled", true);
  moveBottom.prop("disabled", true);

  let results = []

  $.ajax({
    url: urlLoad,
    type: 'GET',
    success: function (data) {
      results = data.results;

      let leftOption = '';
      let rightOption = '';

      for (let index = 0; index < results.length; index++) {
        const element = results[index];
        if (element.is_registered) {
          rightOption += "<option value=" + element.lang_code + ">" + element.lang_name + "&nbsp;" + element.lang_code + "</option>";
          continue;
        }
        leftOption += "<option value=" + element.lang_code + ">" + element.lang_name + "&nbsp;" + element.lang_code + "</option>";
      }
      leftSelect.append(leftOption);
      rightSelect.append(rightOption);
    },
    error: function (error) {
      console.log(error);
      alert('Error when get languages');
    }
  });

  moveRight.on('click', function () {
    leftSelect.find('option:selected').detach().prop("selected", false).appendTo(rightSelect);
    updateButton();
  });

  moveLeft.on('click', function () {
    rightSelect.find('option:selected').detach().prop("selected", false).appendTo(leftSelect);
    updateButton();
    updateRightButtons();
  });

  moveTop.on('click', function () {
    // The 1ms timeout fixes a display bug in Chrome (4/28/2020)
    let detached = rightSelect.find('option:selected').detach();
    setTimeout(function() {detached.prependTo(rightSelect);}, 1);
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

  moveBottom.on('click', function () {
    rightSelect.find('option:selected').detach().appendTo(rightSelect);
  });

  rightSelect.on('change', function() {
    if (moveTop.prop('disabled')) {
      moveTop.prop('disabled', false);
      moveUp.prop('disabled', false);
      moveDown.prop('disabled', false);
      moveBottom.prop('disabled', false);
    }
  });

  function updateButton() {
    let moveRightDisabled = true;
    if (leftSelect.children().length) {
      moveRightDisabled = false;
    }
    moveRight.prop("disabled", moveRightDisabled);

    let moveLeftDisabled = true;
    if (rightSelect.children().length) {
      moveLeftDisabled = false;
    }
    moveLeft.prop("disabled", moveLeftDisabled);
    saveBtn.prop("disabled", moveLeftDisabled);
  }

  function updateRightButtons() {
    moveTop.prop('disabled', true);
    moveUp.prop('disabled', true);
    moveDown.prop('disabled', true);
    moveBottom.prop('disabled', true);
  }

  function addAlert(message) {
    $('#alerts').append(
        '<div class="alert alert-light" id="alert-style">' +
        '<button type="button" class="close" data-dismiss="alert">' +
        '&times;</button>' + message + '</div>');
         }

 $('#btn_commit_lg').on('click', function () {

    const children = $('#leftSelect').children();
    const selectedChildren = $('#rightSelect').children();
    const map = {};
    for (let index = 0; index < results.length; index++) {
      map[results[index].lang_code] = results[index];
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
      contentType: 'application/json',
      data: JSON.stringify(results),
      success: function (data) {
          var success_message = 'Update languages action successfully';
          addAlert(success_message);
      },
      error: function (error) {
        console.log(error);
        alert('Update languages action erroneously');
      }
    });
  });
});
