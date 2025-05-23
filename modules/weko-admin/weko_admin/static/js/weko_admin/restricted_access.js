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
const EMPTY_ERROR_MESSAGE = document.getElementById('empty_error_message').value;
const USAGE_REPORT_WORKFLOW_ACCESS_LABEL = document.getElementById('usage_report_workflow_access_label').value
const MAXINT = Number(document.getElementById('maxint').value)
const MAX_DOWNLOAD_LIMIT = MAXINT;
const MAX_EXPIRATION_DATE = MAXINT;

const MESSAGE_MISSING_DATA = document.getElementById('message_miss_data').value;
const LABEL_ENGLISH = document.getElementById("english").value;
const LABEL_JAPANESE = document.getElementById("japanese").value;
const LABEL_NEW = document.getElementById("new").value;
const LABEL_TERMS_AND_CONDITIONS = document.getElementById("terms_and_conditions").value;

const CONST_DEFAULT_ITEMS_PER_PAGE =parseInt(document.getElementById('const_items_per_page').value);
const LABEL_ACTIVITY = document.getElementById('label_activity').value;
const LABEL_ITEMS = document.getElementById("label_items").value;
const LABEL_WORKFLOW = document.getElementById("label_workflow").value;
const LABEL_STATUS = document.getElementById("label_status").value;
const LABEL_USER = document.getElementById("label_user").value;
const LABEL_CONFIRM = document.getElementById("label_confirm").value;
const LABEL_CLOSE = document.getElementById("label_close").value;
const LABEL_SEND = document.getElementById("label_send_mail").value;
const LABEL_USAGE_REPORT_REMINDER_MAIL = document.getElementById("label_usage_report_reminder_mail").value;
const LABEL_ACTION_DOING = document.getElementById("label_action_doing").value;
const MSG_SEND_MAIL_SUCCESSFUL = document.getElementById("msg_sent_success").value;
const MSG_SEND_MAIL_FAILED = document.getElementById("msg_sent_failed").value;
const LABEL_SECRET_URL_DOWNLOAD = document.getElementById("label_secret_url_download").value;
const LABEL_SECRET_URL_ENABLED = document.getElementById("label_secret_url_enabled").value;
const LABEL_ERROR_MESSAGE = document.getElementById("error_message").value;

const EMPTY_TERM = {
  key: '',
  content:
    {
      "en": {
        "title": "",
        "content": ""
      },
      "ja": {
        "title": "",
        "content": ""
      }
    }
};
(function () {
  let initValue = document.getElementById('init_data').value;
  initValue = JSON.parse(initValue);

  ReactDOM.render(
    <RestrictedAccessLayout {...initValue} />,
    document.getElementById('root')
  )

})();

function InputComponent({
                          label,
                          currentValue,
                          checkboxValue,
                          value,
                          setValue,
                          inputId,
                          checkboxId,
                          disabledAll=false
                        }) {
  const style = {marginRight: "5px", marginLeft: "15px"}

  function handleChange(event) {
    event.preventDefault();
    let target = event.target;
    let key = target.id;
    let updateValue = target.type === 'checkbox' ? target.checked : target.value;

    if (target.type !== 'checkbox') {
      if (!event.target.validity.valid) {
        updateValue = value[key];
      }
      if (isNaN(updateValue)) {
        try {
          updateValue = parseInt(updateValue);
        } catch (e) {
          console.log(e);
        }
      }
    }
    setValue({...value, ...{[key]: updateValue}});
  }

  return (
    <div className="form-inline">
      <label htmlFor={inputId} className="col-sm-2 text-right">{label}</label>
      <input type="text" id={inputId} className="col-sm-2"
             value={currentValue}
             onChange={handleChange}
             pattern="[0-9]*"
             maxLength={String(MAXINT).length}
             disabled={checkboxValue || disabledAll}
      />
      <label htmlFor={checkboxId}
             className="text-left">
        <input type="checkbox"
               style={style}
               id={checkboxId}
               key={Math.random()}
               checked={checkboxValue}
               onChange={handleChange}
               disabled={disabledAll}/>
        {UNLIMITED_LABEL}
      </label>
    </div>
  )
}

