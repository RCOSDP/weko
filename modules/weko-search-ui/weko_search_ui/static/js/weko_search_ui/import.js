const import_label = document.getElementById("import").value;
const list = document.getElementById("list").value;
const select_file = document.getElementById("select_file").value;
const selected_file_name = document.getElementById("selected_file_name").value;
const index_tree = document.getElementById("index_tree").value;
const designate_index = document.getElementById("designate_index").value;
const item_type = document.getElementById("item_type").value;
const item_type_templates = document.getElementById("item_type_templates").value;
const flow = document.getElementById("flow").value;
const select = document.getElementById("select").value;
const cancel = document.getElementById("cancel").value;
const check = document.getElementById("check").value;
const change_identifier_mode = document.getElementById("change_identifier_mode").value;
const change_doi_mode = document.getElementById("change_doi_mode").value;
const i_agree = document.getElementById("i_agree").value;
// label check
const summary = document.getElementById("summary").value;
const total_label = document.getElementById("total").value;
const new_item_label = document.getElementById("new_item").value;
const update_item_label = document.getElementById("update_item").value;
const check_error_label = document.getElementById("check_error").value;
const waring_item_label = document.getElementById("warning").value;
const download = document.getElementById("download").value;
const no = document.getElementById("no").value;
const item_id = document.getElementById("item_id").value;
const title = document.getElementById("title").value;
const doi = document.getElementById("doi").value;
const check_result = document.getElementById("check_result").value;
const error = document.getElementById("error").value;
const warning = document.getElementById("warning").value;
const not_match = document.getElementById("not_match").value;
const register = document.getElementById("register").value;
const keep = document.getElementById("keep").value;
const upgrade = document.getElementById("upgrade").value;
const register_with = document.getElementById("register_with").value;

//label result
const start_date = document.getElementById("start_date").value;
const end_date = document.getElementById("end_date").value;
const importResult = document.getElementById("import_result").value;
const end = document.getElementById("end").value;
const statusLabel = document.getElementById("status").value;
const done = document.getElementById("done").value;
const processing = document.getElementById("processing").value;
const waiting = document.getElementById("waiting").value;
const result_label = document.getElementById("result").value;
const succses = document.getElementById("succses").value;
const next = document.getElementById("next").value;
const error_download = document.getElementById("error_download").value;
const error_get_lstItemType = document.getElementById("error_get_lstItemType").value;
const internal_server_error = document.getElementById("internal_server_error").value;
const not_available_error_another = document.getElementById("not_available_error_another").value;
const not_available_error = document.getElementById("not_available_error").value;
const celery_not_run = document.getElementById("celery_not_run").value;
const is_duplicated_doi = document.getElementById("is_duplicated_doi").value;
const is_withdraw_doi = document.getElementById("is_withdraw_doi").value;
const item_is_deleted = document.getElementById("item_is_deleted").value;
const item_is_being_edit = document.getElementById("item_is_being_edit").value;

const file_format = $("#file_format").text() ? $("#file_format").text() : "tsv";
const workflows = JSON.parse($("#workflows").text() ? $("#workflows").text() : "");
const urlTree = window.location.origin + '/api/tree'
const urlCheck = window.location.origin + '/admin/items/import/check'
const urlGetChangeIdentifierMode = window.location.origin + '/admin/items/import/get_disclaimer_text'
const urlCheckStatus = window.location.origin + '/admin/items/import/check_status'
const urlDownloadCheck = window.location.origin + '/admin/items/import/download_check'
const urlDownloadImport = window.location.origin + '/admin/items/import/export_import'
const urlDownloadTemplate = window.location.origin + '/admin/items/import/export_template'
const urlImport = window.location.origin + '/admin/items/import/import'
const urlCheckImportAvailable = window.location.origin + '/admin/items/import/check_import_is_available'
const step = {
  "SELECT_STEP": 0,
  "IMPORT_STEP": 1,
  "RESULT_STEP": 2,
}

function closeError() {
  $('#errors').empty();
}

function showErrorMsg(msg) {
  $('#errors').append(
    '<div class="alert alert-danger alert-dismissable">' +
    '<button type="button" class="close" data-dismiss="alert" aria-hidden="true">' +
    '&times;</button>' + msg + '</div>');
}

function getTaskResult(task_result) {
  if (!task_result) return '';
  if (task_result.success) return succses;

  const errorMessages = {
    is_duplicated_doi,
    is_withdraw_doi,
    item_is_deleted,
    item_is_being_edit
  };
  const msg = errorMessages[task_result.error_id] || '';
  return msg === '' ? '' : error + ': ' + msg;
}

