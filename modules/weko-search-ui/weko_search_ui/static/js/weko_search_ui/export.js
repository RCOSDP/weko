const last_item_id_label = document.getElementById("last_item_id").value;
const add_filter_label = document.getElementById("add_filter").value;
const item_type_label = document.getElementById("item_type").value;
const item_id_label = document.getElementById("item_id").value;
const export_item_label = document.getElementById("export_item").value;
const download_url_label = document.getElementById("download_url").value;
const status_label = document.getElementById("status").value;
const start_time_label = document.getElementById('start_time').value;
const finish_time_label = document.getElementById('finish_time').value;
const export_label = document.getElementById("export").value;
const export_messaage = document.getElementById("export_messaage").value;
const cancel_messaage = document.getElementById("cancel_messaage").value;
const run_label = document.getElementById("run").value;
const cancel_label = document.getElementById("cancel").value;
const celery_not_run = document.getElementById("celery_not_run").value;
const lifetime_not_one_day = document.getElementById("lifetime_not_one_day").value;
const error_get_lstItemType = document.getElementById("error_get_lstItemType").value;
const error_get_lastItemId = document.getElementById("error_get_lastItemId").value;

const urlExportAll = window.location.origin + '/admin/items/bulk-export/export_all'
const urlExportStatus = window.location.origin + '/admin/items/bulk-export/check_export_status'
const urlCancelExport = window.location.origin + '/admin/items/bulk-export/cancel_export'
const urlDownload = window.location.origin + '/admin/items/bulk-export/download'
function closeError() {
  $('#errors').empty();
}

class MainLayout extends React.Component {

  constructor() {
    super()
    this.state = {}
  }

  componentDidMount() {
    const header = document.getElementsByClassName('content-header')[0];
    if (header) {
      const errorElement = document.createElement('div');
      errorElement.setAttribute('id', 'errors');
      header.insertBefore(errorElement, header.firstChild);
    }
  }

  render() {
    return (
      <div>
        <ExportComponent />
      </div>
    )
  }
}

class ExportComponent extends React.Component {
  constructor() {
    super()
    this.state = {
      show: false,
      esportRunMessage: "",
      exportStatus: false,
      uriStatus: false,
      checkExportSttInterval: null,
      interval_time: 3000,
      isDisableExport: false,
      isDisableCancel: true,
      taskStatus: "",
      startTime: "",
      finishTime: "",
      isExport: false,
      confirmMessage: "",
      last_item_id: "",
      item_types: null,
      selected_item_type: '-1',
      item_id_range: ""
    }
    this.getLastItemId = this.getLastItemId.bind(this);
    this.getListItemType = this.getListItemType.bind(this);
    this.InputItemIdChange = this.InputItemIdChange.bind(this);
    this.SelectItemTypeChange = this.SelectItemTypeChange.bind(this);
    this.handleExport = this.handleExport.bind(this);
    this.handleCancel = this.handleCancel.bind(this);
    this.handleClose = this.handleClose.bind(this);
    this.handleConfirm = this.handleConfirm.bind(this);
    this.handleExecute = this.handleExecute.bind(this);
  }

  componentDidMount() {
    this.getLastItemId();
    this.getListItemType();
    this.checkExportStatus();
  }

  getLastItemId() {
    const that = this;
    $.ajax({
      url: "/api/get_last_item_id",
      type: 'GET',
      dataType: "json",
      success: function (response) {
        if (response.data) {
          that.setState({ last_item_id: response.data.last_id });
        }
      },
      error: function (error) {
        console.log(error);
        alert(error_get_lastItemId);
      }
    });
  }

