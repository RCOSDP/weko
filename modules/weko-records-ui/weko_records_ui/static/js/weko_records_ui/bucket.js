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
  .then(res => res.json())
  .then((result) => {
    $('.options-list').empty();
    result.forEach(function(bucket_name) {
        const newLi = $('<li>').text(bucket_name);
        $('.options-list').append(newLi);
    });
  })
  .catch(error => {
    console.log(error);
    alert('failed getting Bucket.');
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

// 入力ボックスからフォーカスが外れたときにオプションリストを非表示にする
document.getElementById('search').addEventListener('blur', function() {
  setTimeout(() => {
      document.querySelector('.options-list').style.display = 'none';
  }, 400); // 少し遅延を入れて、クリックイベントが処理されるのを待つ
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
  const file = event.target.files[0];
  document.getElementById('fileInput').click();
  const pid = document.getElementById('pid').value
  const bucket_id = document.getElementById('bucket_id_value').value
  const txt_filename = document.getElementById('txt_filename').value
  const select_same_named_message = document.getElementById('select_same_named_message').value
  const record_url = document.getElementById('txt_record_url').value
  const file_replacement_successful_message = document.getElementById('file_replacement_successful').value

  if (file) {
    if (file.name !== txt_filename) {
      alert(select_same_named_message);
      return;
    }
    const formData = new FormData();
    formData.append('pid', pid);
    formData.append('bucket_id', bucket_id);
    formData.append('file', file);
    url ="/records/replace_file";

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
      alert(file_replacement_successful_message);
      window.location = record_url;
    })
    .catch(error => {
      alert(error.message);
    });
  }

});
