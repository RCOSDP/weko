
const Successfully_Changed = document.getElementById("Successfully_Changed").value;
const Failed_Changed = document.getElementById("Failed_Changed").value;
const item_required_alert = document.getElementById("items_required_alert").value;
const workflow_deleted_alert = document.getElementById("workflow_deleted_alert").value;
const Unapproved_Items_Exit = document.getElementById("Unapproved_Items_Exit").value;
const current_page_type = document.getElementById("current_page_type").value;
const current_model_json = JSON.parse(document.getElementById('current_model_json').value);
const current_name = document.getElementById("current_name").value;
const current_item_type_id = document.getElementById("current_item_type_id").value;
const current_mapping = document.getElementById("current_mapping").value;

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

function isEmpty(value){
  if (!value){
    return true;
  }else{
    return false;
  }
}

$("#workflow").change(function(){
  // mapping set
  const selectedOption = $(this).find('option:selected');
  const select_item_type_id = selectedOption.data('itemtype');
  $("#mapping").children().remove();
  $('#mapping').append($('<option>').html("").val(""));
  for (let i = 0; i < sword_item_type_mappings.length; i++){
    if (sword_item_type_mappings[i]["item_type_id"] === select_item_type_id) {
      $('#mapping').append($('<option>').html(sword_item_type_mappings[i]["name"]).val(sword_item_type_mappings[i]["id"]));
    }
  }

  // save button enable
  save_button_state_change();
});

function save_button_state_change() {
  if ( $('#mapping').val() !== "" ) {
    $('#save_button').prop("disabled", false);
  } else {
    $('#save_button').prop("disabled", true);
  }
}

async function saveDataFormat(type) {

  closeError();

  const name_value = document.getElementById("name").value;
  const item_type_id_value = document.getElementById("item_type").value;
  let mapping_value = document.getElementById("mapping").value;

  //Validate
  // required check
  NGList = [];
  if(name_value === ""){
    NGList.push('Name');
    return showMsg(item_required_alert + NGList , false);
  }
  if(item_type_id_value === ""){
    NGList.push('Item Type');
    return showMsg(item_required_alert + NGList , false);
  }
  if(mapping_value === ""){
    NGList.push('Mapping');
    return showMsg(item_required_alert + NGList , false);
  }
  try {
    mapping_value = JSON.parse(mapping_value);
  } catch (error) {
      alert('Invalid JSON:', error);
      return;
  }

  // mapping check
  const data = {
    'mapping_id': mapping_value,
    'itemtype_id': item_type_id_value,
  }
  let check = true;
  url ="/sword/validate_mapping";
  await fetch(url ,{method:'POST' ,headers:{'Content-Type':'application/json'} ,credentials:"include", body: JSON.stringify(data)})
  .then(res => {
    if (!res.ok) {
      return res.json().then(errorData => {
          throw new Error(errorData.error);
      });
    }
    return res.json();
  })
  .then(result => {
    if (result !== null) {
      const message = result.join(', ');
      $('#modal-message').text('mapping inconsistency.' + message );
      $('#error_modal').modal('show');
      return;
    }
  })
  .catch(error => {
    alert('validation check error' + error.message);
    check = false;
  });

  if (check === false){
    return;
  }

  const form = {
    'name': name_value
    ,'mapping': mapping_value
    ,'item_type_id': item_type_id_value
  }
  if (type === "new") {
    url ="/admin/jsonld-mapping/new/?url=%2Fadmin%2ItemType%2Fjsonld-mapping%2F";
  } else {
    url ="/admin/jsonld-mapping/edit/" + current_model_json["id"] + "/?url=%2Fadmin%2ItemType%2Fjsonld-mapping%2F";
  }
  fetch(url ,{method:'POST' ,headers:{'Content-Type':'application/json'} ,credentials:"include", body: JSON.stringify(form)})
  .then(res => {
    if(!res.ok){
      console.log(error);
    }
    alert(Successfully_Changed);
    window.location.href = "/admin/jsonld-mapping/";
  })
  .catch(error => {
    console.log(error);
    showMsg(Failed_Changed , false);
  });
}

function openDeleteModal() {
  $('#delete_modal').modal('show');
}

function deleteData(){
  closeError();
  const form = {}
  fetch("/admin/jsonld-mapping/delete/" + current_model_json["id"] + "/?url=%2Fadmin%2ItemType%2Fjsonld-mapping%2F" ,
    {method:'POST' ,headers:{'Content-Type':'application/json'} ,credentials:"include", body: JSON.stringify(form)})
  .then(res => {
    if(!res.ok){
      console.log(error);
    }
    alert(Successfully_Changed);
    window.location.href = "/admin/jsonld-mapping/";
  })
  .catch(error => {
    console.log(error);
    showMsg(Failed_Changed , false);
  });
}

window.onload = function() {
  if ( current_page_type === "new" ) {
    // new
    // registration_type[0].checked = true;
    // changeRegistrationType("Direct");
  } else{
    // edit
    $('#name').val(current_name);
    $('#item_type').val(current_item_type_id);
    $('#mapping').val(current_mapping);

    if (exist_Waiting_approval_workflow === "True") {
      $('#modal-message').text(Unapproved_Items_Exit);
      $('#error_modal').modal('show');
      $('#save_button').prop("disabled", true);
    }
  }
};


componentDidMount();
