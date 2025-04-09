
$(document).ready(function () {

  const moveRight = $('#moveRight');
  const moveLeft = $('#moveLeft')
  const moveTop = $('#moveTop')
  const moveUp = $('#moveUp')
  const moveDown = $('#moveDown')
  const moveBottom = $('#moveBottom')
  const leftSelect = $('#leftSelect');
  const rightSelect = $('#rightSelect');

  moveTop.prop('disabled', true);
  moveUp.prop('disabled', true);
  moveDown.prop('disabled', true);
  moveBottom.prop('disabled', true);

  moveRight.on('click', function () {
    leftSelect.find('option:selected').detach().prop('selected', false).appendTo(rightSelect);
    updateButton();
  });

  moveLeft.on('click', function () {
    rightSelect.find('option:selected').detach().prop('selected', false).appendTo(leftSelect);
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
    moveRight.prop('disabled', moveRightDisabled);

    let moveLeftDisabled = true;
    if (rightSelect.children().length) {
      moveLeftDisabled = false;
    }
    moveLeft.prop('disabled', moveLeftDisabled);
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
});


const Successfully_Changed = document.getElementById('Successfully_Changed').value;
const Failed_Changed = document.getElementById('Failed_Changed').value;
const item_required_alert = document.getElementById('items_required_alert').value;
const workflow_deleted_alert = document.getElementById('workflow_deleted_alert').value;
const registration_type_value = document.getElementById('registration_type_value').value;
const workflow_value = document.getElementById('workflow_value').value;
const deleted_workflows_name = JSON.parse(document.getElementById('deleted_workflows_name').value);
const sword_item_type_mappings = JSON.parse(document.getElementById('sword_item_type_mappings').value);
const current_page_type = document.getElementById('current_page_type').value;
const current_model_json = JSON.parse(document.getElementById('current_model_json').value);
const exist_Waiting_approval_workflow = document.getElementById('exist_Waiting_approval_workflow').value;
const item_type_names = JSON.parse(document.getElementById('item_type_names').value);

/** close ErrorMessage area */
function closeError() {
  $('#errors').empty();
}

/** show ErrorMessage */
function showMsg(msg , success=false) {
  $('#errors').append(
      '<div class="alert ' + (success? "alert-success":"alert-danger") + ' alert-dismissable">' +
      '<button type="button" class="close" data-dismiss="alert" aria-hidden="true">' +
      '&times;</button>' + msg + '</div>');
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

function isDeletedWorkflow(value){
  let is_deleted = false;
  let keys = Object.keys(deleted_workflows_name)
  if(keys.includes(value)){
    is_deleted = true;
  }
  return is_deleted;
}

function changeRegistrationType(value) {
  const workflowMenu = document.getElementById('workflow');
  closeError();

  if (value === 'empty') {
    workflowMenu.disabled = true;
    workflowMenu.value = 'empty';
  } else if (value === 'Direct') {
    workflowMenu.value = '';
    workflowMenu.disabled = true;

    // mapping set
    $('#mapping').children().remove();
    $('#mapping').append($('<option>').html("").val(""));
    for (let i = 0; i < sword_item_type_mappings.length; i++) {
      $('#mapping').append(
        $('<option>')
          .html(sword_item_type_mappings[i]['name'])
          .val(sword_item_type_mappings[i]['id'])
      );
    }
  } else if (value === 'Workflow') {
    workflowMenu.removeAttribute('disabled');
    workflowMenu.setAttribute('required', true);
    if (isDeletedWorkflow('workflow_current')) {
      workflowOption.value = 'deleted_workflow';
      workflowOption.textContent =
        deleted_workflows_name['workflow_current'] + '(削除済みワークフロー)';
      workflowOption.selected = true;
      workflowOption.setAttribute('hidden', 'hidden');
      workflowMenu.appendChild(workflowOption);
      return showMsg(workflow_deleted_alert, false);
    } else {
      workflowMenu.value = 'workflow_current';
    }
    $('#mapping').children().remove();
    $('#mapping').append($('<option>').html("").val(""));
  } else {
    workflowOption.removeAttribute('disabled');
    workflowMenu.setAttribute('required', true);
  }
  // save button enable
  save_button_state_change();
}

function isEmpty(value){
  if (!value){
    return true;
  }else{
    return false;
  }
}

$('#workflow').change(function(){
  // mapping set
  const selectedOption = $(this).find('option:selected');
  const select_item_type_id = selectedOption.data('itemtype');
  $('#mapping').children().remove();
  $('#mapping').append($('<option>').html("").val(""));
  for (let i = 0; i < sword_item_type_mappings.length; i++){
    if (sword_item_type_mappings[i]['item_type_id'] === select_item_type_id) {
      $('#mapping').append($('<option>').html(sword_item_type_mappings[i]['name']).val(sword_item_type_mappings[i]['id']));
    }
  }

  // save button enable
  save_button_state_change();
});

$('#mapping').change(async function(){
  // save button enable
  save_button_state_change();

  // mapping check
  mapping_val = $(this).val();
  if ( mapping_val !== '' ){
    mapping_val = Number(mapping_val);
    let result = sword_item_type_mappings.find(data => data.id === mapping_val);
    item_type_id = result['item_type_id'];
    result = item_type_names.find(data => data.id === item_type_id);
    item_type_name = result['name'];


    const form = {
      'mapping_id': mapping_val,
      'itemtype_id': item_type_id,
    }
    url ='/sword/validate_mapping';
    await fetch(url ,{method:'POST' ,headers:{'Content-Type':'application/json'} ,credentials:'include', body: JSON.stringify(form)})
    .then(res => {
      if (!res.ok) {
        return res.json().then(errorData => {
            throw new Error(errorData.error);
        });
      }
      return res.json();
    })
    .then(result => {
      if (result === null) {
        $('#mapping-check').empty();
        $('#mapping-check').append('Item type : ' + item_type_name + '<span class="text-success">✓</span>');
        $('#save_button').prop('disabled', false);
      } else{
        $('#mapping-check').append('Item type:' + item_type_name + '<span class="text-danger">✘</span>');
      }
    })
    .catch(error => {
      alert('validation check error');
      return;
    });

  } else {
    $('#mapping-check').empty();
  }
});

function save_button_state_change() {
  if ( $('#mapping').val() !== '' ) {
    $('#save_button').prop('disabled', false);
  } else {
    $('#save_button').prop('disabled', true);
  }
}

function saveDataFormat(type) {
  const application = document.getElementById('application');
  const active = document.getElementById('active');
  const registration_type = document.getElementsByName('registration_type');
  for (let i = 0; i < registration_type.length; i++) {
    if (registration_type[i].checked) {
      registration_type_save_value = registration_type[i].value;
    }
  }
  const workflowMenu = document.getElementById('workflow');
  const duplicate_check = document.getElementById('duplicate_check');
  closeError();

  //Validate
  // required check
  NGList = [];
  if (
    registration_type_save_value === 'Workflow' &&
    workflowMenu.value === ''
  ) {
    NGList.push('Workflow');
    return showMsg(item_required_alert + NGList, false);
  }
  if (current_page_type === 'add') {
    if (application.value === '') {
      NGList.push('Application');
      return showMsg(item_required_alert + NGList, false);
    }
  }
  if ($('#mapping').val() === '') {
    NGList.push('Mapping');
    return showMsg(item_required_alert + NGList, false);
  }
  if (workflowMenu.value === 'deleted_workflow') {
    return showMsg(workflow_deleted_alert, false);
  }

  active_value = 'False';
  duplicate_check_value = 'False';
  if (active.checked) {
    active_value = 'True';
  }
  if (duplicate_check.checked) {
    duplicate_check_value = 'True';
  }

  const children = $('#leftSelect').children();
  const selectedChildren = $('#rightSelect').children();
  selected_API = [];
  for (let index = 0; index < selectedChildren.length; index++) {
    let element = selectedChildren[index].value;
    selected_API.push(element);
  }
  no_selected_API = [];
  for (let index = 0; index < children.length; index++) {
    let element = children[index].value;
    no_selected_API.push(element);
  }

  const mapping = document.getElementById('mapping');

  const form = {
    application: application.value,
    active: active_value,
    registration_type: registration_type_save_value,
    workflow_id: workflowMenu.value,
    mapping_id: mapping.value,
    duplicate_check: duplicate_check_value,
    Meta_data_API_selected: selected_API,
    Meta_data_API_no_selected: no_selected_API,
  };

  if (type === 'add') {
    url = '/admin/swordapi/jsonld/add/';
  } else {
    url = '/admin/swordapi/jsonld/edit/' + current_model_json['id'];
  }
  fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(form),
  })
    .then((res) => {
      if (!res.ok) {
        throw new Error('Failed to save data');
      }
      showMsg(Successfully_Changed, true);
      window.location.href = '/admin/swordapi/jsonld/';
    })
    .catch((error) => {
      showMsg(Failed_Changed, false);
    });
}

window.onload = function () {
  const registration_type = document.getElementsByName('registration_type');
  if (current_page_type === 'add') {
    // add
    registration_type[0].checked = true;
    changeRegistrationType('Direct');
  } else {
    // edit
    if (current_model_json['active'] === true) {
      $('#active').prop('checked', true);
    }
    if (current_model_json['registration_type_id'] === 1) {
      // Direct
      registration_type[0].checked = true;
      changeRegistrationType('Direct');
      $('#mapping').val(current_model_json['mapping_id']);
    } else {
      // Workflow
      registration_type[1].checked = true;
      changeRegistrationType('Workflow');
      $('#workflow').val(current_model_json['workflow_id']);
      // mapping set
      const selectedOption = $('#workflow').find('option:selected');
      const select_item_type_id = selectedOption.data('itemtype');
      $('#mapping').children().remove();
      $('#mapping').append($('<option>').html("").val(""));
      for (let i = 0; i < sword_item_type_mappings.length; i++) {
        if (
          sword_item_type_mappings[i]['item_type_id'] === select_item_type_id
        ) {
          $('#mapping').append(
            $('<option>')
              .html(sword_item_type_mappings[i]['name'])
              .val(sword_item_type_mappings[i]['id'])
          );
        }
      }
      $('#mapping').val(current_model_json['mapping_id']);
    }
    if (current_model_json['duplicate_check'] === true) {
      $('#duplicate_check').prop('checked', true);
    }
    const meta_data_api = current_model_json['meta_data_api'];
    meta_data_api.forEach(function (api) {
      $('#leftSelect')
        .find('option[value="' + api + '"]')
        .prop('selected', false)
        .appendTo($('#rightSelect'));
    });
    let moveRightDisabled = true;
    if ($('#leftSelect').children().length) {
      moveRightDisabled = false;
    }
    $('#moveRight').prop('disabled', moveRightDisabled);

    let moveLeftDisabled = true;
    if ($('#rightSelect').children().length) {
      moveLeftDisabled = false;
    }
    $('#moveLeft').prop('disabled', moveLeftDisabled);

    $('#save_button').prop('disabled', false);
    if (exist_Waiting_approval_workflow === 'True') {
      $('#error_modal').modal('show');
      $('#save_button').prop('disabled', true);
      $('#application').prop('disabled', true);
      $('#active').prop('disabled', true);
      $('input[name=registration_type]').prop('disabled', true);
      $('#workflow').prop('disabled', true);
      $('#mapping').prop('disabled', true);
      $('#leftSelect').prop('disabled', true);
      $('#rightSelect').prop('disabled', true);
    }
  }
};


componentDidMount();
