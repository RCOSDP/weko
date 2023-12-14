const host = window.location.host;
const retry_count = $('input[id="retry_count"]').get(0).value;
const chunk_size = parseInt($('input[id="chunk_size"]').get(0).value);
const errorMsgList = $('input[id="errormsg"]');

function closeError() {
    $('#errors').empty();
}

function showErrorMsg(msg , success=false) {
    $('#errors').append(
        '<div class="alert ' + (success? "alert-success":"alert-danger") + ' alert-dismissable">' +
        '<button type="button" class="close" data-dismiss="alert" aria-hidden="true">' +
        '&times;</button>' + msg + '</div>');
}

function uploadIdSet(upload_id){
    $('input[id="upload_id_text"]').get(0).value = upload_id
    window.scroll({
        top: 0,
        behavior: "smooth",
    });
}

async function getHash(sha, text){
    const hashBuffer = await crypto.subtle.digest("SHA-256", text);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    const hashHex = hashArray
        .map((b) => b.toString(16).padStart(2, "0"))
        .join("");
    return hashHex;
}

async function multipartUpload(){
    $('button[id="upload_button"]').get(0).disabled = true
    $('input[id="upload_file_area"]').get(0).disabled = true
    closeError();

    let $upfile = $('input[id="upload_file_area"]');
    const file = $upfile.prop('files')[0];

    const uploadStatus_p = $('p[name="upload_status"]')[0];
    const uploadId_p = $('p[name="upload_id"]')[0];

    if(file === undefined){
        $('button[id="upload_button"]').get(0).disabled = false
        $('input[id="upload_file_area"]').get(0).disabled = false
        showErrorMsg(errorMsgList.get(0).value)
        uploadStatus_p.innerText = "Error"
        return;
    }

    let uploadId = $('input[id="upload_id_text"]').get(0).value;
    uploadId_p.innerText = uploadId;

    let contentType = file.type;
    const FILE_NAME = file.name;
    if(!contentType){
        console.log("undefined type");
        contentType = "text/plain";
    }
    
    let offset = 0;
    const BUFFER_SIZE = chunk_size;
    if(file.size > BUFFER_SIZE * 10000){
        $('button[id="upload_button"]').get(0).disabled = false
        $('input[id="upload_file_area"]').get(0).disabled = false
        showErrorMsg(errorMsgList.get(6).value)
        uploadStatus_p.innerText = "Error"
        return;
    }

    uploadStatus_p.innerText = "Initializing..."
    
    let file_id;
    let uri;
    const xhr = new XMLHttpRequest();

    xhr.onerror = function(){
        $('button[id="upload_button"]').get(0).disabled = false
        $('input[id="upload_file_area"]').get(0).disabled = false
        showErrorMsg(errorMsgList.get(5).value)
        uploadStatus_p.innerText = "Error"
    }

    if(uploadId === ""){
        xhr.open("POST", "https://" + host + "/api/largeFileUpload/createFileInstance?size=" + file.size, false);
        xhr.send();

        if(xhr.status != 200){
            $('button[id="upload_button"]').get(0).disabled = false
            $('input[id="upload_file_area"]').get(0).disabled = false
            showErrorMsg(errorMsgList.get(5).value)
            uploadStatus_p.innerText = "Error"
            return;
        }

        file_id = xhr.responseText;
        uri = "/" + file_id.slice(0,2) + "/" + file_id.slice(2,4) + "/" + file_id.slice(4) + "/data";

        xhr.open('POST', "https://" + host + "/initiateMultipartUpload" + uri + "?uploads", false);
        xhr.send();
        uploadId = xhr.responseText.match(/\<UploadId\>.*\<\/UploadId\>/)[0].replaceAll(/\<(.*?UploadId)\>/g, "");
        uploadId_p.innerText = uploadId;

        if(xhr.status != 200){
            $('button[id="upload_button"]').get(0).disabled = false
            $('input[id="upload_file_area"]').get(0).disabled = false
            showErrorMsg(errorMsgList.get(5).value)
            uploadStatus_p.innerText = "Error"
            return;
        }

        xhr.open("POST", "https://" + host + "/api/largeFileUpload/createMultipartObjectInstance?upload_id=" + uploadId + "&file_id=" + file_id + "&key=" + FILE_NAME + "&size=" + file.size + "&chunk_size=" + BUFFER_SIZE, false);
        xhr.send();

        if(xhr.status != 200){
            $('button[id="upload_button"]').get(0).disabled = false
            $('input[id="upload_file_area"]').get(0).disabled = false
            showErrorMsg(errorMsgList.get(5).value)
            uploadStatus_p.innerText = "Error"
            return;
        }

        file_id = xhr.responseText;
    }else{
        xhr.open("POST", "https://" + host + "/api/largeFileUpload/checkMultipartObjectInstance?upload_id=" + uploadId, false);
        xhr.send();

        if(xhr.status != 200){
            $('button[id="upload_button"]').get(0).disabled = false
            $('input[id="upload_file_area"]').get(0).disabled = false
            showErrorMsg(xhr.responseText)
            uploadStatus_p.innerText = "Error"
            return;
        }

        if(BUFFER_SIZE != parseInt(JSON.parse(xhr.responseText)["chunk_size"])){
            $('button[id="upload_button"]').get(0).disabled = false
            $('input[id="upload_file_area"]').get(0).disabled = false
            showErrorMsg(errorMsgList.get(4).value)
            uploadStatus_p.innerText = "Error"
            return;
        }
        file_id = JSON.parse(xhr.responseText)["file_id"]
    }

    xhr.open("POST", "https://" + host + "/api/largeFileUpload/lock_upload_id?upload_id=" + uploadId, false);
    xhr.send();

    if(xhr.status != 200){
        $('button[id="upload_button"]').get(0).disabled = false
        $('input[id="upload_file_area"]').get(0).disabled = false
        showErrorMsg(errorMsgList.get(5).value)
        uploadStatus_p.innerText = "Error"
        return;
    }

    xhr.onerror = function(){
        console.log("Error");
        $('button[id="upload_button"]').get(0).disabled = false
        $('input[id="upload_file_area"]').get(0).disabled = false
        showErrorMsg(errorMsgList.get(5).value)
        for(const x of xhrList){
            x.abort();
        }
        uploadStatus_p.innerText = "Error"
        xhr.open("POST", "https://" + host + "/api/largeFileUpload/unlock_upload_id?upload_id=" + uploadId, false);
        xhr.send();
    }

    uri = "/" + file_id.slice(0,2) + "/" + file_id.slice(2,4) + "/" + file_id.slice(4) + "/data";

    let numOfPart = 0;
    if(file.size % BUFFER_SIZE === 0){
        numOfPart = parseInt(file.size / BUFFER_SIZE);
    }else{
        numOfPart = parseInt(file.size / BUFFER_SIZE) + 1; 
    }
    console.log(numOfPart);

    let doc = document.implementation.createDocument(null, null);
    let compTag = doc.createElement("CompleteMultipartUpload");
    compTag.tagName = "CompleteMultipartUpload";
    doc.append(compTag);

    const object_name = uri;

    function up(threads) {
        let partNumber = threads - 1;
        let xhrStateList = [];
        let xhrList = [];

        function cmpMultipartUpload() { 
            uploadStatus_p.innerText = "Processing..."
            xhr.open('POST', "https://" + host + "/completeMultipartUpload" + object_name + "?uploadId=" + uploadId, false);
            xhr.send(doc);

            if(xhr.status != 200){
                $('button[id="upload_button"]').get(0).disabled = false
                $('input[id="upload_file_area"]').get(0).disabled = false
                showErrorMsg(errorMsgList.get(5).value)
                uploadStatus_p.innerText = "Error"
                xhr.open("POST", "https://" + host + "/api/largeFileUpload/unlock_upload_id?upload_id=" + uploadId, false);
                xhr.send();
                return;
            }

            xhr.open('POST', "https://" + host + "/api/largeFileUpload/complete_multipart?upload_id=" + uploadId, false);
            xhr.send();

            if(xhr.status != 200){
                $('button[id="upload_button"]').get(0).disabled = false
                $('input[id="upload_file_area"]').get(0).disabled = false
                showErrorMsg(errorMsgList.get(5).value)
                uploadStatus_p.innerText = "Error"
                xhr.open("POST", "https://" + host + "/api/largeFileUpload/unlock_upload_id?upload_id=" + uploadId, false);
                xhr.send();
                return;
            }

            $('button[id="upload_button"]').get(0).disabled = false
            $('input[id="upload_file_area"]').get(0).disabled = false
            xhr.open("POST", "https://" + host + "/api/largeFileUpload/unlock_upload_id?upload_id=" + uploadId, false);
            xhr.send();
            uploadStatus_p.innerText = "Complete"
        }

        async function xhrInitialize(indexNum){
            let lxhr = new XMLHttpRequest();
            xhrList[indexNum] = lxhr;
            let currentNum = indexNum;
            let bodyHash;
            let retryCount = 0;
            let partfile = file.slice(offset, offset + BUFFER_SIZE, contentType)
            offset += BUFFER_SIZE;

            async function uploadPart(object_name, partNum) {
                xhrStateList[indexNum] = XMLHttpRequest.OPENED;
                partfile.arrayBuffer().then(buf => {
                    getHash(undefined, buf).then(hash => {
                        bodyHash = hash
                        const xhr1 = new XMLHttpRequest();
                        xhr1.open("GET", "https://" + host + "/api/largeFileUpload/part?part_number=" + (partNum+1) +"&upload_id=" + uploadId, false);
                        xhr1.send();

                        if(xhr1.status != 200){
                            $('button[id="upload_button"]').get(0).disabled = false
                            $('input[id="upload_file_area"]').get(0).disabled = false
                            showErrorMsg(errorMsgList.get(5).value)
                            for(const x of xhrList){
                                x.abort();
                            }
                            uploadStatus_p.innerText = "Error"
                            xhr.open("POST", "https://" + host + "/api/largeFileUpload/unlock_upload_id?upload_id=" + uploadId, false);
                            xhr.send();
                            return;
                        }

                        if(xhr1.responseText === ""){
                            lxhr.open('PUT', "https://" + host + "/uploadPart" + object_name + "?partNumber=" + (partNum + 1) + "&uploadId=" + uploadId, true);
                            lxhr.setRequestHeader('Content-type', contentType);
                            lxhr.setRequestHeader("bodyHash", bodyHash);
                            lxhr.send(partfile);
                        }else{
                            if(xhr1.responseText === bodyHash){ 
                                uploadStatus_p.innerText = (parseInt((partNumber / numOfPart) * 100)).toString() + "%";
                                if(partNumber < numOfPart - 1){
                                    partNumber += 1;
                                    currentNum = partNumber;
                                    partfile = file.slice(offset, offset + BUFFER_SIZE, contentType)
                                    offset += BUFFER_SIZE;
                                    uploadPart(object_name, currentNum);
                                } else if (xhrStateList.filter((xhr) => xhr === XMLHttpRequest.DONE).length === xhrStateList.length) {
                                    cmpMultipartUpload();
                                }
                            }else{
                                $('button[id="upload_button"]').get(0).disabled = false
                                $('input[id="upload_file_area"]').get(0).disabled = false
                                showErrorMsg(errorMsgList.get(3).value)
                                for(const x of xhrList){
                                    x.abort();
                                }
                                uploadStatus_p.innerText = "Error"
                                xhr.open("POST", "https://" + host + "/api/largeFileUpload/unlock_upload_id?upload_id=" + uploadId, false);
                                xhr.send();
                            }
                        }
                    })
                })
            };

            lxhr.onerror = function(){
                if(retryCount < retry_count){
                    retryCount += 1;
                    uploadPart(object_name, currentNum);
                }else{
                    console.log("Error");
                    $('button[id="upload_button"]').get(0).disabled = false
                    $('input[id="upload_file_area"]').get(0).disabled = false
                    showErrorMsg(errorMsgList.get(5).value)
                    for(const x of xhrList){
                        x.abort();
                    }
                    uploadStatus_p.innerText = "Error"
                    xhr.open("POST", "https://" + host + "/api/largeFileUpload/unlock_upload_id?upload_id=" + uploadId, false);
                    xhr.send();
                }
            }

            lxhr.onreadystatechange = function(){
                xhrStateList[indexNum] = lxhr.readyState;
            }

            lxhr.onload = function() {
                if(lxhr.status != 200){
                    if(retryCount < retry_count){
                        retryCount += 1;
                        uploadPart(object_name, currentNum);
                    }else{
                        console.log("Error");
                        $('button[id="upload_button"]').get(0).disabled = false
                        $('input[id="upload_file_area"]').get(0).disabled = false
                        showErrorMsg(errorMsgList.get(5).value)
                        for(const x of xhrList){
                            x.abort();
                        }
                        uploadStatus_p.innerText = "Error"
                        xhr.open("POST", "https://" + host + "/api/largeFileUpload/unlock_upload_id?upload_id=" + uploadId, false);
                        xhr.send();
                    }
                }else{
                    retryCount = 0;
                    uploadStatus_p.innerText = (parseInt((partNumber / numOfPart) * 100)).toString() + "%";
                    let partTag = doc.createElement("Part");

                    let partNumTag = doc.createElement("PartNumber");
                    partNumTag.textContent = currentNum + 1;
                    partTag.append(partNumTag);

                    let eTag = doc.createElement("ETag");
                    eTag.textContent = lxhr.getResponseHeader("ETag");
                    partTag.append(eTag);
        
                    compTag.append(partTag);
                    
                    const xhr2 = new XMLHttpRequest();
                    xhr2.open("POST", "https://" + host + "/api/largeFileUpload/part?part_number=" + (currentNum+1) + "&upload_id=" + uploadId + "&check_sum=" + bodyHash + "&ETag=" + lxhr.getResponseHeader("ETag"), false);
                    xhr2.send();

                    if(xhr2.status != 200){
                        $('button[id="upload_button"]').get(0).disabled = false
                        $('input[id="upload_file_area"]').get(0).disabled = false
                        showErrorMsg(errorMsgList.get(5).value)
                        for(const x of xhrList){
                            x.abort();
                        }
                        uploadStatus_p.innerText = "Error"
                        xhr.open("POST", "https://" + host + "/api/largeFileUpload/unlock_upload_id?upload_id=" + uploadId, false);
                        xhr.send();
                        return;
                    }

                    if(partNumber < numOfPart - 1){
                        partNumber += 1;
                        currentNum = partNumber;
                        partfile = file.slice(offset, offset + BUFFER_SIZE, contentType);
                        offset += BUFFER_SIZE;
                        uploadPart(object_name, currentNum);
                    } else if (xhrStateList.filter((xhr) => xhr === XMLHttpRequest.DONE).length === xhrStateList.length) {
                        cmpMultipartUpload();
                    }
                }
            }
        
            uploadPart(object_name, indexNum);
        }

        for(let i = 0; i < threads; i++){
            xhrInitialize(i);
        }
    }

    up(Math.min(2, numOfPart));
}