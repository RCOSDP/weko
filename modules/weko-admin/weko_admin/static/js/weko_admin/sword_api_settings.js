//poファイル定義の文言をhiddenから取得
const Required_item = document.getElementById("Required_item").value;
const Successfully_Changed = document.getElementById("Successfully_Changed").value;
const Failed_Changed = document.getElementById("Failed_Changed").value;
const itemtype_alert = document.getElementById("Dependency_ItemType_not_found.").value;
let lists = document.getElementById("itemtype_lists").value;
lists = lists.replace('[', '');
lists = lists.replace(']','');
listsarray = lists.split(',');
/** close ErrorMessage area */
function closeError() {
  $('#errors').empty();
}

/** show ErrorMessage */
function showMsg(msg , success=false) {
  $('#messages').append(
      '<div class="alert ' + (success? "alert-success":"alert-danger") + ' alert-dismissable">' +
      '<button type="button" class="close" data-dismiss="alert" aria-hidden="true">' +
      '&times;</button>' + msg + '</div>');
}

function componentDidMount() {
  /** set errorMessage Area */
  const header = document.getElementsByClassName('content-header')[0];
  if (header) {
      const errorElement = document.createElement('div');
      errorElement.setAttribute('id', 'messages');
      header.insertBefore(errorElement, header.firstChild);
  }
}

function isItemtypeDeleted(value){
  var value = new RegExp(value);
  var deletedFlag = true;
  for(i=0; i < Object.keys(listsarray).length; i++){
    if(value.test(listsarray[i])){
      deletedFlag = false;
    }
  }
  return deletedFlag;
}

function toggleMenu() {
  var dataMenu = document.getElementById("data_format");
  var registerMenu = document.getElementById("register_format");
  var itemMenu = document.getElementById("sword_item_type");
  let settings = document.getElementById("current_settings").value;
  settings = JSON.parse(settings);

  if (dataMenu.value === "empty") {
    // 最初のメニューが空欄の場合、二番目のメニューを非活性化し、空欄を選択状態にする
    // 最初のメニューが選択された場合、二番目のメニューを活性化する
    registerMenu.disabled = true;
    registerMenu.value = "empty";
    itemMenu.disabled = true;
    itemMenu.value = "empty";
  } else if(dataMenu.value === "TSV"){
    registerMenu.removeAttribute("disabled");
    itemMenu.removeAttribute("disabled");
    registerMenu.setAttribute("required",true);
    itemMenu.setAttribute("required",true);

    registerMenu.value = settings["data_format"]["TSV"]["register_format"];
    if(isItemtypeDeleted(settings["data_format"]["TSV"]["item_type"])){
      itemMenu.value = "deleted_Item_Type";
    }else{
      itemMenu.value = settings["data_format"]["TSV"]["item_type"];
    }
  } else if(dataMenu.value === "XML"){
    registerMenu.removeAttribute("disabled");
    itemMenu.removeAttribute("disabled");
    registerMenu.setAttribute("required",true);
    itemMenu.setAttribute("required",true);
    registerMenu.value = settings["data_format"]["XML"]["register_format"];
    if(isItemtypeDeleted(settings["data_format"]["XML"]["item_type"])){
      itemMenu.value = "deleted_Item_Type";
    }else{
      itemMenu.value = settings["data_format"]["XML"]["item_type"];
    }
  }else{
    registerMenu.removeAttribute("disabled");
    itemMenu.removeAttribute("disabled");
    registerMenu.setAttribute("required",true);
    itemMenu.setAttribute("required",true);
  }
}

function isEmpty(value){
  if (!value){
    return true;
  }else if(value === 'empty'){
    return true;
  }else{
    return false;
  }
}

function handleDefaultSubmit() {
  const form ={
    'default_format': document.getElementById("default_select").value
  }
  fetch("/admin/swordapi/default_format" ,{method:'POST' ,headers:{'Content-Type':'application/json'} ,credentials:"include", body: JSON.stringify(form)})
  .then(res => {
    if(!res.ok){
      console.log(etext);
  }
    componentDidMount();
    showMsg(Successfully_Changed , true);
  })
  .catch(error => {
    console.log(error);
    componentDidMount();
    showMsg(Failed_Changed , false);
  });
}

function handleSubmit(event) {
  var dataMenu = document.getElementById("data_format");
  var registerMenu = document.getElementById("register_format");
  var itemMenu = document.getElementById("sword_item_type");
  const errorMessages = document.getElementsByClassName('errorMessage');
  const alertMessage = document.getElementsByClassName('alertMessage');
  alertMessage.textContent ='';
  var errorMessagearray = Array.from(errorMessages)
  errorMessagearray.forEach(function(errorMessage){
    errorMessage.textContent = '';
  });
  
  //Validate 
  // required check
  if(isEmpty(dataMenu.value)){
    errorMessages[0].textContent = Required_item;
    return;
  }else if(isEmpty(registerMenu.value) && isEmpty(itemMenu.value)){
    errorMessages[1].textContent = Required_item;
    errorMessages[2].textContent = Required_item;
    return;
  }else if(isEmpty(registerMenu.value)){
    errorMessages[1].textContent = Required_item;
    return;
  }else if(isEmpty(itemMenu.value)){
    errorMessages[2].textContent = Required_item;
    return;
  }else if(itemMenu.value === "deleted_Item_Type") {
    errorMessages[2].textContent = itemtype_alert;
    return;
  }

  const form = {
    'data_format': document.getElementById("data_format").value
    ,'register_format':document.getElementById("register_format").value
    ,'sword_item_type':document.getElementById("sword_item_type").value
  }

  fetch("/admin/swordapi/data_format" ,{method:'POST' ,headers:{'Content-Type':'application/json'} ,credentials:"include", body: JSON.stringify(form)})
  .then(res => {
    if(!res.ok){
      console.log(etext);
  }
    componentDidMount();
    showMsg(Successfully_Changed , true);
  })
  .catch(error => {
    console.log(error);
    componentDidMount();
    showMsg(Failed_Changed , false);
  });
}