function getTaskStatusLabel(taskStatus) {
  if (!taskStatus) return '';
  switch (taskStatus) {
    case "PENDING":
      return waiting;
    case "STARTED":
      return processing;
    case "SUCCESS":
      return done;
    case "FAILURE":
      return "FAILURE";
    default:
      return '';
  }
}

class MainLayout extends React.Component {

  constructor() {
    super()
    this.state = {
      tab: 'select',
      step: 0,
      tabs: [
        {
          tab_key: 'select',
          tab_name: select,
          step: step.SELECT_STEP
        },
        {
          tab_key: 'import',
          tab_name: import_label,
          step: step.IMPORT_STEP
        },
        {
          tab_key: 'result',
          tab_name: result_label,
          step: step.RESULT_STEP
        }
      ],
      list_record: [],
      tasks: [],
      is_import: true,
      import_status: false,
      isShowMessage: false,
      isChecking: false
    }
    this.handleChangeTab = this.handleChangeTab.bind(this)
    this.handleCheck = this.handleCheck.bind(this)
    this.getCheckStatus = this.getCheckStatus.bind(this)
    this.handleImport = this.handleImport.bind(this)
    this.getStatus = this.getStatus.bind(this)
    this.updateShowMessage = this.updateShowMessage.bind(this)
    this.handleCheckImportAvailable = this.handleCheckImportAvailable.bind(this)
  }

  updateShowMessage(state) {
    this.setState({ isShowMessage: state })
  }

  handleChangeTab(tab) {
    const { step, tabs } = this.state
    const a = tabs.filter(item => {
      return item.tab_key === tab
    })
    if (a[0]) {
      const item = a[0]
      if (step >= item.step) {
        this.setState({
          tab: tab
        })
      }
    }
  }

  componentDidMount() {
    const header = document.getElementsByClassName('content-header')[0];
    if (header) {
      const errorElement = document.createElement('div');
      errorElement.setAttribute('id', 'errors');
      header.insertBefore(errorElement, header.firstChild);
    }
    this.handleCheckImportAvailable();
  }

  handleCheck(formData) {
    const that = this;
    closeError();
    this.setState({ isChecking: true });

    var csrf_token = $('#csrf_token').val();
    $.ajaxSetup({
      beforeSend: function (xhr, settings) {
        if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
          xhr.setRequestHeader("X-CSRFToken", csrf_token);
        }
      }
    });

