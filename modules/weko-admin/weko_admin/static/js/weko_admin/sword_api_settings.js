const Required_item = document.getElementById("Required_item").value;
const Successfully_Changed = document.getElementById("Successfully_Changed").value;
const Failed_Changed = document.getElementById("Failed_Changed").value;
const item_required_alert = document.getElementById("items_required_alert").value;
const itemtype_deleted_alert = document.getElementById("itemtype_deleted_alert").value;
let settings = document.getElementById("current_settings_json").value;
settings = JSON.parse(settings);
let itemtype_name_dict = document.getElementById("itemtype_name_dict").value;
itemtype_name_dict = JSON.parse(itemtype_name_dict);
let lists = document.getElementById("itemtype_lists").value;
lists = lists.replace('[', '');
lists = lists.replace(']','');
listsarray = lists.split(',');
let deleted_itemtype_lists = document.getElementById("deleted_itemtype_lists").value;
deleted_itemtype_lists = deleted_itemtype_lists.replace('[', '');
deleted_itemtype_lists = deleted_itemtype_lists.replace(']','');
let deleted_itemtype_listsarray = deleted_itemtype_lists.split(',');

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

function isItemtypeDeleted(value){
  var value = new RegExp(value);
  var deletedFlag = false;
  for(i=0; i < deleted_itemtype_listsarray.length; i++){
    if(value.test(deleted_itemtype_listsarray[i])){
      deletedFlag = true;
    }
  }
  return deletedFlag;
}

function toggleMenu() {
  const dataMenu = document.getElementById("data_format");
  const registerMenu = document.getElementById("register_format");
  const itemMenu = document.getElementById("sword_item_type");
  const itemtypeOption = document.createElement('option');
  closeError();

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
      itemtypeOption.value = "deleted_Item_Type";
      itemtypeOption.textContent = itemtype_name_dict[settings["data_format"]["TSV"]["item_type"]] 
      + "(" + settings["data_format"]["XML"]["item_type"] + ")" + "(削除済みアイテムタイプ)";
      itemtypeOption.selected = true;
      itemtypeOption.setAttribute("hidden","hidden");
      itemMenu.appendChild(itemtypeOption);
      return showMsg(itemtype_deleted_alert, false);
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
      itemtypeOption.value = "deleted_Item_Type";
      itemtypeOption.textContent = itemtype_name_dict[settings["data_format"]["XML"]["item_type"]]
       + "(" + settings["data_format"]["XML"]["item_type"] + ")" + "(削除済みアイテムタイプ)";
      itemtypeOption.selected = true;
      itemtypeOption.setAttribute("hidden","hidden");
      itemMenu.appendChild(itemtypeOption);
      return showMsg(itemtype_deleted_alert, false);
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
  }else if(value === ''){
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
  const itemMenu = document.getElementById("sword_item_type");
  closeError();
  
  //Validate 
  // required check
  NGList = [];
  if(isEmpty(dataMenu.value)){
    NGList.push('Data Format');
  }
  if(isEmpty(registerMenu.value)){
    NGList.push('Register Format');
  }
  if(isEmpty(itemMenu.value)){
    NGList.push('Item Type');
  }
  if(NGList.length){
    return showMsg(item_required_alert + NGList , false);
  }
  if(itemMenu.value === "deleted_Item_Type") {
    return showMsg(itemtype_deleted_alert, false);
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
    showMsg(Successfully_Changed , true);
  })
  .catch(error => {
    console.log(error);
    showMsg(Failed_Changed , false);
  });
}
componentDidMount();