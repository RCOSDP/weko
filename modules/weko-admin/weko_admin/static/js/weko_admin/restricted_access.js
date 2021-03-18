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

const MESSAGE_MISSING_DATA = document.getElementById('message_miss_data').value;
const LABEL_ENGLISH = document.getElementById("english").value;
const LABEL_JAPANESE = document.getElementById("japanese").value;
const LABEL_NEW = document.getElementById("new").value;
const LABEL_TERMS_AND_CONDITIONS = document.getElementById("terms_and_conditions").value;

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
              <div className="form-inline">
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
                  <input type="checkbox"
                         style={{marginRight: "5px", marginLeft: "15px"}}
                         id="expiration_date_unlimited_chk"
                         key={Math.random()}
                         checked={expiration_date_unlimited_chk}
                         onChange={handleChange}/>
                  {UNLIMITED_LABEL}
                </label>
              </div>
              <div className="form-inline">
                <label
                  className="col-sm-2 text-right">{DOWNLOAD_LIMIT_LABEL}</label>
                <input type="text" id="download_limit" className="col-sm-2"
                       onChange={handleChange}
                       disabled={download_limit_unlimited_chk}
                       pattern="[0-9]*"
                       value={download_limit}/>
                <label htmlFor="download_limit_unlimited_chk"
                       className="text-left">
                  <input type="checkbox"
                         style={{marginRight: "5px", marginLeft: "15px"}}
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
                  <a className="glyphicon glyphicon-remove glyphicon-remove-term pull-right"
                     id={term.key}
                     key={term.key} onClick={handleRemoveTerm}/>
                </li>
              ))
            }

            <button className="btn btn-light add-button btn-add" style={{marginTop: "10px"}} id="new_term"
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
          className="col-sm-2 col-form-label" style={{textAlign: 'right'}}>{LABEL_JAPANESE}</label>
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
          className="col-sm-2 col-form-label field-required" style={{textAlign: 'right'}}>{LABEL_ENGLISH}</label>
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


function RestrictedAccessLayout({content_file_download, terms_and_conditions}) {
  const [contentFileDownload, setContentFileDownload] = useState(content_file_download);
  const [termList, setTermList] = useState(terms_and_conditions);
  const [currentTerm, setCurrentTerm] = useState(EMPTY_TERM);

  function handleApply() {
    let termListClone = [...termList];
    if (!currentTerm.existed) {
      return {"valid": true, "data": [...JSON.parse(JSON.stringify(termListClone))]}
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
    let errorMessage = validateContentFileDownload();
    if (errorMessage) {
      showErrorMessage(errorMessage);
      return false;
    }
    let terms_data = handleApply();
    if (terms_data["valid"] === false) {
      showErrorMessage(MESSAGE_MISSING_DATA);
      return false;
    }

    let data = {
      content_file_download: contentFileDownload,
      terms_and_conditions: terms_data["data"]
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
      <TermsConditions termList={termList} setTermList={setTermList}
                       currentTerm={currentTerm}
                       setCurrentTerm={setCurrentTerm}/>
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