    $.ajax({
      url: urlCheck,
      type: 'POST',
      data: formData,
      contentType: false,
      processData: false,
      success: function (response) {
        that.getCheckStatus(response.check_import_task_id);
      },
      error: function (error) {
        console.log(error);
        showErrorMsg(internal_server_error);
        that.setState({ isChecking: false });
      }
    });
  }

  getCheckStatus(taskId) {
    const that = this;

    $.ajax({
      url: window.location.origin + '/admin/items/import/get_check_status',
      method: 'POST',
      data: JSON.stringify({ task_id: taskId }),
      contentType: "application/json; charset=utf-8",
      dataType: "json",
    }).done((response) => {
      if (response.error) {
        showErrorMsg(response.error);
        that.setState({ isChecking: false });
        return;
      }

      if ('list_record' in response) {
        const is_import = response.list_record.filter(item => {
          return !item.errors || item.errors.length === 0;
        }).length <= 0;
        that.setState(() => {
          return {
            list_record: response.list_record,
            data_path: response.data_path,
            is_import,
            step: step.IMPORT_STEP
          }
        }, () => {
          that.handleChangeTab('import');
          that.setState({ isChecking: false });
          return;
        })
      } else {
        setTimeout(function () {
          that.getCheckStatus(taskId);
        }, 1000);
      }
    }).fail((err) => {
      console.log(err);
      showErrorMsg(internal_server_error);
      that.setState({ isChecking: false });
    });
  }

  handleCheckImportAvailable() {
    closeError();
    let result = false;
    $.ajax({
      url: urlCheckImportAvailable,
      type: 'GET',
      dataType: "json",
      async: false,
      success: function (response) {
        if (!response.is_available) {
          let error_msg = not_available_error;
          if (response.error_id === 'celery_not_run') {
            error_msg = celery_not_run;
          }
          showErrorMsg(error_msg);
        } else {
          result = true;
        }
      },
      error: function (error) {
        console.log(error);
        showErrorMsg(internal_server_error);
      }
    });
    return result;
  }

  handleImport() {
    const { list_record, data_path, is_import } = this.state;
    const that = this;
    if (is_import || !this.handleCheckImportAvailable()) {
      return;
    }
    this.setState({
      is_import: true
    })
    $.ajax({
      url: urlImport,
      type: 'POST',
      data: JSON.stringify({
        list_record: list_record.filter(item => !item.errors),
        data_path,
        list_doi: $('[name="list_doi"]:not(:disabled)').map((_, el) => $(el).val()).get()
      }),
      contentType: "application/json; charset=utf-8",
      dataType: "json",
      success: function (response) {
        that.setState(() => {
          return {
            step: step.RESULT_STEP,
            tasks: response.data.tasks,
          }
        }, () => {
          that.handleChangeTab('result');
        })
      },
      error: function (error) {
        console.log(error);
      }
    });
  }

  getStatus() {
    const that = this
    const { tasks } = this.state
    $.ajax({
      url: urlCheckStatus,
      method: 'POST',
      data: JSON.stringify({
        tasks
      }),
      contentType: "application/json; charset=utf-8",
      dataType: "json",
    })
      .done((res) => {

        that.setState({
          tasks: res.result
        })
        if (res.status === 'done') {
          that.setState({
            import_status: true
          })
          return
        }
        setTimeout(function () {
          that.getStatus();
        }, 1000);
      })
      .fail((err) => {
        console.log(err);
      });
  }

  render() {
    const { tab, tabs, list_record, is_import, tasks, import_status, isShowMessage, isChecking } = this.state;
    return (
      <div>
        <ul className="nav nav-tabs">
          {
            tabs.map((item, key) => {
              return (
                <li role="presentation" className={`${item.tab_key === tab ? 'active' : ''}`} onClick={() => this.handleChangeTab(item.tab_key)}><a href="#">{item.tab_name}</a></li>
              )
            })
          }
        </ul>
        <div className={`${tab === tabs[0].tab_key ? '' : 'hide'}`}>
          <ImportComponent
            handleCheck={this.handleCheck}
            updateShowMessage={this.updateShowMessage}
            isChecking={isChecking}
          />
        </div>
        <div className={`${tab === tabs[1].tab_key ? '' : 'hide'}`}>
          <CheckComponent
            isShowMessage={isShowMessage}
            list_record={list_record || []}
            handleImport={this.handleImport}
            is_import={is_import}
          />
        </div>
        <div className={`${tab === tabs[2].tab_key ? '' : 'hide'}`}>
          {
            tab === tabs[2].tab_key && <ResultComponent
              tasks={tasks || []}
              getStatus={this.getStatus}
              import_status={import_status}
            />
          }

        </div>
      </div>
    )
  }
}

class ImportComponent extends React.Component {

  constructor() {
    super()
    this.state = {
      file: null,
      file_name: "",
      isShowModalWF: false,
      work_flow_data: null,
      wl_key: null,
      isShowModalIndex: false,
      list_index: [],
      term_select_index_list: [],
      select_index_list: [],
      isShowModalImport: false,
      show: false,
      is_agree_doi: false,
      is_change_identifier: false,
      change_identifier_mode_content: [],
      disabled_checkbox: false
    }
    this.handleChangefile = this.handleChangefile.bind(this)
    this.handleClickFile = this.handleClickFile.bind(this)
    this.getLastString = this.getLastString.bind(this)
    this.handleShowModalWorkFlow = this.handleShowModalWorkFlow.bind(this)
    this.handleChangeWF = this.handleChangeWF.bind(this)
    this.handleShowModalIndex = this.handleShowModalIndex.bind(this)
    this.handleSelectIndex = this.handleSelectIndex.bind(this)
    this.handleSubmit = this.handleSubmit.bind(this)
    this.handleInputChange = this.handleInputChange.bind(this);
    this.handleAgreeChange = this.handleAgreeChange.bind(this);
    this.handleClose = this.handleClose.bind(this);
    this.handleConfirm = this.handleConfirm.bind(this);
    this.getDisclaimerContent = this.getDisclaimerContent.bind(this);
  }

  componentDidMount() {
    const that = this
    $.ajax({
      url: urlTree,
      type: 'GET',
      success: function (data) {
        that.setState({
          list_index: data
        })
      },
      error: function (error) {
        console.log(error);
      }
    });

    this.getDisclaimerContent();
  }

