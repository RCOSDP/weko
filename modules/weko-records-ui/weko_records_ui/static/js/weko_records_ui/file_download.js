const confirm_msg = $('input[id="confirm_msg"]').get(0).value;
const error_msg = $('input[id="error_msg"]').get(0).value;
const comp_msg = $('input[id="comp_msg"]').get(0).value;

function closeError(ediv) {
    $('div#' + ediv).empty();
}

function showErrorMsg(msg , success=false, ediv) {
    $('div#' + ediv).append(
        '<div class="alert ' + (success? "alert-success":"alert-danger") + ' alert-dismissable">' +
        '<button type="button" class="close" data-dismiss="alert" aria-hidden="true">' +
        '&times;</button>' + msg + '</div>');
}

async function downloadFile(recNum, fileName, content_length, buffer_size, event){
    let ediv = event.getAttribute("ediv")
    if(!ediv){
        ediv = "errors";
    }
    const host = window.location.host;
    const retry_count = $('input[id="retry_count"]');
    if(!confirm(confirm_msg)){
        return;
    }

    const ring_background = $('div.lds-ring-background').get(0);
    let newHandle;
    try{
        newHandle = await window.showSaveFilePicker({suggestedName: fileName});
    }catch(e){
        console.log("abort")
        return;
    }
    let contentLength = parseInt(content_length);
    const BUFFER_SIZE = parseInt(buffer_size);

    let writableStream = await newHandle.createWritable();
    ring_background.classList.remove("hidden");
  
    let offset = 0;
    let partNumber = 1;
    let retryCount = 0;
  
    let xhr = new XMLHttpRequest();
    xhr.responseType = "blob";

    xhr.onerror = function(){
      if(retryCount < retry_count){
        retryCount += 1;
        xhr.open("GET", "https://" + host + "/record/" + recNum + "/multipartfiles/" + fileName + "?partNumber=" + partNumber, true)
        xhr.send();
        return;
      }else{
        console.log("File Download Failed", new Date());
        xhr.abort();
        showErrorMsg(error_msg, false, ediv)
        ring_background.classList.add("hidden");
        return;
      }
    }
  
    xhr.onload = async function() {
        if(String(xhr.status).indexOf("2") != 0){
          if(retryCount < retry_count){
            retryCount += 1;
            xhr.open("GET", "https://" + host + "/record/" + recNum + "/multipartfiles/" + fileName + "?partNumber=" + partNumber, true)
            xhr.send();
            return;
          }else{
            console.log("File Download Failed", new Date());
            xhr.abort();
            showErrorMsg(error_msg, false, ediv)
            ring_background.classList.add("hidden");
            return;
          }
        }
        partNumber += 1;
        
        await writableStream.write(xhr.response);
  
        if(offset + BUFFER_SIZE < contentLength){
            offset += BUFFER_SIZE;
            xhr.open("GET", "https://" + host + "/record/" + recNum + "/multipartfiles/" + fileName + "?partNumber=" + partNumber, true)
            xhr.send();
        }else{
          await writableStream.close();
          showErrorMsg(comp_msg, true, ediv);
          ring_background.classList.add("hidden");
        }
    }
  
    xhr.open("GET", "https://" + host + "/record/" + recNum + "/multipartfiles/" + fileName + "?partNumber=" + partNumber, true)
    xhr.send();
  }