  getListItemType() {
    const that = this;
    $.ajax({
      url: "/api/itemtypes/lastest?type=all_type",
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

  SelectItemTypeChange(event) {
    const me = this;
    me.setState({ selected_item_type: event.target.value });
  }

  InputItemIdChange(event) {
    const me = this;
    let reg_value = event.target.value.match('[0-9]*-?[0-9]*');
    if (reg_value) {
      me.setState({ item_id_range: reg_value[0] });
    }
  }

  handleExecute() {
    const {
      isExport
    } = this.state
    if (isExport) {
      this.handleExport();
    }
    else {
      this.handleCancel();
    }
    this.setState({
      show: false
    });
  }

  handleConfirm(isExport) {
    const me = this;
    me.setState({
      show: true,
      isExport: isExport,
      confirmMessage: isExport ? export_messaage : cancel_messaage
    });
  }

  handleCancel() {
    const me = this;
    $.ajax({
      type: 'GET',
      url: urlCancelExport,
      success: function (response) {
        if (response.data) {
          if (!response.data.cancel_status) {
            me.setState({
              isDisableExport: true,
              isDisableCancel: false
            })
          } else {
            me.setState({
              isDisableExport: response.data.export_status,
              isDisableCancel: !response.data.export_status,
              taskStatus: response.data.status
            })
          }
        }
      },
      error: function () {
        $('#errors').append(
          '<div class="alert alert-danger alert-dismissable">' +
          '<button type="button" class="close" data-dismiss="alert" aria-hidden="true">' +
          '&times;</button>' + internal_server_error.value + '</div>');
      }
    });
  }

  handleExport() {
    const me = this;
    const {
      selected_item_type,
      item_id_range,
    } = me.state
    closeError();
    $.ajax({
      url: urlExportAll,
      type: 'POST',
      data: JSON.stringify({
        item_type_id: selected_item_type,
        item_id_range: item_id_range
      }),
      contentType: "application/json; charset=utf-8",
      dataType: "json",
      success: function () {
        me.setState({
          isDisableExport: response.data.export_status,
          isDisableCancel: !response.data.export_status,
          taskStatus: response.data.status,
          startTime: response.data.start_time
        });
      },
      error: function () {
        $('#errors').append(
          '<div class="alert alert-danger alert-dismissable">' +
          '<button type="button" class="close" data-dismiss="alert" aria-hidden="true">' +
          '&times;</button>' + internal_server_error.value + '</div>');
      }
    });
  }

  checkExportStatus() {
    const me = this;
    closeError();
    $.ajax({
      type: 'GET',
      url: urlExportStatus,
      dataType: 'json',
      async: false,
      success: function (response) {
        if (response.data) {
          if (!me.state.checkExportSttInterval) {
            let checkExportSttInterval = setInterval(me.checkExportStatus.bind(me),
              me.state.interval_time);
            me.setState({
              checkExportSttInterval: checkExportSttInterval
            });
          }
          me.setState({
            esportRunMessage: response.data.export_run_msg,
            exportStatus: response.data.export_status,
            uriStatus: response.data.uri_status,
            isDisableExport: response.data.export_status || !response.data.celery_is_run || !response.data.is_lifetime,
            isDisableCancel: !response.data.export_status,
            taskStatus: response.data.status,
            startTime: response.data.start_time,
            finishTime: response.data.finish_time
          });
          if (!response.data.celery_is_run) {
            $('#errors').append(
              '<div class="alert alert-danger alert-dismissable">' +
              '<button type="button" class="close" data-dismiss="alert" aria-hidden="true">' +
              '&times;</button>' + celery_not_run + '</div>');
          }
          if (!response.data.is_lifetime) {
            $('#errors').append(
              '<div class="alert alert-danger alert-dismissable">' +
              '<button type="button" class="close" data-dismiss="alert" aria-hidden="true">' +
              '&times;</button>' + lifetime_not_one_day + '</div>');
          }
          if (response.data.error_message) {
            if (response.data.error_message.length > 0) {
              $('#errors').append(
                '<div class="alert alert-danger alert-dismissable">' +
                '<button type="button" class="close" data-dismiss="alert" aria-hidden="true">' +
                '&times;</button>' + response.data.error_message + '</div>');
            }
          }
        }
      },
      error: function () {
        $('#errors').append(
          '<div class="alert alert-danger alert-dismissable">' +
          '<button type="button" class="close" data-dismiss="alert" aria-hidden="true">' +
          '&times;</button>' + internal_server_error.value + '</div>');
      }
    });
  }

  handleClose() {
    this.setState({
      show: false
    });
  }

  render() {
    const {
      show,
      isDisableExport,
      isDisableCancel,
      taskStatus,
      startTime,
      finishTime,
      esportRunMessage,
      exportStatus,
      uriStatus,
      confirmMessage,
      last_item_id,
      item_types,
      selected_item_type,
      item_id_range,
    } = this.state
    const select_options = item_types && item_types.map(it => {
      if (it === null) {
        return <option value={'-1'} selected={true}>All</option>
      } else {
        return <option value={it.id} selected={it.id === selected_item_type}>{it.name} ({it.id})</option>
      }
    });

    return (
      <div className="export_component">
        <div className="row layout">
          <div className="col-xs-12">
            <div className="row">
              <div className="col-xs-12">
                <label>{last_item_id_label}: {last_item_id}</label>
              </div>
            </div>
            <br />
            <div className="row">
              <div className="col-xs-12">
                <label>{add_filter_label}</label>
              </div>
            </div>
            <div className="row">
              <div className="col-xs-12 text-center">
                <div className="form-inline">
                  <label>{item_type_label}: </label>
                  <select disabled={isDisableExport} className="form-control" onChange={this.SelectItemTypeChange}>{select_options}</select>&nbsp;
                  <label>{item_id_label}: </label>
                  <input disabled={isDisableExport} className="form-control" type="text" id="item_id_range" pattern="[0-9]*-[0-9]*" onChange={this.InputItemIdChange} value={item_id_range} placeholder="e.g.: 50 or 1-100 or 1- or -100" />
                </div>
              </div>
            </div>
            <div className="row">
              <div className="col-xs-12">
                <label>{export_item_label}</label>
              </div>
            </div>
            <div className="row">
              <div className="col-xs-12 text-center">
                <button disabled={isDisableExport} variant="primary" type="button" className="btn btn-primary" onClick={() => this.handleConfirm(true)}>{export_label}</button>
                <button disabled={isDisableCancel} variant="secondary" type="button" className="btn btn-primary cancel" onClick={() => this.handleConfirm(false)}>{cancel_label}</button>
              </div>
              <div className="col-xs-12">
                <label>{esportRunMessage}</label>
              </div>
            </div>
            <div className="row">
              <div className="col-xs-12">
                <label>{status_label}: {taskStatus}</label>
              </div>
            </div>
            <div className="row">
              <div className="col-xs-12">
                <label>{start_time_label}: {startTime}</label>
              </div>
            </div>
            <div className="row">
              <div className="col-xs-12">
                <label>{finish_time_label}: {finishTime}</label>
              </div>
            </div>
            <div className="row">
              <div className="col-xs-12">
                <label>{download_url_label}</label>
              </div>
            </div>
            <div className="row" className={!uriStatus ? 'hidden' : ''} >
              <div className="col-xs-12">
                <a className={exportStatus ? 'linkDisabled' : ''} href={urlDownload}>{urlDownload}</a>
              </div>
            </div>
          </div>
        </div>
        <ReactBootstrap.Modal show={show} onHide={this.handleClose} dialogClassName="w-725">
          <ReactBootstrap.Modal.Header closeButton>
            {/* <h4 className="modal-title in_line">{change_identifier_mode}</h4> */}
          </ReactBootstrap.Modal.Header>
          <ReactBootstrap.Modal.Body>
            <div className="col-12">
              <div className="row text-center">
                {confirmMessage}
              </div>
            </div>
          </ReactBootstrap.Modal.Body>
          <ReactBootstrap.Modal.Footer>
            <div className="col-12">
              <div className="row text-center">
                <button variant="primary" type="button" className="btn btn-default" onClick={this.handleExecute}>{run_label}</button>
                <button variant="secondary" type="button" className="btn btn-default cancel" onClick={this.handleClose}>{cancel_label}</button>
              </div>
            </div>
          </ReactBootstrap.Modal.Footer>
        </ReactBootstrap.Modal>
      </div>
    )
  }
}

$(function () {
  ReactDOM.render(
    <MainLayout />,
    document.getElementById('root')
  )
});