  handleChangefile(e) {
    const file = e.target.files[0];
    const file_name = this.getLastString(e.target.value, "\\");
    if (this.getLastString(file_name, ".") !== 'zip') {
      return false;
    }

    this.setState({
      file,
      file_name,
      disabled_checkbox: false
    });
  }

  handleClickFile() {
    this.inputElement.click();
  }

  getLastString(path, code) {
    const split_path = path.split(code)
    return split_path.pop()
  }

  handleShowModalWorkFlow(data) {
    const { isShowModalWF, work_flow_data } = this.state
    if (!isShowModalWF) {
      this.setState({
        isShowModalWF: !isShowModalWF,
        wl_key: work_flow_data ? workflows.findIndex((item) => { return work_flow_data && item.id === work_flow_data.id }) : null
      })
    } else {
      this.setState({
        isShowModalWF: !isShowModalWF,
        work_flow_data: data ? data : work_flow_data
      })
    }
  }

  handleChangeWF(e) {
    const value = e.target.value
    this.setState({
      wl_key: value
    })
  }

  handleShowModalIndex(data) {
    const { isShowModalIndex, select_index_list, term_select_index_list } = this.state
    if (!isShowModalIndex) {
      this.setState({
        isShowModalIndex: !isShowModalIndex,
        term_select_index_list: [...select_index_list]
      })
    } else {
      this.setState({
        isShowModalIndex: !isShowModalIndex,
        select_index_list: data ? [...term_select_index_list] : [...select_index_list]
      })
    }
  }

  handleSelectIndex(data) {
    const { term_select_index_list } = this.state
    const new_select_index = term_select_index_list.filter(item => {
      return data.id !== item.id
    })
    if (new_select_index.length !== term_select_index_list.length) {
      this.setState({
        term_select_index_list: new_select_index
      })
    } else {
      this.setState({
        term_select_index_list: [...term_select_index_list, { ...data }]
      })
    }
  }

  handleSubmit() {
    const { file, is_change_identifier } = this.state;
    const { handleCheck, updateShowMessage } = this.props;
    let formData = new FormData();
    formData.append('file', file);
    formData.append('is_change_identifier', is_change_identifier);

    if (is_change_identifier) {
      this.setState({
        disabled_checkbox: true,
        show: true
      });
    } else {
      updateShowMessage(false);
      handleCheck(formData);
    }

  }

  getDisclaimerContent() {
    const that = this
    $.ajax({
      url: urlGetChangeIdentifierMode,
      type: 'GET',
      success: function (result) {

        that.setState({
          change_identifier_mode_content: result.data
        })
      },
      error: function (error) {
        console.log(error);
      }
    });
  }

  handleInputChange(event) {
    const target = event.target;
    const value = target.name === 'is_change_identifier' ? target.checked : target.value;
    const name = target.name;

    this.setState({
      [name]: value
    });
  }
  handleAgreeChange(event) {
    const target = event.target;
    const value = target.name === 'is_agree_doi' ? target.checked : target.value;
    const name = target.name;

    this.setState({
      [name]: value
    });
  }


  handleClose() {
    this.setState({
      show: false,
      is_agree_doi: false
    });
  }
  handleConfirm() {
    const { file, is_change_identifier } = this.state;
    const { handleCheck, updateShowMessage } = this.props;
    let formData = new FormData();
    formData.append('file', file);
    formData.append('is_change_identifier', is_change_identifier);

    this.setState({
      show: false,
      is_agree_doi: false
    });
    updateShowMessage(true);
    handleCheck(formData);
  }

