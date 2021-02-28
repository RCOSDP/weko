const export_all_label = document.getElementById("export_all").value;
const download_url_label = document.getElementById("download_url").value;
const export_label = document.getElementById("export").value;
const confirm_messaage = document.getElementById("confirm_messaage").value;
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
    }
    this.handleExport = this.handleExport.bind(this);
    this.handleCancel = this.handleCancel.bind(this);
    this.handleRun = this.handleRun.bind(this);
    this.handleClose = this.handleClose.bind(this);
  }

  componentDidMount() {
    this.checkExportStatus();
  }

  handleExport() {
    this.setState({
      show: true
    });
  }

  handleCancel() {
    $.ajax({
      type: 'GET',
      url: urlCancelExport,
      success: function (response) {
        if (response) {
          thisComponent.setState({
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

  handleRun() {
    const thisComponent = this;
    this.setState({
      show: false
    });
    closeError();
    $.ajax({
      url: urlExportAll,
      type: 'GET',
      success: function () {
        let checkExportSttInterval = setInterval(thisComponent.checkExportStatus.bind(thisComponent),
          thisComponent.state.interval_time);
        thisComponent.setState({
          checkExportSttInterval: checkExportSttInterval,
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
    const thisComponent = this;
    closeError();
    $.ajax({
      type: 'GET',
      url: urlExportStatus,
      dataType: 'json',
      async: false,
      success: function (response) {
        if (response) {
          thisComponent.state.checkExportSttInterval && !response.data.export_status
            && clearInterval(thisComponent.state.checkExportSttInterval);
          thisComponent.setState({
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
      uriStatus
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
                <button disabled={isDisableExport} variant="primary" type="button" className="btn btn-primary" onClick={this.handleExport}>{export_label}</button>
                <button disabled={isDisableCancel} variant="secondary" type="button" className="btn btn-primary cancel" onClick={this.handleCancel}>{cancel_label}</button>
              </div>
            </div>
            <div className="row">
              <div className="col-xs-12">
                <label>{download_url_label}</label>
              </div>
            </div>
            <div className="row" className={!uriStatus ? 'hidden' : ''} >
              <div className="col-xs-12">
                <a className={!exportStatus ? 'linkDisabled' : ''} href={urlDownload}>{urlDownload}</a>
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
                {confirm_messaage}
              </div>
            </div>
          </ReactBootstrap.Modal.Body>
          <ReactBootstrap.Modal.Footer>
            <div className="col-12">
              <div className="row text-center">
                <button variant="primary" type="button" className="btn btn-default" onClick={this.handleRun}>{run_label}</button>
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