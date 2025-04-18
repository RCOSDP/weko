const Successfully_Changed = document.getElementById('Successfully_Changed').value;
const Failed_Changed = document.getElementById('Failed_Changed').value;
const item_required_alert = document.getElementById('items_required_alert').value;
const workflow_deleted_alert = document.getElementById('workflow_deleted_alert').value;
const Unapproved_Items_Exit = document.getElementById('Unapproved_Items_Exit').value;
const current_page_type = document.getElementById('current_page_type').value;
const current_model_json = JSON.parse(document.getElementById('current_model_json').value);
const can_edit = document.getElementById('can_edit').value;
const current_name = document.getElementById('current_name').value;
const current_item_type_id = document.getElementById('current_item_type_id').value;
const current_mapping = document.getElementById('current_mapping').value;

/** close ErrorMessage area */
function closeError() {
  $('#errors').empty();
}

/** show ErrorMessage */
function showMsg(msg, success = false) {
  $('#errors').append(
    '<div class="alert ' +
      (success ? 'alert-success' : 'alert-danger') +
      ' alert-dismissable">' +
      '<button type="button" class="close" data-dismiss="alert" aria-hidden="true">' +
      '&times;</button>' +
      msg +
      '</div>'
  );
}

function componentDidMount() {
  /** set errorMessage Area */
  const header = document.getElementsByClassName('content-header')[0];
  if (header) {
    const errorElement = document.createElement('div');
    errorElement.setAttribute('id', 'errors');
    header.insertBefore(errorElement, header.firstChild);
  }
}

function isEmpty(value) {
  if (!value) {
    return true;
  } else {
    return false;
  }
}

$('#workflow').change(function () {
  // mapping set
  const selectedOption = $(this).find('option:selected');
  const select_item_type_id = selectedOption.data('itemtype');
  $('#mapping').children().remove();
  $('#mapping').append($('<option>').html("").val(""));
  for (let i = 0; i < sword_item_type_mappings.length; i++) {
    if (sword_item_type_mappings[i]['item_type_id'] === select_item_type_id) {
      $('#mapping').append(
        $('<option>')
          .html(sword_item_type_mappings[i]['name'])
          .val(sword_item_type_mappings[i]['id'])
      );
    }
  }

  // save button enable
  save_button_state_change();
});

function save_button_state_change() {
  if ($('#mapping').val() !== '') {
    $('#save_button').prop('disabled', false);
  } else {
    $('#save_button').prop('disabled', true);
  }
}

async function saveDataFormat(event, type) {
  event.preventDefault();
  closeError();

  const name_value = document.getElementById('name').value;
  const item_type_id_value = document.getElementById('item_type').value;
  let mapping_value = document.getElementById('mapping').value;

  //Validate
  // required check
  NGList = [];
  if (name_value === '') {
    NGList.push('Name');
    return showMsg(item_required_alert + NGList, false);
  }
  if (item_type_id_value === '') {
    NGList.push('Item Type');
    return showMsg(item_required_alert + NGList, false);
  }
  if (mapping_value === '') {
    NGList.push('Mapping');
    return showMsg(item_required_alert + NGList, false);
  }
  try {
    mapping_value = JSON.parse(mapping_value);
  } catch (error) {
    return showMsg('Invalid JSON', false);
  }

  // mapping check
  const data = {
    mapping: mapping_value,
    itemtype_id: item_type_id_value,
  };
  let check = true;
  url = '/admin/jsonld-mapping/validate';
  await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(data),
  })
    .then((res) => {
      if (!res.ok) {
        return res.json().then((errorData) => {
          throw new Error(errorData.error);
        });
      }
      return res.json();
    })
    .then((result) => {
      if (result !== null) {
        const modalMessage = $('#modal-message');
        modalMessage.empty(); // Clear existing content
        result.forEach((message) => {
          modalMessage.append('<p>' + message + '</p>');
        });
        $('#error_modal').modal('show');
        check = false;
        return;
      }
    })
    .catch((error) => {
      check = false;
    });

  if (check === false) {
    return showMsg('Failed to validate mapping', false);
  }

  const form = {
    name: name_value,
    mapping: mapping_value,
    item_type_id: item_type_id_value,
  };
  if (type === 'new') {
    url = '/admin/jsonld-mapping/new/';
  } else {
    url = '/admin/jsonld-mapping/edit/' + current_model_json['id'];
  }
  fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(form),
  })
    .then((res) => {
      if (!res.ok) {
        throw new Error('');
      }
      showMsg(Successfully_Changed, true);
      window.location.href = '/admin/jsonld-mapping/';
    })
    .catch((error) => {
      showMsg(Failed_Changed, false);
    });
}

function openDeleteModal() {
  $('#delete_modal').modal('show');
}

function deleteData() {
  closeError();
  fetch(
    '/admin/jsonld-mapping/delete/' + current_model_json['id'],
    {
      method: 'DELETE',
      credentials: 'include',
    }
  )
    .then((res) => {
      if (!res.ok) {
        throw new Error('');
      }
      showMsg(Successfully_Changed, true);
      window.location.href = '/admin/jsonld-mapping/';
    })
    .catch((error) => {
      showMsg(Failed_Changed, false);
    });
}

window.onload = function () {
  if (current_page_type === 'edit') {
    $('#name').val(current_name);
    $('#item_type').val(current_item_type_id);
    try {
      $('#mapping').val(
        JSON.stringify(
          JSON.parse(
            document.getElementById('current_mapping').value.replace(/'/g, '"')
          ),
          null,
          4
        )
      );
    } catch (error) {
      showMsg('Failed to get mapping', false);
    }

    if (can_edit === 'False') {
      $('#modal-message').text(Unapproved_Items_Exit);
      $('#error_modal').modal('show');
      $('#save_button').prop('disabled', true);
      $('#delete_button').prop('disabled', true);
    }
  }
};

componentDidMount();