  render() {
    const {
      file_name,
      file,
      is_agree_doi,
      is_change_identifier,
      change_identifier_mode_content,
      disabled_checkbox
    } = this.state;
    const { isChecking } = this.props;
    return (
      <div className="import_component">
        <div className="row layout">
          <div className="col-md-12">
            <div className="row">
              <div className="col-md-2 col-cd">
                <label>{select_file}</label>
              </div>
              <div className="col-md-8">
                <div>
                  <button className="btn btn-primary" onClick={this.handleClickFile}>{select_file}</button>
                  <input
                    type="file"
                    className="input-file"
                    ref={input => this.inputElement = input}
                    accept=".zip"
                    onChange={this.handleChangefile}
                  />
                </div>
                <div className="block-placeholder">
                  {
                    file_name ? <p className="active">{file_name}</p> : <p>{selected_file_name}</p>
                  }
                </div>
              </div>
            </div>
          </div>
          <div className="col-md-12">
            <div className="row">
              <div className="col-md-4">
                <div class="form-check">
                  <input
                    id="is_change_identifier"
                    name="is_change_identifier"
                    type="checkbox"
                    disabled={disabled_checkbox}
                    checked={is_change_identifier}
                    onChange={this.handleInputChange} />
                  <label class="form-check-label margin_left" for="is_change_identifier">{change_identifier_mode}</label>
                </div>
              </div>
            </div>
          </div>
          <div className="col-md-12">
            <div className="row">
              <div className="col-md-2">
                <button
                  className="btn btn-primary"
                  disabled={!file || isChecking}
                  onClick={() => {
                    file && this.handleSubmit()
                  }}>
                  {isChecking ? <div className="loading" /> : <span className="glyphicon glyphicon-download-alt icon"></span>}
                  {next}
                </button>
              </div>
            </div>
          </div>
        </div>
        <hr />
        <ItemTypeComponent />
        <ReactBootstrap.Modal show={this.state.show} onHide={this.handleClose} dialogClassName="w-725">
          <ReactBootstrap.Modal.Header closeButton>
            <h4 className="modal-title in_line">{change_identifier_mode}</h4>
          </ReactBootstrap.Modal.Header>
          <ReactBootstrap.Modal.Body>
            {change_identifier_mode_content.map((item, index) => (
              <div className="row">{item} </div>
            ))}
          </ReactBootstrap.Modal.Body>
          <ReactBootstrap.Modal.Footer>
            <br />
            <div className="col-12">
              <div className="row">
                <div className="form-check pull-left">
                  <input
                    id="is_agree_doi"
                    name="is_agree_doi"
                    type="checkbox"
                    checked={is_agree_doi}
                    onChange={this.handleAgreeChange} />
                  <label className="form-check-label margin_left" htmlFor="is_agree_doi">{i_agree}</label>
                </div>
              </div>
              <br />
              <br />
              <div className="row text-center">
                <button variant="primary" type="button" className="btn btn-default" disabled={!is_agree_doi} onClick={this.handleConfirm}>OK</button>
                <button variant="secondary" type="button" className="btn btn-default" onClick={this.handleClose}>{cancel}</button>
              </div>
            </div>
          </ReactBootstrap.Modal.Footer>
        </ReactBootstrap.Modal>
      </div>
    )
  }
}

class TreeList extends React.Component {

  constructor() {
    super()

  }

  render() {
    const { children, tree_name, select_index_list } = this.props
    return (
      <div>
        <ul>
          {
            children.map((item, index) => {
              return (
                <li>
                  <TreeNode
                    data={item} key={index}
                    handleSelectIndex={this.props.handleSelectIndex}
                    tree_name={tree_name}
                    select_index_list={select_index_list}
                  ></TreeNode>
                </li>
              )
            })
          }
        </ul>
      </div>
    )
  }

}

class TreeNode extends React.Component {

  constructor() {
    super()
    this.state = {
      isCollabsed: true,
      defaultChecked: false
    }
    this.handleShow = this.handleShow.bind(this)
    this.handleClick = this.handleClick.bind(this)
    this.defaultChecked = this.defaultChecked.bind(this)
  }

  handleShow() {
    const { isCollabsed } = this.state
    this.setState({
      isCollabsed: !isCollabsed
    })
  }

  handleClick(e) {
    const checked = e.target.checked
    this.props.handleSelectIndex({
      id: this.props.data.id,
      name: [...this.props.tree_name, this.props.data.name]
    })
    this.setState({
      defaultChecked: checked
    })
  }

  defaultChecked() {
    const { data, select_index_list } = this.props
    const result = !!select_index_list.filter(item => item.id === data.id).length
    return result
  }

  componentDidMount() {
    this.setState({
      defaultChecked: this.defaultChecked()
    })
  }

  render() {
    const { data, tree_name, select_index_list, } = this.props
    const { isCollabsed, defaultChecked } = this.state

    return (
      <div className="tree-node">
        <div
          className={`folding ${data.children.length ? isCollabsed ? 'node-collapsed' : 'node-expanded' : 'weko-node-empty'}`}
          onClick={() => { data.children.length && this.handleShow() }}
        >
        </div>
        <div className='node-value'>
          <input type="checkbox" onChange={this.handleClick} ref={re => this.input} checked={defaultChecked} style={{ marginRight: '5px' }}></input>
          <span className="node-name">{data.name}</span>
        </div>
        <div className={`${isCollabsed ? 'hide' : ''}`}>
          <TreeList
            children={data.children}
            tree_name={[...tree_name, data.name]}
            handleSelectIndex={this.props.handleSelectIndex}
            select_index_list={select_index_list}
          ></TreeList>
        </div>
      </div>
    )
  }

}

