const {useState, useEffect} = React;
const LABEL_NEW = document.getElementById("new").value;
const SAVE_LABEL = document.getElementById('save_label').value;
const SUBJECT_LABEL = document.getElementById('subject_label').value;
const RECIPIENTS_LABEL = document.getElementById('recipients_label').value;
const MESSAGE_MISSING_DATA = document.getElementById('message_miss_data').value;
const EMPTY_TERM = {
  key: "",
  flag: false,
  content: {
    "subject": "",
    "recipients": "",
    "cc": "",
    "bcc": "",
    "body": ""
  }
};

$(function () {
  let initValue = document.getElementById('init_data').value;
  initValue = JSON.parse(initValue);

  ReactDOM.render(
      <MailTemplateLayout {...initValue} />,
      document.getElementById('root')
  )
});

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

    const URL = "/admin/mailtemplates/delete";
    let data = {
      template_id: event.target.id
    }

    $.ajax({
      url: URL,
      method: 'DELETE',
      contentType: 'application/json',
      dataType: 'json',
      data: JSON.stringify(data),
      success: function (result) {
        if (result.status) {
          addAlert(result.msg, 2);
        } else {
          addAlert(result.msg, 1);
        }
        if (result.data) {
          setTermList(result.data)
        }
      },
      error: function (error) {
        console.log(error);
        addAlert('Mail template delete failed.', 1);
      }
    });
  }

  function groupTemplatesByGenre(templates) {
    let groupingTemplates = templates.filter((tmpl) => tmpl["genre_key"] != null)
      .sort((tmpl1, tmpl2) => tmpl1.genre_order - tmpl2.genre_order)
      .reduce(function (newDict, tmpl) {
        newDict[tmpl["genre_key"]] = newDict[tmpl["genre_key"]] || {
          name: tmpl["genre_name"],
          items: []
        }
        newDict[tmpl["genre_key"]].items.push(tmpl);
        return newDict;
      }, {});
    return groupingTemplates
  }

  let groupTemplates = groupTemplatesByGenre(termList)

  return (
    <div className='row'>
      <div className="col col-md-12">
        <div className="panel-default">
          {
            Object.keys(groupTemplates).map((key) => (
              <div>
                <div>{groupTemplates[key].name}</div>
                <div className={`col col-md-12 padding-top ${key == "Others" ? " margin-top both scrollbar" : "margin-bottom"}`} id="sltBoxListEmail">
                  {
                    groupTemplates[key].items.map((term) => (
                      <li className="tree-list" key={term.key}>
                        <a
                          className={`list-group-item list-group-item-action ${currentTerm !== undefined && currentTerm.key === term.key ? 'active' : ''}`}
                          onClick={handleOnTermClick}
                          id={term.key}>ID:{term.key} | {term.content.subject}
                        </a>
                        {term.flag === false ? (
                          <a
                            className="glyphicon glyphicon-remove glyphicon-remove-term pull-right"
                            id={term.key}
                            key={term.key} onClick={handleRemoveTerm} />
                        ) : (
                          ""
                        )}
                      </li>
                    ))
                  }
                </div>
              </div>
            ))
          }

          <button className="btn btn-light add-button btn-add"
                  style={{ marginTop: "10px" }} id="new_term"
                  onClick={handleCreateNewTerm}>
            <span class="glyphicon glyphicon-plus"></span>{LABEL_NEW}
          </button>
        </div>
      </div>
    </div>
  )
}

