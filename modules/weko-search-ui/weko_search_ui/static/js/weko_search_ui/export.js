const export_all_label = document.getElementById("export_all").value;
const download_url_label = document.getElementById("download_url").value;
const export_label = document.getElementById("export").value;
const export_messaage = document.getElementById("export_messaage").value;
const cancel_messaage = document.getElementById("cancel_messaage").value;
const run_label = document.getElementById("run").value;
const cancel_label = document.getElementById("cancel").value;

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
      exportStatus: false,
      uriStatus: false,
      checkExportSttInterval: null,
      interval_time: 3000,
      isDisableExport: false,
      isDisableCancel: true,
      isExport: false,
      confirmMessage: ""
    }
    this.handleExport = this.handleExport.bind(this);
    this.handleCancel = this.handleCancel.bind(this);
    this.handleClose = this.handleClose.bind(this);
    this.handleConfirm = this.handleConfirm.bind(this);
    this.handleExecute = this.handleExecute.bind(this);
  }

  componentDidMount() {
    this.checkExportStatus();
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
          me.setState({
            isDisableExport: !response.data.cancel_status,
            isDisableCancel: response.data.cancel_status
          });
        }
      },
      error: function () {
        $('#errors').append(
          '<div class="alert alert-danger alert-dismissable">' +
          '<button type="button" class="close" data-dismiss="alert" aria-hidden="true">' +
          '&times;</button>' + internal_server_error + '</div>');
      }
    });
  }

  handleExport() {
    const me = this;
    closeError();
    $.ajax({
      url: urlExportAll,
      type: 'GET',
      success: function () {
        me.setState({
          isDisableExport: true,
          isDisableCancel: false
        });
      },
      error: function () {
        $('#errors').append(
          '<div class="alert alert-danger alert-dismissable">' +
          '<button type="button" class="close" data-dismiss="alert" aria-hidden="true">' +
          '&times;</button>' + internal_server_error + '</div>');
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
            exportStatus: response.data.export_status,
            uriStatus: response.data.uri_status,
            isDisableExport: response.data.export_status,
            isDisableCancel: !response.data.export_status
          });
        }
      },
      error: function () {
        $('#errors').append(
          '<div class="alert alert-danger alert-dismissable">' +
          '<button type="button" class="close" data-dismiss="alert" aria-hidden="true">' +
          '&times;</button>' + internal_server_error + '</div>');
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
      exportStatus,
      uriStatus,
      confirmMessage
    } = this.state
    return (
      <div className="export_component">
        <div className="row layout">
          <div className="col-xs-12">
            <div className="row">
              <div className="col-xs-12">
                <label>{export_all_label}</label>
              </div>
            </div>
            <div className="row">
              <div className="col-xs-12 text-center">
                <button disabled={isDisableExport} variant="primary" type="button" className="btn btn-primary" onClick={() => this.handleConfirm(true)}>{export_label}</button>
                <button disabled={isDisableCancel} variant="secondary" type="button" className="btn btn-primary cancel" onClick={() => this.handleConfirm(false)}>{cancel_label}</button>
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