class CheckComponent extends React.Component {

  constructor(props) {
    super(props)
    this.state = {
      total: 0,
      new_item: 0,
      update_item: 0,
      check_error: 0,
      warning_item: 0,
      list_record: []
    }
    this.handleGenerateData = this.handleGenerateData.bind(this)
    this.generateTitle = this.generateTitle.bind(this)
    this.handleDownload = this.handleDownload.bind(this)
  }

  componentWillReceiveProps(nextProps, prevProps) {
    this.handleGenerateData(nextProps.list_record)
  }

  handleGenerateData(list_record = []) {
    const check_error = list_record.filter((item) => {
      return item.errors
    }).length
    const new_item = list_record.filter((item) => {
      return item.status && item.status === 'new'
    }).length
    const update_item = list_record.filter((item) => {
      return item.status && (item.status === 'keep' || item.status === 'upgrade')
    }).length
    const warning_item = list_record.filter((item) => {
      return item.warnings && item.warnings.length > 0
    }).length

    this.setState({
      total: list_record.length,
      check_error: check_error,
      new_item: new_item,
      update_item: update_item,
      warning_item: warning_item,
      list_record: list_record
    })
  }

  generateTitle(title, len) {
    if (title.length <= len) {
      return title
    } else {
      return title.substring(0, len + 1) + '...'
    }
  }
  create_errors(errors) {
    let result = "";
    if (errors[0]) {

      for (let i = 0; i < errors.length; i++) {
        result += "ERRORS: " + errors[i];
        if (i != errors.length - 1) {
          result += "; ";
        }
      }
    } else {
      result = "ERRORS";
    }
    return result
  }

  handleDownload() {
    const { list_record } = this.state
    const result = list_record.map((item, key) => {
      return {
        'No': key + 1,
        'Item Type': item.item_type_name,
        'Item Id': item.id,
        'Title': item['item_title'] ? item['item_title'] : '',
        'Check result': item['errors'] ? this.create_errors(item['errors']) : item.status === 'new' ? 'Register' : item.status === 'keep' ? 'Keep' : item.status === 'upgrade' ? 'Upgrade' : ''
      }
    })
    const data = {
      list_result: result
    }

    $.ajax({
      url: urlDownloadCheck,
      type: 'POST',
      data: JSON.stringify(data),
      contentType: "application/json; charset=utf-8",
      success: function (response) {
        const date = moment()
        const fileName = 'check_' + date.format("YYYY-MM-DD") + '.' + file_format;

        const blob = new Blob([response], { type: 'text/' + file_format });
        if (window.navigator && window.navigator.msSaveOrOpenBlob) {
          window.navigator.msSaveOrOpenBlob(blob, fileName);
        } else {
          const url = window.URL.createObjectURL(blob);
          const tempLink = document.createElement('a');
          tempLink.style.display = 'none';
          tempLink.href = url;
          tempLink.download = fileName;
          document.body.appendChild(tempLink);
          tempLink.click();

          setTimeout(function () {
            document.body.removeChild(tempLink);
            window.URL.revokeObjectURL(url);
          }, 200)
        }
      },
      error: function (error) {
        console.log(error);
        alert(error_download);
      }
    });
  }