function TermDetail({currentTerm, setCurrentTerm, additionalDisplay}) {
  const {subject, recipients, cc, bcc, body} = currentTerm.content;

  function handleOnInputChanged(event) {
    event.preventDefault();
    let oldContent;
    let content;

    oldContent = currentTerm.content;
    oldContent[event.target.name] = event.target.value;
    content = {...currentTerm.content, ...oldContent};
    setCurrentTerm({...currentTerm, content: content})
  }

  // Change the display based on the argument
  if (additionalDisplay == true) {
    return (
      <div style={{paddingRight: '15px'}}>
        <div className="form-group row margin-top">
          <label htmlFor="subject" className="col-sm-2 col-form-label field-required" style={{textAlign: 'right'}}>{SUBJECT_LABEL}</label>
          <div className="col-sm-10">
            <input type="text" className="form-control" disabled={currentTerm.existed !== true} name="subject" value={subject} onChange={e => handleOnInputChanged(e)}/>
          </div>
          <label htmlFor="recipients" className="col-sm-2 col-form-label" style={{textAlign: 'right'}}>{RECIPIENTS_LABEL}</label>
          <div className="col-sm-10">
            <input type="text" className="form-control" disabled={currentTerm.existed !== true} name="recipients" value={recipients} onChange={e => handleOnInputChanged(e)}/>
          </div>
          <label htmlFor="cc" className="col-sm-2 col-form-label" style={{textAlign: 'right'}}>CC</label>
          <div className="col-sm-10">
            <input type="text" className="form-control" disabled={currentTerm.existed !== true} name="cc" value={cc} onChange={e => handleOnInputChanged(e)}/>
          </div>
          <label htmlFor="bcc" className="col-sm-2 col-form-label" style={{textAlign: 'right'}}>BCC</label>
          <div className="col-sm-10">
            <input type="text" className="form-control" disabled={currentTerm.existed !== true} name="bcc" value={bcc} onChange={e => handleOnInputChanged(e)}/>
          </div>
          <div className="col-sm-12 margin-top">
            <textarea className="form-control mail_template_height" disabled={currentTerm.existed !== true} name="body" value={body} onChange={e => handleOnInputChanged(e)}/>
          </div>
        </div>
      </div>
    )
  } else {
    return (
      <div style={{paddingRight: '15px'}}>
        <div className="form-group row margin-top">
          <label htmlFor="subject" className="col-sm-2 col-form-label field-required" style={{textAlign: 'right'}}>{SUBJECT_LABEL}</label>
          <div className="col-sm-10">
            <input type="text" className="form-control" disabled={currentTerm.existed !== true} name="subject" value={subject} onChange={e => handleOnInputChanged(e)}/>
          </div>
          <div className="col-sm-12 margin-top">
            <textarea className="form-control mail_template_height" disabled={currentTerm.existed !== true} name="body" value={body} onChange={e => handleOnInputChanged(e)}/>
          </div>
        </div>
      </div>
    )
  }
}

function TermsConditions(
  {termList, setTermList, currentTerm, setCurrentTerm, additionalDisplay}
) {
  return (
    <div className="row">
      <div className="col col-md-4">
        <TermsList termList={termList} setTermList={setTermList}
                    currentTerm={currentTerm}
                    setCurrentTerm={setCurrentTerm}/>
      </div>
      <div className="col col-md-8">
        <TermDetail currentTerm={currentTerm}
                    setCurrentTerm={setCurrentTerm}
                    additionalDisplay={additionalDisplay}/>
      </div>
    </div>
  )
}

function MailTemplateLayout({mail_templates, additional_display}) {
  const [termList, setTermList] = useState(mail_templates);
  const [currentTerm, setCurrentTerm] = useState(EMPTY_TERM);

  function handleApply() {
    let termListClone = [...termList];
    if (currentTerm['key'] !== '') {
      // for existed term
      termListClone.map((term) => {
        if (term.key === currentTerm.key)
          term["content"] = JSON.parse(JSON.stringify(currentTerm)).content
      });
      setTermList(termListClone)
    }
    if (currentTerm['content'] && currentTerm['content']['subject'].trim() && currentTerm['content']['body'].trim()) {
      return {
        "valid": true,
        "data": [currentTerm]
      }
    } else {
      return {
        "valid": false,
        "data": null
      }
    }
  }

  function handleSave() {
    const URL = "/admin/mailtemplates/save";

    let terms_data = handleApply();
    if (terms_data["valid"] === false) {
      showErrorMessage(MESSAGE_MISSING_DATA);
      return false;
    }

    let data = {
      mail_templates: terms_data["data"]
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
          showErrorMessage(result.msg);
        }
        if (result.data) {
          setTermList(result.data)
        }
      },
      error: function (error) {
        console.log(error);
        addAlert('Mail template update failed.', 1);
      }
    });
  }

  return (
    <div>
      <TermsConditions termList={termList}
                       setTermList={setTermList}
                       currentTerm={currentTerm}
                       setCurrentTerm={setCurrentTerm}
                       additionalDisplay={additional_display}/>
      <div className="form-group">
        <button id="save-btn" className="btn btn-default"
                style={{width: "130px", height: "40px", fontSize: "15px"}} onClick={handleSave}>
          <span className="glyphicon glyphicon-save"></span>{SAVE_LABEL}
        </button>
      </div>
    </div>
  )
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
