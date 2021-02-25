const export_all_label = document.getElementById("export_all").value;
const download_url_label = document.getElementById("download_url").value;
const export_label = document.getElementById("export").value;
const confirm_messaage = document.getElementById("confirm_messaage").value;
const run_label = document.getElementById("run").value;
const cancel_label = document.getElementById("cancel").value;
const workflows = JSON.parse($("#workflows").text() ? $("#workflows").text() : "");

const urlExportAll = window.location.origin + '/admin/items/export/export_all'
const urlExportStatus = window.location.origin + '/admin/items/export/check_export_status'
const urlCancelExport = window.location.origin + '/admin/items/export/cancel_export'
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
      download_url: "",
      show: false,
      export_status: "",
      export_interval: null,
      interval_time: 3000
    }
    this.handleExport = this.handleExport.bind(this);
    this.handleCancel = this.handleCancel.bind(this);
    this.handleRun = this.handleRun.bind(this);
    this.handleClose = this.handleClose.bind(this);
  }

  componentDidMount() {
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
      dataType: 'json',
      async: false,
      success: function (response) {
        console.log(response.data.cancel_status);
      }
    });
  }

  handleRun() {
    const that = this;
    this.setState({
      show: false
    });
    closeError();
    $.ajax({
      url: urlExportAll,
      type: 'GET',
      contentType: "application/json; charset=utf-8",
      dataType: "json",
      async: false,
      success: function (response) {
        if (response) {
          let export_interval = setInterval(that.checkExportStatus.bind(that), that.state.interval_time);
          that.setState({
            download_url: response.data.download_url,
            export_interval: export_interval
          });          
        }
      },
      error: function (error) {
        $('#errors').append(
          '<div class="alert alert-danger alert-dismissable">' +
          '<button type="button" class="close" data-dismiss="alert" aria-hidden="true">' +
          '&times;</button>' + internal_server_error + '</div>');
      }
    });
  }

  checkExportStatus() {
    const that = this;
    $.ajax({
      type: 'GET',
      url: urlExportStatus,
      dataType: 'json',
      async: false,
      success: function (response) {
        switch (response.export_status) {
          case 'FAILURE':
            // code block
            break;
          case 'SUCCESS':
            // code block
            clearInterval(that.state.export_interval);
            break;
        }
        that.setState({
          export_status: response.data.export_status
        });
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
      download_url,
      show,
      export_status
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
                <button variant="primary" type="button" className="btn btn-primary" onClick={this.handleExport}>{export_label}</button>
                <button variant="secondary" type="button" className="btn btn-primary cancel" onClick={this.handleCancel}>{cancel_label}</button>
              </div>
            </div>
            <div className="row">
              <div className="col-xs-12">
                <label>{download_url_label}</label>
              </div>
            </div>
            <div className="row">
              <div className="col-xs-12">
                <a className={export_status != 'SUCCESS' ? 'linkDisabled' : ''} href={download_url}>{download_url}</a>
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