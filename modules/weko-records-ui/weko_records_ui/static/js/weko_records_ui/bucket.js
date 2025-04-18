async function openBucketCopyModal() {
  $('#bucket_copy_modal').modal('show');
  $('#modal-guide').hide();
  $('#modal-message').text('loading...');
  $('.options-list').empty();
  $('#execution').prop("disabled", true);
  $('#modal-result-message').text('');
  $('#modal-result-uri').text('');
  $('creating_bucket_name').text('');

  url ="/records/get_bucket_list";
  await fetch(url ,{method:'GET' ,headers:{'Content-Type':'application/json'} ,credentials:"include"})
  .then(res => {
    if (!res.ok) {
      return res.json().then(errorData => {
          throw new Error(errorData.error);
      });
    }
    return res.json();
  })
  .then((result) => {
    $('.options-list').empty();
    result.forEach(function(bucket_name) {
        const newLi = $('<li>').text(bucket_name);
        $('.options-list').append(newLi);
    });
  })
  .catch(error => {
    alert(error);
  });
  $('#modal-message').text('');
  $('#modal-guide').show();
  $('#execution').prop("disabled", false);
  document.querySelectorAll('.options-list li').forEach(option => {
    option.addEventListener('click', function() {
      console.log(this.textContent);
      document.getElementById('search').value = this.textContent; // 選択したオプションのテキストを入力ボックスに設定
      document.querySelector('.options-list').style.display = 'none'; // オプションリストを非表示にする
    });
  });

}

document.getElementById('search').addEventListener('input', function() {
  const filter = this.value.toLowerCase();
  const options = document.querySelectorAll('.options-list li');

  options.forEach(option => {
      if (option.textContent.toLowerCase().includes(filter)) {
          option.style.display = 'block';
      } else {
          option.style.display = 'none';
      }
  });
});

// 入力ボックスがフォーカスされたときにオプションリストを表示
document.getElementById('search').addEventListener('focus', function() {
  document.querySelector('.options-list').style.display = 'block';
});

// オプションリストのアイテムがクリックされたときの処理
const options = document.querySelectorAll('.options-list li');
options.forEach(option => {
  option.addEventListener('mousedown', function(event) {
      // クリックされたオプションの値を入力ボックスに設定
      document.getElementById('search').value = this.textContent;

      // オプションリストを非表示にする
      document.querySelector('.options-list').style.display = 'none';
  });
});

async function copyFileToBucket() {
  $('#execution').prop("disabled", true);
  $('#modal-result-message').text('executing...');

  const copy_success_message = document.getElementById('copy_success_message').value
  const pid = document.getElementById('pid').value
  const filename = document.getElementById('txt_filename').value
  const bucket_id = document.getElementById('bucket_id_value').value
  const checked =  $('input[name=bucket_option]:checked').val()
  let bucket_name = ''
  if (checked == 'select') {
    bucket_name = document.getElementById('search').value
  } else {
    bucket_name = document.getElementById('creating_bucket_name').value
  }
  if (bucket_name == '') {
    alert('Please select or input bucket.');
    return;
  }

  const form = {
    'pid': pid,
    'bucket_id': bucket_id,
    'filename': filename,
    'checked': checked,
    'bucket_name': bucket_name,
  }
  url ="/records/copy_bucket";
  await fetch(url ,{method:'POST' ,headers:{'Content-Type':'application/json'} ,credentials:"include", body: JSON.stringify(form)})
  .then(res => {
    if (!res.ok) {
      return res.json().then(errorData => {
          throw new Error(errorData.error);
      });
    }
    return res.json();
  })
  .then(result => {
    $('#modal-result-message').text(copy_success_message);
    $('#modal-result-uri').text(result);
  })
  .catch(error => {
    $('#modal-result-message').text('');
    $('#modal-result-uri').text('');
    alert(error.message);
  });
  $('#execution').prop("disabled", false);
}