  render() {
    const { total, list_record, update_item, new_item, check_error, warning_item } = this.state
    const { is_import, isShowMessage } = this.props
    return (
      <div className="check-component">
        <div className="row">
          {isShowMessage && (<div className="col-md-12 text-center"><div className="message">{register_with}</div></div>)}
          <br />
          <br />
          <div className="col-md-12 text-center">
            <button
              className="btn btn-primary"
              onClick={this.props.handleImport}
              disabled={is_import}
            >
              <span className="glyphicon glyphicon-download-alt icon"></span>{import_label}
            </button>
          </div>
          <div className="col-md-12 text-center">
            <div className="row block-summary">
              <div className="col-lg-2 col-md-3 col-sm-3">
                <h3><b>{summary}</b></h3>
                <div className="flex-box">
                  <div>{total_label}:</div>
                  <div>{total}</div>
                </div>
                <div className="flex-box">
                  <div>{new_item_label}:</div>
                  <div>{new_item}</div>
                </div>
                <div className="flex-box">
                  <div>{update_item_label}:</div>
                  <div>{update_item}</div>
                </div>
                <div className="flex-box">
                  <div>{check_error_label}:</div>
                  <div>{check_error}</div>
                </div>
                <div className="flex-box">
                  <div>{waring_item_label}:</div>
                  <div>{warning_item}</div>
                </div>
              </div>
              <div className="col-lg-10 col-md-9 text-align-right">
                <button
                  className="btn btn-primary"
                  onClick={this.handleDownload}
                >
                  <span className="glyphicon glyphicon-cloud-download icon"></span>{download}
                </button>
              </div>
            </div>
          </div>
          <div className="col-md-12 m-t-20">
            <table class="table table-striped table-bordered">
              <thead>
                <tr>
                  <th>{no}</th>
                  <th><p className="item_type">{item_type}</p></th>
                  <th><p className="item_id">{item_id}</p></th>
                  <th>{title}</th>
                  <th>{doi}</th>
                  <th><p className="check_result">{check_result}</p></th>
                </tr>
              </thead>
              <tbody>
                {
                  list_record.map((item, key) => {
                    return (
                      <tr key={key}>
                        <td>
                          {key + 1}
                        </td>
                        <td>{item.item_type_name || not_match}</td>
                        <td>
                          {item.status === 'new' && item.id ? (new_item_label + '(' + item.id + ')') : item.id ? item.id : ''}
                        </td>
                        <td>
                          <p className="title_item">
                            {item['item_title'] ? item['item_title'] : ''}
                          </p>

                        </td>
                        <td>
                          <div class="form-inline">
                            <input class="form-control" type="text" name="list_doi" disabled={item.errors && item.errors.length > 0} />
                          </div>
                        </td>
                        <td>
                          {
                            item['errors'] ? item['errors'].map(e => {
                              return <div dangerouslySetInnerHTML={{ __html: error + ': ' + e }}></div>
                            }) : item.status === 'new' ? register : item.status === 'keep' ? keep : item.status === 'upgrade' ? upgrade : ''
                          }
                          {
                            item['warnings'] && item['warnings'].map(e => {
                              return <div dangerouslySetInnerHTML={{ __html: warning + ': ' + e }}></div>
                            })
                          }
                        </td>
                      </tr>
                    )
                  })
                }
              </tbody>
            </table>
          </div>
        </div>
      </div>
    )
  }
}

class ResultComponent extends React.Component {
  constructor() {
    super()
    this.state = {
    }
    this.handleDownload = this.handleDownload.bind(this)
  }

  componentDidMount() {
    this.props.getStatus()
  }

  handleDownload() {
    const { tasks } = this.props
    const result = tasks.map((item, key) => {
      return {
        [no]: key + 1,
        [start_date]: item.start_date ? item.start_date : '',
        [end_date]: item.end_date ? item.end_date : '',
        [item_id]: item.item_id || '',
        [statusLabel]: getTaskStatusLabel(item.task_status),
        [importResult]: getTaskResult(item.task_result)
      }
    })
    const data = {
      list_result: result
    }

    $.ajax({
      url: urlDownloadImport,
      type: 'POST',
      data: JSON.stringify(data),
      contentType: "application/json; charset=utf-8",
      success: function (response) {
        const date = moment()
        const fileName = 'List_Download_' + date.format("YYYY-MM-DD") + '.' + file_format;

        const blob = new Blob([response], { type: 'text/' + file_format });
        if (window.navigator && window.navigator.msSaveOrOpenBlob) {
          window.navigator.msSaveOrOpenBlob(blob, fileName);
        } else {
          const url = window.URL.createObjectURL(blob);
          const tempLink = document.createElement('a');
          tempLink.style.display = 'none';
          tempLink.href = url;
          tempLink.download = fileName;
          document.body.appendChild(tempLink);
          tempLink.click();

          setTimeout(function () {
            document.body.removeChild(tempLink);
            window.URL.revokeObjectURL(url);
          }, 200)
        }
      },
      error: function (error) {
        console.log(error);
        alert(error_download);
      }
    });
  }

