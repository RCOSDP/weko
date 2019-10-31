const import_label = document.getElementById("import").value;
const list = document.getElementById("list").value;
const import_file = document.getElementById("import_file").value;
const import_index = document.getElementById("import_index").value;
const work_flow = document.getElementById("work_flow").value;
const select_file = document.getElementById("select_file").value;
const select_index = document.getElementById("select_index").value;
const select_work_flow = document.getElementById("select_work_flow").value;
const selected_file_name = document.getElementById("selected_file_name").value;
const selected_index = document.getElementById("selected_index").value;
const selected_work_flow = document.getElementById("selected_work_flow").value;
const index_tree = document.getElementById("index_tree").value;
const designate_index = document.getElementById("designate_index").value;
const work_flow_2 = document.getElementById("work_flow_2").value;
const item_type = document.getElementById("item_type").value;
const flow = document.getElementById("flow").value;
const select = document.getElementById("select").value;
const cancel = document.getElementById("cancel").value;

class MainLayout extends React.Component {

    componentDidMount() {
      console.log("import is work");
      console.log("cancel", cancel);
    }

    render() {
      return(

        <div>
          <ul className="nav nav-tabs">
            <li role="presentation" className="active"><a href="#">{import_label}</a></li>
            <li role="presentation"><a href="#">{list}</a></li>
          </ul>

          <ImportComponent></ImportComponent>
        </div>
      )
    }
}

class ImportComponent extends React.Component {

    constructor(){
      super()
      this.state = {
        file: null,
        file_name: ""
      }
    }

    componentDidMount() {
      console.log("ImportComponent is work");
    }

    handleChangefile = (e) => {
      const file = e.target.files[0],
            reader = new FileReader();
        const file_name = this.getLastString(e.target.value, "\\")
        if (this.getLastString(favicon_name,".") !== 'tsv') {
          return false
        }

        this.setState({
          file_name:file_name,
         });

        reader.onload = (e) => {
            this.setState({
                file: reader.result,
            });
        }
        reader.readAsDataURL(file);
    }

    handleClickFile = () => {
      this.inputElement.click();
    }

    render() {
      const {file_name} = this.state
      return(
        <div className="container import_component">
          <div className="row layout">
            <div className="col-md-12">
              <div className="row">
                <div className="col-md-4">
                  <label>{import_file}</label>
                </div>
                <div className="col-md-8">
                  <div>
                    <button className="btn btn-primary" onClick={this.handleClickFile}>{select_file}</button>
                    <input
                      type="file"
                      className="input-file"
                      ref={input => this.inputElement = input}
                      accept=".tsv"
                      onChange={this.handleChangefile}
                      />
                  </div>
                  <div>
                    {
                      file_name ? <label>{file_name}</label> : <q>{selected_file_name}</q>
                    }
                  </div>
                </div>
              </div>
            </div>
            <div className="col-md-12">
              <div className="row">
                <div className="col-md-4">
                  <label>{import_index}</label>
                </div>
                <div className="col-md-8">
                  <div>
                    <button className="btn btn-primary">{select_index}</button>
                  </div>
                  <div>
                    <label>{selected_index}</label>
                  </div>
                </div>
              </div>
            </div>
            <div className="col-md-12">
              <div className="row">
                <div className="col-md-4">
                  <label>{work_flow}</label>
                </div>
                <div className="col-md-8">
                  <div>
                    <button className="btn btn-primary">{select_work_flow}</button>
                  </div>
                  <div>
                    <label>{selected_work_flow}</label>
                  </div>
                </div>
              </div>
            </div>
            <div className="col-md-12">
              <div className="row">
                <div className="col-md-4"><button className="btn btn-primary"><span className="glyphicon glyphicon-download-alt"></span>{import_label}</button></div>
              </div>
            </div>
          </div>
        </div>
      )
    }
}

$(function () {
    ReactDOM.render(
        <MainLayout/>,
        document.getElementById('root')
    )
});
