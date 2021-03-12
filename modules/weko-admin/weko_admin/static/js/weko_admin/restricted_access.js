const {useState, useEffect} = React;
const CONTENT_FILE_DOWNLOAD_LABEL = document.getElementById('content_file_download_label').value;
const DOWNLOAD_LIMIT_LABEL = document.getElementById('download_limit_label').value;
const EXPIRATION_DATE_LABEL = document.getElementById('expiration_date_label').value;
const UNLIMITED_LABEL = document.getElementById('unlimited_label').value;
const SAVE_LABEL = document.getElementById('save_label').value;
const CHECK_INPUT_DOWNLOAD = document.getElementById('check_input_download').value;
const CHECK_INPUT_EXPIRATION_DATE = document.getElementById('check_input_expiration_date').value;
const EMPTY_DOWNLOAD = document.getElementById('empty_download').value;
const EMPTY_EXPIRATION_DATE = document.getElementById('empty_expiration_date').value;
const MAX_DOWNLOAD_LIMIT = 2147483647;
const MAX_EXPIRATION_DATE = 999999999;

(function () {
  let initValue = document.getElementById('init_data').value;
  initValue = JSON.parse(initValue);

  ReactDOM.render(
    <RestrictedAccessLayout {...initValue} />,
    document.getElementById('root')
  )

})();

function ContentFileDownloadLayout({value, setValue}) {
  const style = {marginRight: "5px", marginLeft: "15px"}
  const {
    download_limit,
    download_limit_unlimited_chk,
    expiration_date,
    expiration_date_unlimited_chk
  } = value;

  function handleChange(event) {
    event.preventDefault();
    let target = event.target;
    let key = target.id;
    let updateValue = target.type === 'checkbox' ? target.checked : target.value;

    if (target.type !== 'checkbox') {
      if (!event.target.validity.valid) {
        updateValue = value[key];
      }
    }
    setValue({...value, ...{[key]: updateValue}});
  }

  return (
    <div>
      <div className="row">
        <div className="col-sm-12 col-md-12 col-md-12">
          <div className="panel panel-default">
            <div className="panel-heading">
              <h5><strong>{CONTENT_FILE_DOWNLOAD_LABEL}</strong></h5>
            </div>
            <div className="panel-body">
              <div className="form-group">
                <label
                  className="col-sm-2 text-right">{EXPIRATION_DATE_LABEL}</label>
                <input type="text" id="expiration_date" className="col-sm-2"
                       value={expiration_date}
                       onChange={handleChange}
                       pattern="[0-9]*"
                       maxLength={10}
                       disabled={expiration_date_unlimited_chk}
                />
                <label htmlFor="expiration_date_unlimited_chk"
                       className="text-left">
                  <input type="checkbox" style={style}
                         id="expiration_date_unlimited_chk"
                         key={Math.random()}
                         checked={expiration_date_unlimited_chk}
                         onChange={handleChange}/>
                  &nbsp; {UNLIMITED_LABEL}
                </label>
              </div>
              <div className="form-inline">
                <label
                  className="col-sm-2 text-right">{DOWNLOAD_LIMIT_LABEL}</label>
                <input type="text" id="download_limit" className="col-sm-2"
                       onChange={handleChange}
                       disabled={download_limit_unlimited_chk}
                       value={download_limit}/>
                <label htmlFor="download_limit_unlimited_chk"
                       className="text-left">
                  <input type="checkbox" style={style}
                         id="download_limit_unlimited_chk"
                         key={Math.random()}
                         checked={download_limit_unlimited_chk}
                         onClick={handleChange}/>
                  {UNLIMITED_LABEL}
                </label>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )

}

function RestrictedAccessLayout({content_file_download}) {
  const [contentFileDownload, setContentFileDownload] = useState(content_file_download);

  function handleSave() {
    const URL = "/api/admin/restricted_access/save";
    let errorMessage = validateContentFileDownload();
    if (errorMessage) {
      showErrorMessage(errorMessage);
      return false;
    }

    let data = {
      content_file_download: contentFileDownload,
    }
    $.ajax({
      url: URL,
      method: 'POST',
      contentType: 'application/json',
      dataType: 'json',
      data: JSON.stringify(data),
      success: function (result) {
        if (result.status) {
          addAlert(result.msg);
        } else {
          addAlert(result.msg);
        }
      },
      error: function (error) {
        console.log(error);
      }
    });
  }

  function validateContentFileDownload() {
    const {
      download_limit,
      download_limit_unlimited_chk,
      expiration_date,
      expiration_date_unlimited_chk
    } = contentFileDownload;

    let errorMessage;

    if (expiration_date === "" && !expiration_date_unlimited_chk) {
      errorMessage = EMPTY_EXPIRATION_DATE;
    } else if (download_limit === "" && !download_limit_unlimited_chk) {
      errorMessage = EMPTY_DOWNLOAD;
    } else if ((expiration_date < 1 && !expiration_date_unlimited_chk)
      || expiration_date > MAX_EXPIRATION_DATE) {
      errorMessage = CHECK_INPUT_EXPIRATION_DATE;
    } else if ((download_limit < 1 && !download_limit_unlimited_chk)
      || download_limit > MAX_DOWNLOAD_LIMIT) {
      errorMessage = CHECK_INPUT_DOWNLOAD;
    }

    return errorMessage;
  }

  return (
    <div>
      <ContentFileDownloadLayout value={contentFileDownload}
                                 setValue={setContentFileDownload}/>
      <div className="form-group">
        <button id="save-btn" className="btn btn-primary pull-right"
                onClick={handleSave}>
          <span className="glyphicon glyphicon-save"></span>&nbsp;{SAVE_LABEL}
        </button>
      </div>
    </div>
  )
}

function showErrorMessage(errorMessage) {
  $("#inputModal").html(errorMessage);
  $("#allModal").modal("show");
}

function addAlert(message) {
  $('#alerts').append(
    '<div class="alert alert-light" id="alert-style">' +
    '<button type="button" class="close" data-dismiss="alert">' +
    '&times;</button>' + message + '</div>');
}