function SecretURLFileDownloadLayout({value, setValue}) {
  const {
    secret_download_limit,
    secret_download_limit_unlimited_chk,
    secret_expiration_date,
    secret_expiration_date_unlimited_chk,
    secret_enable
  } = value;

  const style = {marginRight: "5px", marginLeft: "15px"}
  let checkboxValue = secret_enable;
  let disabledAll = !checkboxValue;

  function handleChange(event) {
    event.preventDefault();
    let target = event.target;
    let key = target.id;
    checkboxValue = target.checked
    disabledAll = !checkboxValue;
    setValue({...value, ...{[key]: checkboxValue}});
  }

  return (
    <div>
      <div className="row">
        <div className="col-sm-12 col-md-12 col-md-12">
          <div className="panel panel-default">
            <div className="panel-heading">
              <h5><strong>{LABEL_SECRET_URL_DOWNLOAD}</strong></h5>
            </div>
            <div className="panel-body">
              {/* start enabled checkbox */}
              <div className="form-inline">
                <label htmlFor="secret_enable" className="text-left">
                  <input type="checkbox"
                    style={style}
                    id="secret_enable"
                    key={Math.random()}
                    checked={checkboxValue}
                    onChange={handleChange}/>
                    {LABEL_SECRET_URL_ENABLED}
                </label>
              </div>
              {/* end enabled checkbox */}
              <InputComponent
                label={EXPIRATION_DATE_LABEL}
                currentValue={secret_expiration_date}
                checkboxValue={secret_expiration_date_unlimited_chk}
                inputId="secret_expiration_date"
                checkboxId="secret_expiration_date_unlimited_chk"
                value={value}
                setValue={setValue}
                disabledAll={disabledAll}
              />
              <InputComponent
                label={DOWNLOAD_LIMIT_LABEL}
                currentValue={secret_download_limit}
                checkboxValue={secret_download_limit_unlimited_chk}
                inputId="secret_download_limit"
                checkboxId="secret_download_limit_unlimited_chk"
                value={value}
                setValue={setValue}
                disabledAll={disabledAll}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function ContentFileDownloadLayout({value, setValue}) {
  const {
    download_limit,
    download_limit_unlimited_chk,
    expiration_date,
    expiration_date_unlimited_chk
  } = value;

  return (
    <div>
      <div className="row">
        <div className="col-sm-12 col-md-12 col-md-12">
          <div className="panel panel-default">
            <div className="panel-heading">
              <h5><strong>{CONTENT_FILE_DOWNLOAD_LABEL}</strong></h5>
            </div>
            <div className="panel-body">
              <InputComponent
                label={EXPIRATION_DATE_LABEL}
                currentValue={expiration_date}
                checkboxValue={expiration_date_unlimited_chk}
                inputId="expiration_date"
                checkboxId="expiration_date_unlimited_chk"
                value={value}
                setValue={setValue}
              />
              <InputComponent
                label={DOWNLOAD_LIMIT_LABEL}
                currentValue={download_limit}
                checkboxValue={download_limit_unlimited_chk}
                inputId="download_limit"
                checkboxId="download_limit_unlimited_chk"
                value={value}
                setValue={setValue}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function UsageReportWorkflowAccessLayout({value, setValue}) {
  const {expiration_date_access, expiration_date_access_unlimited_chk} = value
  return (
    <div>
      <div className="row">
        <div className="col-sm-12 col-md-12 col-md-12">
          <div className="panel panel-default">
            <div className="panel-heading">
              <h5><strong>{USAGE_REPORT_WORKFLOW_ACCESS_LABEL}</strong></h5>
            </div>
            <div className="panel-body">
              <InputComponent
                label={EXPIRATION_DATE_LABEL}
                currentValue={expiration_date_access}
                checkboxValue={expiration_date_access_unlimited_chk}
                inputId="expiration_date_access"
                checkboxId="expiration_date_access_unlimited_chk"
                value={value}
                setValue={setValue}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function TermsList({termList, setTermList, currentTerm, setCurrentTerm}) {

  function handleOnTermClick(e) {
    e.preventDefault();
    // Set current term whenever an element is clicked
    if (currentTerm === undefined || e.target.id !== currentTerm['key']) {
      let newCurrentTerm;
      newCurrentTerm = JSON.parse(JSON.stringify(termList.find(term => term['key'] === e.target.id)));
      newCurrentTerm.existed = true;
      setCurrentTerm(newCurrentTerm);
    }
  }

  function handleCreateNewTerm(event) {
    console.log("handleCreateNewTerm");
    event.preventDefault();
    let newTerm = JSON.parse(JSON.stringify(EMPTY_TERM));
    newTerm['existed'] = true;
    setCurrentTerm(newTerm);
  }

  function handleRemoveTerm(event) {
    event.preventDefault();
    setTermList(termList.filter(t => t.key !== event.target.id));
    let newTerm = JSON.parse(JSON.stringify(EMPTY_TERM));
    setCurrentTerm(newTerm)
  }

  return (
    <div className='row'>
      <div className="col col-md-12">
        <div className="panel-default">
          <div className="col col-md-12 both scrollbar margin-top padding-top"
               id="sltBoxListEmail">
            {
              termList.map((term) => (
                <li className="tree-list" key={term.key}>
                  <a
                    className={`list-group-item list-group-item-action ${currentTerm !== undefined && currentTerm.key === term.key ? 'active' : ''}`}
                    onClick={handleOnTermClick}
                    id={term.key}>{term.content.en.title}
                  </a>
                  <a
                    className="glyphicon glyphicon-remove glyphicon-remove-term pull-right"
                    id={term.key}
                    key={term.key} onClick={handleRemoveTerm}/>
                </li>
              ))
            }

            <button className="btn btn-light add-button btn-add"
                    style={{marginTop: "10px"}} id="new_term"
                    onClick={handleCreateNewTerm}>
              <span class="glyphicon glyphicon-plus">
              </span>{LABEL_NEW}</button>
          </div>
        </div>
      </div>
    </div>
  )
}

function TermDetail({currentTerm, setCurrentTerm}) {
  const {en, ja} = currentTerm.content;

  function handleOnInputChanged(event, key) {
    event.preventDefault();
    let oldContent;
    let content;

    oldContent = currentTerm.content[key];
    oldContent[event.target.name] = event.target.value;
    content = {...currentTerm.content, ...{[key]: oldContent}};
    setCurrentTerm({...currentTerm, content: content})
  }

  return (
    <div style={{paddingRight: '15px'}}>
      <div className="form-group row margin-top">
        <label htmlFor="staticEmail"
               className="col-sm-2 col-form-label"
               style={{textAlign: 'right'}}>{LABEL_JAPANESE}</label>
        <div className="col-sm-10">
          <input type="text" className="form-control"
                 disabled={currentTerm.existed !== true} name="title"
                 value={ja.title}
                 onChange={e => handleOnInputChanged(e, "ja")}/>
        </div>
        <div className="col-sm-12 margin-top">
          <textarea className="form-control textarea_height"
                    disabled={currentTerm.existed !== true} name="content"
                    value={ja.content}
                    onChange={e => handleOnInputChanged(e, "ja")}/>
        </div>
      </div>
      <div className="form-group row margin-top">
        <label htmlFor="staticEmail"
               className="col-sm-2 col-form-label field-required"
               style={{textAlign: 'right'}}>{LABEL_ENGLISH}</label>
        <div className="col-sm-10">
          <input type="text" disabled={currentTerm.existed !== true}
                 className="form-control" name="title" value={en.title}
                 onChange={e => handleOnInputChanged(e, "en")}/>
        </div>
        <div className="col-sm-12 margin-top">
          <textarea className="form-control textarea_height"
                    disabled={currentTerm.existed !== true} name="content"
                    value={en.content}
                    onChange={e => handleOnInputChanged(e, "en")}/>
        </div>
      </div>
    </div>
  )
}

function TermsConditions({termList, setTermList, currentTerm, setCurrentTerm}) {
  return (
    <div>
      <div className="panel panel-default">
        <div className="panel-heading">
          <h5>
            <strong>
              <p>{LABEL_TERMS_AND_CONDITIONS} </p>
            </strong>
          </h5>
        </div>
        <div className="row">
          <div className="col col-md-4">
            <TermsList termList={termList} setTermList={setTermList}
                       currentTerm={currentTerm}
                       setCurrentTerm={setCurrentTerm}/>
          </div>
          <div className="col col-md-8">
            <TermDetail currentTerm={currentTerm}
                        setCurrentTerm={setCurrentTerm}/>
          </div>
        </div>
      </div>
    </div>
  )
}


function ErrorMsgDetail({errorMsg, setErrorMsg}) {
  const {en, ja} = errorMsg.content;

  function InputChanged(event, key) {
    let oldContent;
    let content;

    oldContent = errorMsg.content[key];
    oldContent[event.target.name] = event.target.value;
    content = {...errorMsg.content};
    setErrorMsg({...errorMsg, content})
  }

  return (
    <div>
      <div className="form-group row margin-top">
        <label className="col-sm-2 col-form-label text-right">{LABEL_JAPANESE}</label>
        <div className="col-sm-9">
          <textarea className="form-control textarea"
                    name="content"
                    value={ja.content}
                    onChange={e => InputChanged(e, "ja")}/>
        </div>
      </div>
      <div className="form-group row margin-top">
        <label htmlFor="staticEmail"
               className="col-sm-2 col-form-label text-right">{LABEL_ENGLISH}</label>
        <div className="col-sm-9">
          <textarea className="form-control textarea"
                    name="content"
                    value={en.content}
                    onChange={e => InputChanged(e, "en")}/>
        </div>
      </div>
    </div>  
  )
}

function ErrorMsgConditions({errorMsg, setErrorMsg}) {
  return (
    <div>
      <div className="panel panel-default">
        <div className="panel-heading">
          <h5>
            <strong>
              <p>{LABEL_ERROR_MESSAGE}</p>
            </strong>
          </h5>
        </div>
        <div className="row">
            <ErrorMsgDetail errorMsg={errorMsg} setErrorMsg={setErrorMsg}/>
        </div>
      </div>
    </div>
  )
}


function RestrictedAccessLayout({
                                  secret_URL_file_download,
                                  content_file_download,
                                  terms_and_conditions,
                                  usage_report_workflow_access,
                                  restricted_access_display_flag,
                                  error_msg
                                }) {
  const [secretURLFileDownload , setSecretURLFileDownload] = useState(secret_URL_file_download)
  const [contentFileDownload, setContentFileDownload] = useState(content_file_download);
  const [usageReportWorkflowAccess, setUsageReportWorkflowAccess] = useState(usage_report_workflow_access);
  const [termList, setTermList] = useState(terms_and_conditions);
  const [currentTerm, setCurrentTerm] = useState(EMPTY_TERM);
  const [errorMsg, setErrorMsg] = useState(error_msg);

  function handleApply() {
    let termListClone = [...termList];
    if (!currentTerm.existed) {
      return {
        "valid": true,
        "data": [...JSON.parse(JSON.stringify(termListClone))]
      }
    }

    if (currentTerm.content.en.title.trim() === '' || currentTerm.content.en.content.trim() === '') {
      return {
        "valid": false,
        "data": [...JSON.parse(JSON.stringify(termListClone))]
      }
    }

    if (currentTerm['key'] === '') {
      currentTerm['key'] = (Math.floor(Date.now() / 10)).toString();
      setTermList([...termList, JSON.parse(JSON.stringify(currentTerm))])
      return {
        "valid": true,
        "data": [...termList, JSON.parse(JSON.stringify(currentTerm))]
      }
    } else {
      // for existed term
      termListClone.map((term) => {
        if (term.key === currentTerm.key)
          term["content"] = JSON.parse(JSON.stringify(currentTerm)).content
      });
      setTermList(termListClone)
      return {
        "valid": true,
        "data": [...JSON.parse(JSON.stringify(termListClone))]
      }
    }
  }

  function handleSave() {
    const URL = "/api/admin/restricted_access/save";
    // Validate Secret URL file download.
    let errorMessage = validateSecretURLFileDownload()
    if (errorMessage) {
      showErrorMessage(errorMessage);
      return false;
    }
    // Validate Content file download.
    errorMessage = validateContentFileDownload();
    if (errorMessage) {
      showErrorMessage(errorMessage);
      return false;
    }
    // Validate Usage report workflow access.
    errorMessage = validateUsageReportWorkflowAccess();
    if (errorMessage) {
      showErrorMessage(errorMessage);
      return false;
    }
    // Validate Term and condition
    let terms_data = handleApply();
    if (terms_data["valid"] === false) {
      showErrorMessage(MESSAGE_MISSING_DATA);
      return false;
    }
     //Validate ErrorMsgConditions
     errorMessage = validErrorMsgConditions();
     if(errorMessage){
       showErrorMessage(errorMessage);
       return false;
     } 

    let data = {
      secret_URL_file_download:secretURLFileDownload,
      content_file_download: contentFileDownload,
      usage_report_workflow_access: usageReportWorkflowAccess,
      terms_and_conditions: terms_data["data"],
      error_msg:errorMsg
    }

    $.ajax({
      url: URL,
      method: 'POST',
      contentType: 'application/json',
      dataType: 'json',
      data: JSON.stringify(data),
      success: function (result) {
        if (result.status) {
          addAlert(result.msg, 2);
        } else {
          addAlert(result.msg, 1);
        }
      },
      error: function (error) {
        console.log(error);
      }
    });
  }

  function validateSecretURLFileDownload() {
    const {
      secret_download_limit,
      secret_download_limit_unlimited_chk,
      secret_expiration_date,
      secret_expiration_date_unlimited_chk
    } = secretURLFileDownload;

    let errorMessage;

    if (secret_expiration_date === "" && !secret_expiration_date_unlimited_chk) {
      errorMessage = EMPTY_EXPIRATION_DATE;
    } else if (secret_download_limit === "" && !secret_download_limit_unlimited_chk) {
      errorMessage = EMPTY_DOWNLOAD;
    } else if ((secret_expiration_date < 1 && !secret_expiration_date_unlimited_chk)
      || secret_expiration_date > MAX_EXPIRATION_DATE) {
      errorMessage = CHECK_INPUT_EXPIRATION_DATE;
    } else if ((secret_download_limit < 1 && !secret_download_limit_unlimited_chk)
      || secret_download_limit > MAX_DOWNLOAD_LIMIT) {
      errorMessage = CHECK_INPUT_DOWNLOAD;
    }

    return errorMessage;
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

  function validateUsageReportWorkflowAccess() {
    const {
      expiration_date_access,
      expiration_date_access_unlimited_chk,
    } = usageReportWorkflowAccess;

    let errorMessage;

    if (expiration_date_access === "" && !expiration_date_access_unlimited_chk) {
      errorMessage = EMPTY_EXPIRATION_DATE;
    } else if ((expiration_date_access < 1 && !expiration_date_access_unlimited_chk)
      || expiration_date_access > MAX_EXPIRATION_DATE) {
      errorMessage = CHECK_INPUT_EXPIRATION_DATE;
    }

    return errorMessage;
  }

  function validErrorMsgConditions() {
    let errorMessage;

    if (error_msg.content.en.content == '' || error_msg.content.ja.content == '') {
      errorMessage = EMPTY_ERROR_MESSAGE;
    }
    return errorMessage;
  }

  if (restricted_access_display_flag) {
    return (
      <div>
        <SecretURLFileDownloadLayout value={secretURLFileDownload}
                                   setValue={setSecretURLFileDownload}/>
        <ContentFileDownloadLayout value={contentFileDownload}
                                   setValue={setContentFileDownload}/>
        <UsageReportWorkflowAccessLayout value={usageReportWorkflowAccess}
                                         setValue={setUsageReportWorkflowAccess}/>
        <TermsConditions termList={termList} setTermList={setTermList}
                         currentTerm={currentTerm}
                         setCurrentTerm={setCurrentTerm}/>
        <ErrorMsgConditions errorMsg={errorMsg} setErrorMsg={setErrorMsg}/>
        <div className="form-group">
          <button id="save-btn" className="btn btn-primary pull-right" style={{marginBottom: "15px"}}
                  onClick={handleSave}>
            <span className="glyphicon glyphicon-save"></span>&nbsp;{SAVE_LABEL}
          </button>
        </div>
        <div>
          <UsageReportList/>
        </div>
      </div>
    )
  } else {
    return (
      <div>
        <SecretURLFileDownloadLayout value={secretURLFileDownload}
                                   setValue={setSecretURLFileDownload}/>
        <ErrorMsgConditions errorMsg={errorMsg} setErrorMsg={setErrorMsg}/>
        <div className="form-group">
          <button id="save-btn" className="btn btn-primary pull-right" style={{marginBottom: "15px"}}
                  onClick={handleSave}>
            <span className="glyphicon glyphicon-save"></span>&nbsp;{SAVE_LABEL}
          </button>
        </div>
      </div>
    )
  }
}

function showErrorMessage(errorMessage) {
  $("#inputModal").html(errorMessage);
  $("#allModal").modal("show");
}

function addAlert(message, type) {
  let className = "alert alert-success alert-boder";
  let closeButton = '<button type="button" class="close" data-dismiss="alert">&times;</button>'
  if (type === 1) {
    className = "alert alert-danger alert-dismissable alert-boder";
  }
  if (type === 2) {
    className = "alert alert-info alert-dismissable alert-boder";
  }
  $('#alerts').append(
    '<div class="' + className + '">'
    + closeButton + message + '</div>');
}

function isSuperset (set, subset){
  for (let elem of subset) {
    if (!set.has(elem)) {
      return false
    }
  }
  return true
}

const queryUsageReportList = (method, data, setActivities, setTotalPage, extraParams) => {
    const URL = "/api/admin/restricted_access/get_usage_report_activities";
    let request;
    if (method === 'GET') {
        request = $.ajax({
            url: URL + extraParams,
            type: "GET",
        });
    } else {
        request = $.ajax({
            url: URL,
            method: 'POST',
            contentType: 'application/json',
            dataType: 'json',
            data: JSON.stringify(data)
        });
    }
    request.success(
        function (result) {
            setActivities(result.activities)
            setTotalPage(result.number_of_pages)
        }
    )
        .error(function (error) {
            console.log(error);
        })
}

function ModalBodyConfirm ({selectedActivityIds}) {
  const [activities, setActivities] = useState([])
  const [currentPage, setCurrentPage] = useState(1)
  const [totalPage, setTotalPage] = useState(1)

  let startIndex = (currentPage - 1) * CONST_DEFAULT_ITEMS_PER_PAGE;

    useEffect(() => {
        let data = {
            activity_ids: Array.from(selectedActivityIds),
            page: currentPage,
            size: CONST_DEFAULT_ITEMS_PER_PAGE
        }
        queryUsageReportList('POST', data, setActivities, setTotalPage, '')
        startIndex = (currentPage - 1) * CONST_DEFAULT_ITEMS_PER_PAGE;
    }, [currentPage])

  const onPageChanged = (e) => {
    if (parseInt(e.target.text) !== currentPage) {
      setCurrentPage(parseInt(e.target.text))
    }
  }

  return (
    <div>
      <div className="form-inline flow-root">
        <div className="col-sm-12">
          <h3> {LABEL_USAGE_REPORT_REMINDER_MAIL} </h3>
        </div>
      </div>
      <div className="col-sm-12">
        <div className="table-responsive">
          <table className="table table-striped table-bordered table-responsive">
            <thead>
            <tr className="success">
              <th className="thWidth style-column">No.</th>
              <th className="thWidth style-column">{LABEL_ACTIVITY}</th>
              <th className="thWidth style-column">{LABEL_ITEMS}</th>
              <th className="thWidth style-column">{LABEL_WORKFLOW}</th>
              <th className="thWidth style-column">{LABEL_STATUS}</th>
              <th className="alignCenter">{LABEL_USER}</th>
            </tr>
            </thead>
            <tbody>
            {
              activities.map((activity, index) => (
                <tr>
                  <th scope="row">{startIndex + index + 1}</th>
                  <td>{activity.activity_id}</td>
                  <td>{activity.item_name}</td>
                  <td>{activity.workflow_name}</td>
                  <td>{LABEL_ACTION_DOING}</td>
                  <td>{activity.user_mail}</td>
                </tr>
              ))
            }
            </tbody>
          </table>
        </div>
      </div>
      <div className="row">
        <div className="text-center">
          <ul className="pagination">
            <li className={currentPage === 1 ? 'disabled' : ''} cursor={currentPage === 1 ? 'not-allowed' : ''}
                onClick={() => {
                  if (currentPage > 1) setCurrentPage(currentPage - 1)
                }}>
              <a>&lt;</a>
            </li>
            {Array.from(Array(totalPage), (e, i) => {
              return (
                <li className={(i + 1 === currentPage) ? `active` : ''} onClick={onPageChanged}>
                  <a>{i + 1}</a>
                </li>
              )
            })}
            <li className={currentPage >= totalPage ? `disabled` : ''} cursor={currentPage >= totalPage ?
              'not-allowed' : ''} onClick={() => {
              if (currentPage < totalPage) setCurrentPage(currentPage + 1)
            }}>
              <a>&gt;</a>
            </li>
          </ul>
        </div>
      </div>
    </div>
  )
}

function ModalFooterConfirm({setShowConfirm,setSelectedActivityIds, selectedActivityIds}) {
  function sendMailReminder() {
    const URL = "/api/admin/restricted_access/send_mail_reminder";
    const data = {
      activity_ids: Array.from(selectedActivityIds)
    }
    $.ajax({
      url: URL,
      method: 'POST',
      contentType: 'application/json',
      dataType: 'json',
      data: JSON.stringify(data),
      success: function (result) {
        if (result.status) {
          addAlert(MSG_SEND_MAIL_SUCCESSFUL, 2)
        } else {
          addAlert(MSG_SEND_MAIL_FAILED, 1)
        }
      },
      error: function (error) {
        console.log(error);
      }
    });
  }

  return (
    <div>
      <button type="button" className="btn btn-primary save-button" onClick={() => {
        sendMailReminder();
        setShowConfirm(false);
        setSelectedActivityIds(new Set());
      }}>
        <span className="glyphicon glyphicon-send"></span>&nbsp; {LABEL_SEND}
      </button>
      <button type="button" className="btn btn-info close-button" onClick={() =>
        setShowConfirm(false)}>
        <span className="glyphicon glyphicon-remove"></span>&nbsp; {LABEL_CLOSE}
      </button>
    </div>
  )
}

function ConfirmModal({selectedActivityIds, setSelectedActivityIds, show, setShowConfirm}) {
  return (
    <ReactBootstrap.Modal show={show} dialogClassName="popup-mail-modal">
      <ReactBootstrap.Modal.Body>
        <ModalBodyConfirm selectedActivityIds={selectedActivityIds}/>
      </ReactBootstrap.Modal.Body>
      <ReactBootstrap.Modal.Footer>
        <ModalFooterConfirm setShowConfirm={setShowConfirm} setSelectedActivityIds={setSelectedActivityIds}
                            selectedActivityIds={selectedActivityIds}/>
      </ReactBootstrap.Modal.Footer>
    </ReactBootstrap.Modal>
  )
}

function UsageReportList() {
  const [listActivities, setListActivities] = useState([]);
  const [selectedActivityIds, setSelectedActivityIds] = useState(new Set())
  const [isCheckedAll, setIsCheckedAll] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)
  const [enableBtnConfirm, setEnableBtnConfirm] = useState(true)
  const [totalPage, setTotalPage] = useState(1)
  const [currentPage, setCurrentPage] = useState(1)

  let startIndex = (currentPage - 1) * CONST_DEFAULT_ITEMS_PER_PAGE;
  let allCurrentPageIds = listActivities.map((activity) => {
    return activity.activity_id
  })

  useEffect(() => {
    updateCheckedAllState()
    setEnableBtnConfirm(selectedActivityIds.size <= 0)
  }, [selectedActivityIds]);

  useEffect(() => {
    let extraParams = `?page=${currentPage}&size=${CONST_DEFAULT_ITEMS_PER_PAGE}`
    queryUsageReportList('GET', {},setListActivities, setTotalPage, extraParams);
    startIndex = (currentPage - 1) * CONST_DEFAULT_ITEMS_PER_PAGE;
  }, [currentPage])

  useEffect(() => {
    allCurrentPageIds = listActivities.map((activity) => {
      return activity.activity_id
    })
    updateCheckedAllState()
  }, [listActivities])

  function updateCheckedAllState(){
    if (allCurrentPageIds.length > 0) {
      if (isSuperset(selectedActivityIds, new Set(allCurrentPageIds))) {
        setIsCheckedAll(true)
      } else {
        setIsCheckedAll(false)
      }
    }
  }

  function onCheckedAll(e) {
    let tempSelectedIds = new Set(selectedActivityIds);
    if (e.target.checked) {
      allCurrentPageIds.forEach(ids => tempSelectedIds.add(ids))
      setSelectedActivityIds(tempSelectedIds)
      setIsCheckedAll(true)
    } else {
      allCurrentPageIds.forEach(ids => tempSelectedIds.delete(ids))
      setSelectedActivityIds(tempSelectedIds)
      setIsCheckedAll(false)
    }
  }

  function onChecked(e) {
    let tempSelectedIds = new Set(selectedActivityIds);
    if (e.target.checked) {
      tempSelectedIds.add(e.target.id)
      setSelectedActivityIds(tempSelectedIds)
    } else {
      tempSelectedIds.delete(e.target.id)
      setSelectedActivityIds(tempSelectedIds)
    }
  }

  function onChangePage(e) {
    if (parseInt(e.target.text) !== currentPage) {
      setCurrentPage(parseInt(e.target.text))
    }
  }

  return (
    <div className="row">
      <div className="col-sm-12 col-md-12 col-md-12">
        <div className="panel panel-default">
          <div className="panel-heading">
            <h5>
              <strong>
                <p>{LABEL_USAGE_REPORT_REMINDER_MAIL}</p>
              </strong>
            </h5>
          </div>
          <div className="panel-body">
            <div className="table-responsive">
              <table className="table table-striped table-bordered table-responsive">
                <thead>
                <tr className="success">
                  <th className="thWidth style-column"><input type="checkbox" id="isCheckedAll" checked={isCheckedAll}
                                                              onChange={onCheckedAll}/></th>
                  <th className="thWidth style-column">No.</th>
                  <th className="thWidth style-column">{LABEL_ACTIVITY}</th>
                  <th className="thWidth style-column">{LABEL_ITEMS}</th>
                  <th className="thWidth style-column">{LABEL_WORKFLOW}</th>
                  <th className="thWidth style-column">{LABEL_STATUS}</th>
                  <th className="alignCenter">{LABEL_USER}</th>
                </tr>
                </thead>
                <tbody>
                {
                  listActivities.map((activity, index) => (
                    <tr>
                      <td>
                        <input key={activity.activity_id} type="checkbox"
                               checked={selectedActivityIds.has(activity.activity_id)}
                               id={activity.activity_id} onChange={onChecked}/>
                      </td>
                      <th scope="row">{startIndex + index + 1}</th>
                      <td><a
                        href={`${window.location.origin}/workflow/activity/detail/${activity.activity_id}`}>{activity.activity_id}</a>
                      </td>
                      <td>{activity.item_name}</td>
                      <td>{activity.workflow_name}</td>
                      <td>{LABEL_ACTION_DOING}</td>
                      <td>{activity.user_mail}</td>
                    </tr>
                  ))
                }
                </tbody>
              </table>
            </div>

            <div className="row">
              <div className="text-center">
                <ul className="pagination">
                  <li className={currentPage === 1 ? 'disabled' : ''}
                      onClick={() => {
                        if (currentPage > 1) setCurrentPage(currentPage - 1)
                      }}>
                    <a>&lt;</a>
                  </li>
                  {
                    Array.from(Array(totalPage), (e, i) => {
                      return (
                        <li className={(i + 1 === currentPage) ? `active` : ''} onClick={onChangePage}>
                          <a>{i + 1}</a>
                        </li>)
                    })
                  }
                  <li className={currentPage >= totalPage ? `disabled` : ''} cursor={currentPage >= totalPage ?
                    'not-allowed' : ''} onClick={() => {
                    if (currentPage < totalPage)
                      setCurrentPage(currentPage + 1)
                  }}>
                    <a>&gt;</a>
                  </li>
                </ul>
              </div>
            </div>
            <div className="pull-right">
              <button type="submit" id="filter_form_submit" className="btn btn-primary" disabled={enableBtnConfirm}
                      onClick={() =>
                        setShowConfirm(true)}>
                          <span className="glyphicon glyphicon-check"></span>
                          &nbsp;{LABEL_CONFIRM}
              </button>
            </div>
          </div>
          <div>
            <ConfirmModal selectedActivityIds={selectedActivityIds} setSelectedActivityIds={setSelectedActivityIds}
                          show={showConfirm}
                          setShowConfirm={setShowConfirm}/>
          </div>
        </div>
      </div>
    </div>
  )
}
