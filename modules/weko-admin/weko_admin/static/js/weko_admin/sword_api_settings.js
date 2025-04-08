const Required_item = document.getElementById("Required_item").value;
const Successfully_Changed = document.getElementById("Successfully_Changed").value;
const Failed_Changed = document.getElementById("Failed_Changed").value;
const item_required_alert = document.getElementById("items_required_alert").value;
const workflow_deleted_alert = document.getElementById("workflow_deleted_alert").value;
const registration_type_value = document.getElementById("registration_type_value").value;
const workflow_value = document.getElementById("workflow_value").value;
const page_type_value = document.getElementById("page_type").value;
let settings = document.getElementById("current_settings_json").value;
settings = JSON.parse(settings);
let deleted_workflows_name = document.getElementById("deleted_workflows_name").value;
deleted_workflows_name = JSON.parse(deleted_workflows_name);


/** close ErrorMessage area */
function closeError() {
  $('#errors').empty();
}

/** show ErrorMessage */
function showMsg(msg, success = false) {
  $('#errors').append(
    '<div class="alert ' + (success ? "alert-success" : "alert-danger") + ' alert-dismissable">' +
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

function isDeletedWorkflow(value) {
  let is_deleted = false;
  let keys = Object.keys(deleted_workflows_name)
  if (keys.includes(value)) {
    is_deleted = true;
  }
  return is_deleted;
}

function changeRegistrationType(value) {
  const workflowMenu = document.getElementById("workflow");
  closeError();

  if (value === "empty") {
    workflowMenu.disabled = true;
    workflowMenu.value = "empty";
  } else if (value === "Direct") {
    workflowMenu.value = "";
    workflowMenu.disabled = true;
  } else if (value === "Workflow") {
    workflowMenu.removeAttribute("disabled");
    workflowMenu.setAttribute("required", true);
    if (isDeletedWorkflow(settings["XML"]["workflow"])) {
      workflowOption.value = "deleted_workflow";
      workflowOption.textContent = deleted_workflows_name[settings["XML"]["workflow"]] + "(削除済みワークフロー)";
      workflowOption.selected = true;
      workflowOption.setAttribute("hidden", "hidden");
      workflowMenu.appendChild(workflowOption);
      return showMsg(workflow_deleted_alert, false);
    } else {
      workflowMenu.value = settings["XML"]["workflow"];
    }
  } else {
    workflowOption.removeAttribute("disabled");
    workflowMenu.setAttribute("required", true);
  }
}

function isEmpty(value) {
  if (!value) {
    return true;
  } else {
    return false;
  }
}

function saveDataFormat(page_type) {
  const active = document.getElementById("active");
  const registration_type = document.getElementsByName("registration_type");
  const duplicate_check = document.getElementById("duplicate_check");
  let registration_type_save_value = "";
  for (let i = 0; i < registration_type.length; i++) {
    if (registration_type[i].checked) {
      registration_type_save_value = registration_type[i].value;
    }
  }
  const workflowMenu = document.getElementById("workflow");
  closeError();

  //Validate
  // required check
  let NGList = [];
  if (page_type === "XML") {
    if (registration_type_save_value === "Workflow" && workflowMenu.value === '') {
      NGList.push('Workflow');
      return showMsg(item_required_alert + NGList, false);
    }
  }
  if (workflowMenu.value === "deleted_workflow") {
    return showMsg(workflow_deleted_alert, false);
  }

  let active_value = false;
  let duplicate_check_value = false;
  if (active.checked) {
    active_value = true;
  }
  if (duplicate_check.checked) {
    duplicate_check_value = true;
  }

  const form = {
    'active': active_value,
    'registration_type': registration_type_save_value,
    'workflow': workflowMenu.value,
    'duplicate_check': duplicate_check_value
  }

  let url = "/admin/swordapi/";
  if (page_type === "XML") {
    url = "/admin/swordapi/?tab=xml";
  }
  fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, credentials: "include", body: JSON.stringify(form) })
    .then(res => {
      if (!res.ok) {
        console.log(etext);
      }
      showMsg(Successfully_Changed, true);
    })
    .catch(error => {
      console.log(error);
      showMsg(Failed_Changed, false);
    });
}

window.onload = function () {
  const registration_type = document.getElementsByName("registration_type");
  for (let i = 0; i < registration_type.length; i++) {
    if (registration_type[i].value === registration_type_value) {
      registration_type[i].checked = true;
      changeRegistrationType(registration_type_value);
    }
  }
  if (page_type_value === "TSV/CSV") {
    document.getElementById("workflow_div").style.display = 'none';
  }
  if (workflow_value !== '') {
    const select = document.getElementById("workflow");
    const options = select.options;
    for (let i = 0; i < options.length; i++) {
      if (options[i].value === workflow_value) {
        options[i].selected = true;
        break;
      }
    }
  }
  if (page_type_value === "XML") {
    for (let i = 0; i < registration_type.length; i++) {
      if (registration_type[i].value === "Direct") {
        registration_type[i].disabled = true;
      }
    }
  }

};

componentDidMount();
