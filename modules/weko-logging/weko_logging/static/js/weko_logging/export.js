const export_logs_label = document.getElementById("export_logs").value;
const download_url_label = document.getElementById("download_url").value;
const status_label = document.getElementById("status").value;
const export_label = document.getElementById("export").value;
const export_message = document.getElementById("export_message").value;
const cancel_message = document.getElementById("cancel_message").value;
const run_label = document.getElementById("run").value;
const cancel_label = document.getElementById("cancel").value;
const celery_not_run = document.getElementById("celery_not_run").value;
const internal_server_error = document.getElementById("internal_server_error").value;

const urlExportAll = window.location.origin + '/admin/logs/export/export'
const urlExportStatus = window.location.origin + '/admin/logs/export/check_export_status'
const urlCancelExport = window.location.origin + '/admin/logs/export/cancel_export'

function closeError() {
  $('#errors').empty();
}

class ExportComponent extends React.Component {
  constructor() {
    super()
    this.state = {
      showModal: false,
      checkExportSttInterval: null,
      checkStatusInterval: 3000,
      isDisableExport: false,
      isDisableCancel: true,
      taskStatus: "",
      isExport: false,
      confirmMessage: "",
      downloadLink: "",
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
    const { isExport } = this.state
    if (isExport) {
      this.handleExport();
    } else {
      this.handleCancel();
    }
    this.setState({
      showModal: false
    });
  }

  handleConfirm(isExport) {
    this.setState({
      showModal: true,
      isExport: isExport,
      confirmMessage: isExport ? export_message : cancel_message
    });
  }

  handleCancel() {
    fetch(urlCancelExport, { method: 'GET' })
      .then(response => response.json())
      .then(data => {
        if (data.data) {
          if (!data.data.cancel_status) {
            this.setState({
              isDisableExport: true,
              isDisableCancel: false
            })
          } else {
            this.setState({
              isDisableExport: data.data.export_status,
              isDisableCancel: !data.data.export_status,
              taskStatus: data.data.status
            })
          }
        }
      })
      .catch(() => {
        $('#errors').append(
          '<div class="alert alert-danger alert-dismissable">' +
          '<button type="button" class="close" data-dismiss="alert" aria-hidden="true">' +
          '&times;</button>' + internal_server_error + '</div>');
      });
  }

  handleExport() {
    closeError();
    fetch(urlExportAll, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json charset=utf-8',
      },
      body: JSON.stringify({})
    })
      .then(response => response.json())
      .then(data => {
        if (data.data) {
          if (!data.data.export_status) {
            this.setState({
              isDisableExport: true,
              isDisableCancel: false
            })
          } else {
            this.setState({
              isDisableExport: data.data.export_status,
              isDisableCancel: !data.data.export_status,
              taskStatus: data.data.status
            })
          }
        }
      })
      .catch(() => {
        $('#errors').append(
          '<div class="alert alert-danger alert-dismissable">' +
          '<button type="button" class="close" data-dismiss="alert" aria-hidden="true">' +
          '&times;</button>' + internal_server_error + '</div>');
      });
  }

  checkExportStatus() {
    closeError();
    fetch(urlExportStatus, { method: 'GET' })
      .then(response => response.json())
      .then(data => {
        const response = data.data;
        if (response) {
          if (!this.state.checkExportSttInterval) {
            let checkExportSttInterval = setInterval(this.checkExportStatus.bind(this),
              this.state.checkStatusInterval);
            this.setState({
              checkExportSttInterval: checkExportSttInterval
            });
          }
          const urlDownload = response.download_link;
          this.setState({
            downloadLink: urlDownload,
            isDisableExport: data.data.export_status || !data.data.celery_is_run,
            isDisableCancel: !data.data.export_status,
            taskStatus: data.data.status
          });
          if (!data.data.celery_is_run) {
            $('#errors').append(
              '<div class="alert alert-danger alert-dismissable">' +
              '<button type="button" class="close" data-dismiss="alert" aria-hidden="true">' +
              '&times;</button>' + celery_not_run + '</div>');
          }
          if (data.data.error_message) {
            if (data.data.error_message.length > 0) {
              $('#errors').append(
                '<div class="alert alert-danger alert-dismissable">' +
                '<button type="button" class="close" data-dismiss="alert" aria-hidden="true">' +
                '&times;</button>' + data.data.error_message + '</div>');
            }
          }
        }
      }
      )
      .catch(() => {
        $('#errors').append(
          '<div class="alert alert-danger alert-dismissable">' +
          '<button type="button" class="close" data-dismiss="alert" aria-hidden="true">' +
          '&times;</button>' + internal_server_error + '</div>');
      });
  }

  handleClose() {
    this.setState({
      showModal: false
    });
  }

  render() {
    const {
      showModal,
      isDisableExport,
      isDisableCancel,
      taskStatus,
      confirmMessage,
      downloadLink,
    } = this.state;

    const downloadLinkEnabled = downloadLink && (taskStatus === 'SUCCESS');
    const canExport = !isDisableExport && (!taskStatus || ['SUCCESS', 'FAILURE', 'REVOKED'].includes(taskStatus));
    const canCancel = !isDisableCancel && (taskStatus && !['SUCCESS', 'FAILURE', 'REVOKED'].includes(taskStatus))

    return (
      <div className="export_component">
        <div className="row layout">
          <div className="col-xs-12">
            <div className="row">
              <div className="col-xs-12">
                <label>{export_logs_label}</label>
              </div>
            </div>
            <div className="row">
              <div className="col-xs-12 text-center">
                <button disabled={!canExport} variant="primary" type="button" className="btn btn-primary" onClick={() => this.handleConfirm(true)}>{export_label}</button>
                <button disabled={!canCancel} variant="secondary" type="button" className="btn btn-primary cancel" onClick={() => this.handleConfirm(false)}>{cancel_label}</button>
              </div>
            </div>
            <div className="row">
              <div className="col-xs-12">
                <label>{status_label}: {taskStatus}</label>
              </div>
            </div>
            <div className="row">
              <div className="col-xs-12">
                <label>{download_url_label}</label>
              </div>
            </div>
            <div className={!downloadLinkEnabled ? 'row hidden' : 'row'} >
              <div className="col-xs-12">
                <a className={!downloadLinkEnabled ? 'linkDisabled' : ''} href={downloadLink}>{downloadLink}</a>
              </div>
            </div>
          </div>
        </div>
        <ReactBootstrap.Modal show={showModal} onHide={this.handleClose} dialogClassName="w-725">
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
    );
  }
}

class MainLayout extends React.Component {

  constructor() {
    super();
    this.state = {};
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
    return (<div><ExportComponent /></div>);
  }
}

$(function () {
  ReactDOM.render(
    <MainLayout />,
    document.getElementById('root')
  );
});
