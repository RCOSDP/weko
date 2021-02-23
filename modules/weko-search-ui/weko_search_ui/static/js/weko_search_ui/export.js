const export_all_label = document.getElementById("export_all").value;
const download_url_label = document.getElementById("download_url").value;
const export_label = document.getElementById("export").value;
const confirm_messaage = document.getElementById("confirm_messaage").value;
const run_label = document.getElementById("run").value;
const cancel_label = document.getElementById("cancel").value;
const workflows = JSON.parse($("#workflows").text() ? $("#workflows").text() : "");
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
        <ExportComponent/>
      </div>
    )
  }
}

class ExportComponent extends React.Component {

  constructor() {
    super()
    this.state = {
      download_url: "",
      show: false
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
    alert('Hello Cancel')  
  }

  handleRun() {  
    alert('Hello Run')  
    this.setState({
      show: false
    });
  }

  handleClose() {
    this.setState({
      show: false
    });
  }
  
  render() {
    const {
      download_url
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
                <a href={download_url}>{download_url}</a>
              </div>
            </div>
          </div>                  
        </div>
        <ReactBootstrap.Modal show={this.state.show} onHide={this.handleClose} dialogClassName="w-725">
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