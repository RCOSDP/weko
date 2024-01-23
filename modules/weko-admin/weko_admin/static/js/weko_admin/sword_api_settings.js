//poファイル定義の文言をhiddenから取得
const Required_item = document.getElementById("Required_item").value;
const Successfully_Changed = document.getElementById("Successfully_Changed").value;
const Failed_Change = document.getElementById("Failed_Change").value;

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

function toggleMenu() {
  var dataMenu = document.getElementById("data_format");
  var registerMenu = document.getElementById("register_format");
  var itemMenu = document.getElementById("sword_item_type");

  if (dataMenu.value === "empty") {
    // 最初のメニューが空欄の場合、二番目のメニューを非活性化し、空欄を選択状態にする
    registerMenu.disabled = true;
    registerMenu.value = "empty";
    itemMenu.disabled = true;
    itemMenu.value = "empty";
  } else {
    // 最初のメニューが選択された場合、二番目のメニューを活性化する
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
  fetch("/admin/swordapi/" ,{method:'POST' ,headers:{'Content-Type':'application/json'} ,credentials:"include", body: JSON.stringify(form)})
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
    showMsg(Failed_Change , false);
  });
}

function handleSubmit(event) {
  var dataMenu = document.getElementById("data_format");
  var registerMenu = document.getElementById("register_format");
  var itemMenu = document.getElementById("sword_item_type");
  const errorMessages = document.getElementsByClassName('errorMessage');
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
    showMsg(Failed_Change , false);
  });

}