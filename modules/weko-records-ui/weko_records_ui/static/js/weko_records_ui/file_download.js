const confirm_msg = $('input[id="confirm_msg"]').val();
const error_msg = $('input[id="error_msg"]').val();
const comp_msg = $('input[id="comp_msg"]').val();

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
    const retry_count = Number($('input[id="retry_count"]').val());
    if(!confirm(confirm_msg)){
        return;
    }

    $('div.lds-ring-background').append('<p>')
    const ring_background = $('div.lds-ring-background').get(0);
    const ring_text = ring_background.getElementsByTagName("p")[0]

    ring_text.style.cssText = "position: fixed;" + 
    " top: 66.666%;" +
    " left: 50%; " +
    "text-align: center; " +
    "font-size: 50px; " +
    "font-family: Meiryo; " +
    "margin-right: -50%; " +
    "transform: translate(-50%, -50%);"

    let newHandle;
    try{
        newHandle = await window.showSaveFilePicker({suggestedName: fileName});
    }catch(e){
        console.log("abort");
        ring_text.remove();
        return;
    }
    let contentLength = parseInt(content_length);
    const BUFFER_SIZE = parseInt(buffer_size);

    let writableStream;
    try{
      writableStream = await newHandle.createWritable();
    }catch(e){
      console.log("File Download Failed", new Date());
      showErrorMsg(error_msg, false, ediv)
      ring_text.remove();
      return;
    }
    ring_text.textContent = $('input[id="download_start_msg"]').val();
    ring_background.classList.remove("hidden");
    ring_zIndex = ring_background.style.zIndex;
    ring_background.style.zIndex = "2000";
  
    let offset = 0;
    let partNumber = 1;
    let retryCount = 0;
  
    let xhr = new XMLHttpRequest();
    xhr.responseType = "blob";

    xhr.onerror = function(){
      if(retryCount < retry_count){
        console.log("retry partNumber", partNumber)
        retryCount += 1;
        xhr.open("GET", "https://" + host + "/record/" + recNum + "/multipartfiles/" + fileName + "?partNumber=" + partNumber, true)
        xhr.send();
        return;
      }else{
        console.log("File Download Failed", new Date());
        xhr.abort();
        showErrorMsg(error_msg, false, ediv)
        ring_background.classList.add("hidden");
        ring_background.style.zIndex = ring_zIndex;
        ring_text.remove();
        return;
      }
    }
  
    getted_file_size = 0
    xhr.onload = async function() {
        if(!(xhr.status === 200 || xhr.status === 206)){
          if(retryCount < retry_count){
            console.log("retry partNumber", partNumber)
            retryCount += 1;
            xhr.open("GET", "https://" + host + "/record/" + recNum + "/multipartfiles/" + fileName + "?partNumber=" + partNumber, true)
            xhr.send();
            return;
          }else{
            console.log("File Download Failed", new Date());
            xhr.abort();
            showErrorMsg(error_msg, false, ediv)
            ring_background.classList.add("hidden");
            ring_background.style.zIndex = ring_zIndex;
            ring_text.remove();
            return;
          }
        }
        partNumber += 1;
        retryCount = 0;
        offset += BUFFER_SIZE;
        getted_file_size += Number(xhr.response.size)
        
        try{
          await writableStream.write(xhr.response);
        }catch(e){
          console.log(e);
          console.log("File Download Failed", new Date());
          xhr.abort();
          showErrorMsg(error_msg, false, ediv)
          ring_background.classList.add("hidden");
          ring_background.style.zIndex = ring_zIndex;
          ring_text.remove();
          return;
        }

        ring_text.textContent = $('input[id="downloading_msg"]').val() + ": " + ((offset/contentLength)*100).toFixed(3) + "%";
  
        if(offset < contentLength){
            xhr.open("GET", "https://" + host + "/record/" + recNum + "/multipartfiles/" + fileName + "?partNumber=" + partNumber, true)
            xhr.send();
        }else{
          console.log(getted_file_size)
          ring_text.textContent = $('input[id="download_comp_process_msg"]').val();
          await writableStream.close();
          showErrorMsg(comp_msg, true, ediv);
          ring_background.classList.add("hidden");
          ring_background.style.zIndex = ring_zIndex;
        }
    }
  
    xhr.open("GET", "https://" + host + "/record/" + recNum + "/multipartfiles/" + fileName + "?partNumber=" + partNumber, true)
    xhr.send();
    ring_text.textContent = $('input[id="downloading_msg"]').val() + ": 0%";
  }