function replaceFile() {
  document.getElementById('fileInput').click();
}
document.getElementById('fileInput').addEventListener('change', async function(event) {
  $('#loading').show();

  const file = event.target.files[0];
  document.getElementById('fileInput').click();
  const pid = document.getElementById('pid').value
  const bucket_id = document.getElementById('bucket_id_value').value;
  const txt_filename = document.getElementById('txt_filename').value;
  const select_same_named_message = document.getElementById('select_same_named_message').value;
  const record_url = document.getElementById('txt_record_url').value;
  const file_replacement_successful_message = document.getElementById('file_replacement_successful').value;
  const replacing_file_failed = document.getElementById('replacing_file_failed').value;

  let return_file_place = null;
  let return_s3_uri = null;
  let return_bucket_id = null;
  let return_version_id = null;

  if (file) {
    if (file.name !== txt_filename) {
      alert(select_same_named_message);
      $('#loading').hide();
      return;
    }
    const formData = new FormData();
    formData.append('pid', pid);
    formData.append('bucket_id', bucket_id);
    formData.append('file_name', file.name);
    url ="/records/get_file_place";

    await fetch(url ,{method:'POST', credentials:"include", body: formData})
    .then(res => {
      if (!res.ok) {
        return res.json().then(errorData => {
            throw new Error(errorData.error);
        });
      }
      return res.json();
    })
    .then(result => {
      console.log(result);
      return_file_place = result.file_place
      return_s3_uri = result.uri;
      return_bucket_id = result.bucket_id;
      return_version_id = result.version_id;
    })
    .catch(error => {
      alert(replacing_file_failed + error.message);
      $('#loading').hide();
      return;
    });

    console.log('return_file_place:', return_file_place);
    const formData_second = new FormData();
    url ="/records/replace_file";

    if(return_file_place == "S3"){
      // S3 strage
      const signedUrl = return_s3_uri; // サーバーサイドで生成された署名付きURL
      await uploadFileToS3(file, signedUrl);

      const checksum = await calculateChecksum(file);
      formData_second.append('return_file_place', return_file_place);
      formData_second.append('pid', pid);
      formData_second.append('bucket_id', bucket_id);
      formData_second.append('file_name', file.name);
      formData_second.append('file_size', file.size);
      formData_second.append('file_checksum', checksum);
      formData_second.append('new_bucket_id', return_bucket_id);
      formData_second.append('new_version_id', return_version_id);

      await fetch(url ,{method:'POST', credentials:"include", body: formData_second})
      .then(res => {
        if (!res.ok) {
          return res.json().then(errorData => {
              throw new Error(errorData.error);
          });
        }
        return res.json();
      })
      .then(result => {
        alert(file_replacement_successful_message);
        window.location = record_url;
      })
      .catch(error => {
        alert(replacing_file_failed + error.message);
        $('#loading').hide();
      });

    } else {
      // weko local strage
      formData_second.append('return_file_place', return_file_place);
      formData_second.append('pid', pid);
      formData_second.append('bucket_id', bucket_id);
      formData_second.append('file', file);
      formData_second.append('file_name', file.name);
      formData_second.append('file_size', file.size);

      await fetch(url ,{method:'POST', credentials:"include", body: formData_second})
      .then(res => {
        if (!res.ok) {
          return res.json().then(errorData => {
              throw new Error(errorData.error);
          });
        }
        return res.json();
      })
      .then(result => {
        alert(file_replacement_successful_message);
        window.location = record_url;
      })
      .catch(error => {
        alert(replacing_file_failed + error.message);
        $('#loading').hide();
      });
    }
  }
});

async function calculateChecksum(file) {
  const arrayBuffer = await file.arrayBuffer();
  const hashBuffer = await crypto.subtle.digest('SHA-256', arrayBuffer);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  const hashHex = hashArray.map(b => ('00' + b.toString(16)).slice(-2)).join('');
  return hashHex;
}

// XMLHttpRequestをPromiseでラップする関数
function uploadFileToS3(file, signedUrl) {
  return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      xhr.open('PUT', signedUrl, true);
      xhr.setRequestHeader('Content-Type', 'binary/octet-stream');

      xhr.onload = () => {
          if (xhr.status === 200) {
              console.log('File uploaded successfully');
              resolve();
          } else {
              console.error('Error uploading file:', xhr.statusText);
              alert(replacing_file_failed);
              reject(new Error(xhr.statusText));
          }
      };

      xhr.onerror = () => {
          reject(new Error('Network error'));
      };
      xhr.send(file);
  });
}
