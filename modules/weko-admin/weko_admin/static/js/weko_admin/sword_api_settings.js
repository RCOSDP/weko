const Required_item = document.getElementById("Required_item").value;
const Successfully_Changed = document.getElementById("Successfully_Changed").value;
const Failed_Changed = document.getElementById("Failed_Changed").value;
const item_required_alert = document.getElementById("items_required_alert").value;
const workflow_deleted_alert = document.getElementById("workflow_deleted_alert").value;
let settings = document.getElementById("current_settings_json").value;
settings = JSON.parse(settings);
let deleted_workflows_name = document.getElementById("deleted_workflows_name").value;
deleted_workflows_name = JSON.parse(deleted_workflows_name);

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
  var is_deleted = false;
  var keys = Object.keys(deleted_workflows_name)
  if(keys.includes(value)){
    is_deleted = true;
  }
  return is_deleted;
}

function toggleMenu() {
  const dataMenu = document.getElementById("data_format");
  const registerMenu = document.getElementById("register_format");
  const workflowMenu = document.getElementById("workflow");
  const workflowOption = document.createElement('option');
  closeError();

  if (dataMenu.value === "empty") {
    // 最初のメニューが空欄の場合、二番目のメニューを非活性化し、空欄を選択状態にする
    // 最初のメニューが選択された場合、二番目のメニューを活性化する
    registerMenu.disabled = true;
    registerMenu.value = "empty";
    workflowMenu.disabled = true;
    workflowMenu.value = "empty";
  } else if(dataMenu.value === "TSV"){
    registerMenu.value ="Direct";
    workflowMenu.value = "";
    workflowMenu.disabled = true;
  } else if(dataMenu.value === "XML"){
    registerMenu.value = "Workflow";
    workflowMenu.removeAttribute("disabled");
    workflowMenu.setAttribute("required",true);
      if(isDeletedWorkflow(settings["data_format"]["XML"]["workflow"])){
        workflowOption.value = "deleted_workflow";
        workflowOption.textContent = deleted_workflows_name[settings["data_format"]["XML"]["workflow"]] + "(削除済みワークフロー)";
        workflowOption.selected = true;
        workflowOption.setAttribute("hidden","hidden");
        workflowMenu.appendChild(workflowOption);
        return showMsg(workflow_deleted_alert, false);
      }else{
        workflowMenu.value = settings["data_format"]["XML"]["workflow"];
      }
  }else{
    registerMenu.removeAttribute("disabled");
    workflowOption.removeAttribute("disabled");
    registerMenu.setAttribute("required",true);
    workflowMenu.setAttribute("required",true);
  }
}


function isEmpty(value){
  if (!value){
    return true;
  }else{
    return false;
  }
}

function handleDefaultSubmit() {
  const form ={
    'default_format': document.getElementById("default_select").value
  }
  closeError();
  fetch("/admin/swordapi/default_format" ,{method:'POST' ,headers:{'Content-Type':'application/json'} ,credentials:"include", body: JSON.stringify(form)})
  .then(res => {
    if(!res.ok){
      console.log(etext);
  }
    showMsg(Successfully_Changed , true);
  })
  .catch(error => {
    console.log(error);
    showMsg(Failed_Changed , false);
  });
}

function handleSubmit(event) {
  const dataMenu = document.getElementById("data_format");
  const registerMenu = document.getElementById("register_format");
  const workflowMenu = document.getElementById("workflow");
  closeError();
  
  //Validate 
  // required check
  NGList = [];
  if(isEmpty(dataMenu.value)){
    NGList.push('Data Format');
  }
  if(NGList.length){
    return showMsg(item_required_alert + NGList , false);
  }
  if(workflowMenu.value === "deleted_workflow") {
    return showMsg(workflow_deleted_alert, false);
  }
  

  const form = {
    'data_format': document.getElementById("data_format").value
    ,'register_format':document.getElementById("register_format").value
    ,'workflow':document.getElementById("workflow").value
  }

  fetch("/admin/swordapi/data_format" ,{method:'POST' ,headers:{'Content-Type':'application/json'} ,credentials:"include", body: JSON.stringify(form)})
  .then(res => {
    if(!res.ok){
      console.log(etext);
  }
    showMsg(Successfully_Changed , true);
  })
  .catch(error => {
    console.log(error);
    showMsg(Failed_Changed , false);
  });
}
componentDidMount();