  render() {
    const { tasks, import_status } = this.props
    return (
      <div className="result_container row">
        <div className="col-md-12 text-align-right">
          <button
            className="btn btn-primary"
            onClick={this.handleDownload}
            disabled={!import_status}
          >
            <span className="glyphicon glyphicon-cloud-download icon"></span>{download}
          </button>
        </div>
        <div className="col-md-12 m-t-20">
          <table class="table table-striped table-bordered">
            <thead>
              <tr>
                <th className="id">{no}</th>
                <th className="start_date"><p className="t_head">{start_date}</p></th>
                <th className="end_date"><p className="t_head ">{end_date}</p></th>
                <th className="t_head item_id">{item_id}</th>
                <th className="t_head wf_status">{statusLabel}</th>
                <th><p className="t_head action">{importResult}</p></th>
              </tr>
            </thead>
            <tbody>
              {
                tasks.map((item, key) => {
                  return (
                    <tr key={key}>
                      <td>{key + 1}</td>
                      <td>{item.start_date ? item.start_date : ''}</td>
                      <td>{item.end_date ? item.end_date : ''}</td>
                      <td><a href={item.item_id ? "/records/" + item.item_id : ''} target="_blank">
                          {item.item_id || ''}</a>
                      </td>
                      <td>{getTaskStatusLabel(item.task_status)}</td>
                      <td>{getTaskResult(item.task_result)}</td>
                    </tr>
                  )
                })
              }
            </tbody>
          </table>
        </div>
      </div>
    )
  }
}

class ItemTypeComponent extends React.Component {

  constructor() {
    super();
    this.state = {
      item_types: null,
      selected_item_type: '-1'
    };
    this.getListItemType = this.getListItemType.bind(this);
    this.onCbxItemTypeChange = this.onCbxItemTypeChange.bind(this);
    this.onBtnDownloadClick = this.onBtnDownloadClick.bind(this);
  }

  componentDidMount() {
    this.getListItemType();
  }

  getListItemType() {
    const that = this;
    $.ajax({
      url: "/api/itemtypes/lastest?type=normal_type",
      type: 'GET',
      dataType: "json",
      success: function (data) {
        data = [
          null,
          ...data
        ];
        that.setState({ item_types: data });
      },
      error: function (error) {
        console.log(error);
        alert(error_get_lstItemType);
      }
    });
  }

  onCbxItemTypeChange(event) {
    this.setState({ selected_item_type: event.target.value });
  }

  onBtnDownloadClick() {
    const { selected_item_type } = this.state;
    $.ajax({
      url: urlDownloadTemplate,
      type: 'POST',
      data: JSON.stringify({ item_type_id: selected_item_type }),
      contentType: "application/json; charset=utf-8",
      success: function (response, status, xhr) {
        var fileName = "";
        var disposition = xhr.getResponseHeader('Content-Disposition');
        if (disposition && disposition.indexOf('attachment') !== -1) {
          var filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
          var matches = filenameRegex.exec(disposition);
          if (matches != null && matches[1]) {
            fileName = matches[1].replace(/['"]/g, '');
          }
        }

        fileName = decodeURIComponent(fileName.replace(/\+/g, '%20'));
        const blob = new Blob([response], { type: 'text/' + file_format });
        if (window.navigator && window.navigator.msSaveOrOpenBlob) {
          window.navigator.msSaveOrOpenBlob(blob, fileName);
        } else {
          const url = window.URL.createObjectURL(blob);
          const tempLink = document.createElement('a');
          tempLink.style.display = 'none';
          tempLink.href = url;
          tempLink.download = fileName;
          document.body.appendChild(tempLink);
          tempLink.click();

          setTimeout(function () {
            document.body.removeChild(tempLink);
            window.URL.revokeObjectURL(url);
          }, 200)
        }
      },
      error: function (error) {
        console.log(error);
        alert(error_download);
      }
    });
  }

  render() {
    const { item_types, selected_item_type } = this.state;
    const select_options = item_types && item_types.map(item => {
      if (item === null) {
        return <option value={'-1'} selected={true}></option>;
      } else {
        return <option value={item.id} selected={item.id === selected_item_type}>{item.name} ({item.id})</option>
      }
    });

    return (
      <div class="item_type_compoment">
        <h4>{item_type_templates}</h4>
        <div class="row">
          <div class="col-md-12 form-inline">
            <div class="form-group">
              <label style={{ marginRight: ".5rem" }}>{item_type}:</label>
              <select class="form-control" style={{ marginRight: ".5rem" }} onChange={this.onCbxItemTypeChange}>
                {select_options}
              </select>
            </div>
            <button class="btn btn-primary" disabled={selected_item_type === '-1'} onClick={this.onBtnDownloadClick}>
              <span class="glyphicon glyphicon-cloud-download icon"></span>{download}
            </button>
          </div>
        </div>
      </div>
    );
  }
}

$(function () {
  ReactDOM.render(
    <MainLayout />,
    document.getElementById('root')
  )
});
