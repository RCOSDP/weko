const {useState, useEffect} = React;
const CONTENT_FILE_DOWNLOAD_LABEL = document.getElementById('content_file_download_label').value;
const DOWNLOAD_LIMIT_LABEL = document.getElementById('download_limit_label').value;
const EXPIRATION_DATE_LABEL = document.getElementById('expiration_date_label').value;
const UNLIMITED_LABEL = document.getElementById('unlimited_label').value;
const SAVE_LABEL = document.getElementById('save_label').value;
const MESSAGE_LABEL = document.getElementById('message').value;
const MESSAGE_EMPTY_LABEL = document.getElementById('message_empty').value;
const MAX_INPUT_VAL = 2147483647;

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
                  <a className="glyphicon glyphicon-remove pull-right"
                     id={term.key}
                     key={term.key} onClick={handleRemoveTerm}/>
                </li>
              ))
            }
            <button className="btn btn-success btn-add" id="new_term"
                    onClick={handleCreateNewTerm}>{LABEL_NEW}</button>
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

  const required = {"color": " red"};

  return (
    <div>
      <form>
        <div className="form-group row margin-top">
          <label htmlFor="staticEmail"
                 className="col-sm-1 col-form-label">{LABEL_JAPANESE}</label>
          <div className="col-sm-10">
            <input type="text" className="form-control"
                   disabled={currentTerm.existed !== true} name="title"
                   value={ja.title}
                   onChange={e => handleOnInputChanged(e, "ja")}/>
          </div>

          <div className="col-sm-11 margin-top">
                <textarea className="form-control textarea_height"
                          disabled={currentTerm.existed !== true} name="content"
                          value={ja.content}
                          onChange={e => handleOnInputChanged(e, "ja")}/>
          </div>
        </div>
        <div className="form-group row margin-top">
          <label htmlFor="staticEmail"
                 className="col-sm-1 col-form-label">{LABEL_ENGLISH}<span
            style={required}>*</span></label>
          <div className="col-sm-10">

            <input type="text" disabled={currentTerm.existed !== true}
                   className="form-control" name="title" value={en.title}
                   onChange={e => handleOnInputChanged(e, "en")}/>
          </div>
          <div className="col-sm-11 margin-top">

                <textarea className="form-control textarea_height"
                          disabled={currentTerm.existed !== true} name="content"
                          value={en.content}
                          onChange={e => handleOnInputChanged(e, "en")}/>
          </div>
        </div>
      </form>
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
    if (!currentTerm.existed) {
      return {"valid": true, "data": JSON.parse(JSON.stringify(currentTerm))}
    }
    // for new tem
    console.log("termList: ", termList)
    if (currentTerm['key'] === '') {
      if (currentTerm.content.en.title === '' || currentTerm.content.en.content === '') {
        return {
          "valid": false,
          "data": JSON.parse(JSON.stringify(currentTerm))
        }
      } else {
        currentTerm['key'] = (Math.floor(Date.now() / 10)).toString();
        setTermList([...termList, JSON.parse(JSON.stringify(currentTerm))])
        return {
          "valid": true,
          "data": [...termList, JSON.parse(JSON.stringify(currentTerm))]
        }
      }
    } else {
      // for existed term
      let termListClone = [...termList];
      termListClone.map((term) => {
        if (term.key === currentTerm.key)
          term["content"] = JSON.parse(JSON.stringify(currentTerm)).content
      });
      setTermList(termListClone)
      return {
        "valid": true,
        "data": [JSON.parse(JSON.stringify(termListClone))]
      }
    }
  }

  function handleSave() {
    const URL = "/api/admin/restricted_access/save";
    let isvalid = validateContentFileDownload()

    if (isvalid[0] == false) {
      showErrorMessage(MESSAGE_EMPTY_LABEL + " " + EXPIRATION_DATE_LABEL);
      return false;
    }
    if (isvalid[1] == false) {
      showErrorMessage(MESSAGE_EMPTY_LABEL + " " + DOWNLOAD_LIMIT_LABEL);
      return false;
    }

    if (isvalid[2] == false) {
      showErrorMessage(MESSAGE_LABEL + " " + EXPIRATION_DATE_LABEL);
      return false;
    }

    if (isvalid[3] == false) {
      showErrorMessage(MESSAGE_LABEL + " " + DOWNLOAD_LIMIT_LABEL);
      return false;
    }

    let terms_data = handleApply();
    if (terms_data["valid"] === false) {
      showErrorMessage("Please input required fields");
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

    let isValid_0 = true, isValid_1 = true, isValid_2 = true, isValid_3 = true;

    if (expiration_date === "" && expiration_date_unlimited_chk === false) {
      isValid_0 = false;
    }

    if (download_limit === "" && download_limit_unlimited_chk === false) {
      isValid_1 = false;
    }

    if (expiration_date < 1 || expiration_date > 999999999) {
      isValid_2 = false;
    }

    if (download_limit < 1 || download_limit > MAX_INPUT_VAL) {
      isValid_3 = false;
    }
    let isValid = [isValid_0, isValid_1, isValid_2, isValid_3];

    return isValid;
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
