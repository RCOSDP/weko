class ComponentFeedbackMail extends React.Component {
    constructor(props) {
        super(props);
        this.style_component = {
            "margin-top": "15px",
            "font-size": "18px",
        }
        this.margin_left = {
            "margin-left": "10%",
        }
        this.style_radioBtn = {
            "width" : "18px",
            "height" : "18px",
        }
    }
    render() {
        return (
            <div className="form-group" style = {this.style_component}>
                <span className="control-label col-xs-2">ON/OFF</span>
                <div class="controls col-xs-10">
                    <div className="form-group">
                        <span><input style = {this.style_radioBtn} type="radio"  name="feedback_mail" value="send"/>Send</span>
                        <span  style = {this.margin_left}><input style = {this.style_radioBtn} type="radio" name="feedback_mail" value="not_send"/>Do not send</span>
                    </div>
                </div>
            </div>
        )
    }
}

class ComponentExclusionTarget extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
          list_email: []
        }
        this.style_component = {
            "margin-top": "15px",
            "font-size": "18px",
        }
        this.margin_left = {
            "margin-left": "10%",
        }
        this.style_radioBtn = {
            "width" : "18px",
            "height" : "18px",
        }
        this.style_button = {
            "box-shadow": "4px 4px 5px #7D7D7D",
            "background-color": "white",
            "border": "1px ridge black"
        }
        this.style_selected_box = {
            "margin-top": "15px",
            "width": "70%",
            "heiht": "50px",
            "border": "1px inset black",
            "display": "inline-block",
            "padding": "10px",
        }
        this.style_full_size = {
            "width": "100% !important;%",
        }
        this.style_deleteBtn = {
            "margin-left": "5px",
            "margin-bottom": "10px",
        }
        this.deleteCommand = this.deleteCommand.bind(this);
        this.searchCommand = this.searchCommand.bind(this);
    }

    componentDidMount() {
      let thisClass = this
      fetch("/api/admin/get_feedback_mail")
      .then(res => res.json())
      .then((result) => {
        if (result.error) {
          // Display error
          return;
        }
        let mailData = result.data;
        let sendData = result.is_sending_feedback;

        if (sendData) {
          $("input[name=feedback_mail][value='send']").prop("checked", true);
        } else {
          $("input[name=feedback_mail][value='not_send']").prop("checked", true);
        }
        if ($.isEmptyObject(mailData)) {
          return;
        }
        let innerHTML = [];
        for (let id in mailData) {
          innerHTML.push(<option value={mailData[id].author_id}>{mailData[id].email}</option>);
        }
        thisClass.setState({
          list_email: innerHTML
        });
      });
    }

    deleteCommand() {

    }
    searchCommand(){
      this.props.bindingValueOfComponent("showModalSearch", true);
    }
    render() {
        return (
            <div className="form-group"  style = {this.style_component}>
                <span className="control-label col-xs-2">Send exclusion target persons</span>
                <div className="controls col-xs-10">
                    <div>
                        <ReactBootstrap.Button variant="primary" onClick={this.searchCommand}>
                            <i className = "glyphicon glyphicon-search"></i>&nbsp;From author DB
                        </ReactBootstrap.Button>
                    </div>
                    <div style = {this.style_full_size}>
                        <select multiple style = {this.style_selected_box}>
                            {this.state.list_email}
                        </select>
                        <button className="btn btn-danger delete-button style-my-button" onClick={this.deleteCommand} style = {this.style_deleteBtn}>
                            <span className="glyphicon glyphicon-trash" aria-hidden="true"></span>
                            &nbsp;Delete
                        </button>
                    </div>
                </div>
            </div>
        )
    }
}

class TableUserEmailComponent extends React.Component {
  constructor(props){
    super(props);
    this.state = {
      listUser: this.props.listUser,
    }
    this.style_table_modal = {
      "width": "100%"
    }
    this.style_column = {
      "width" : "40%"
    }
    this.generateBodyTableUser = this.generateBodyTableUser.bind(this);
    this.importEmail = this.importEmail.bind(this);
  }
  static getDerivedStateFromProps(nextProps, prevState) {
    if (nextProps.listUser != prevState.listUser)
    {
      return {
        listUser: nextProps.listUser,
      }
    }
    return null;
  }
  generateBodyTableUser()
  {
    let tBodyElement = this.state.listUser.map((row) => {
      return (
        <tr>
          <td>{row._source.authorNameInfo[0].fullName}</td>
          <td>{row._source.emailInfo[0].email}</td>
          <td><button ref="btn" class="btn btn-info" onClick = {() => this.importEmail(row._source.pk_id, row._source.emailInfo[0].email)}>&nbsp;&nbsp;Import&nbsp;&nbsp;</button></td>
        </tr>
      )
    })
    return (
      <tbody >
        {tBodyElement}
      </tbody>
    )
  }
  importEmail(pk_id, email){
    console.log();
  }
  render(){
    return (
      <div className="col-sm-12 col-md-12">
        <table className="table table-striped" id="table_data" style = {this.style_table_modal}>
          <caption ></caption>
          <thead >
            <tr  className="success">
              <th  className="thWidth" style={this.style_column}>Name</th>
              <th  className="thWidth" style={this.style_column}>Mail Address</th>
              <th  className="alignCenter" ></th>
            </tr>
          </thead>
          {this.generateBodyTableUser()}
        </table>
      </div>
    )
  }
}

class SearchComponent extends React.Component {
  constructor(props){
    super(props);
    this.state = {
      searchKey : "",
    }
    this.searchEmail = this.searchEmail.bind(this);
    this.handleChange = this.handleChange.bind(this);
  }
  searchEmail(){
    let request = {
      searchKey: this.state.searchKey,
      pageNumber: 1,
    }
    fetch("/api/admin/search_email", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(request),
    })
    .then(res => res.json())
    .then((result) => {
      this.props.getListUser(result.hits.hits);
    });
  }
  handleChange(event){
    this.setState({ searchKey: event.target.value });
    event.preventDefault();
  }
  render(){
    return (
      <div>
        <div className="col-sm-5 col-md-5">
          <input className="form-control" placeholder="" type="text" onChange={this.handleChange} value={this.state.searchKey}/>
        </div>
        <div className="col-sm-1 col-md-1">
          <button className="btn btn-info" type="button" onClick={this.searchEmail}>&nbsp;&nbsp;
            Search&nbsp;&nbsp;
          </button>
        </div>
      </div>
    )
  }
}

class Pagination extends React.Component {
  constructor(props) {
    super(props);
  }
  render () {
    return (
      <div  className="row">
        <div  className="col-sm-12 col-md-12 alignCenter">
          <ul  className="pagination">
            <li >
              <a  href="#"><span  aria-hidden="true">&lt;</span></a>
            </li>
            <li  id="pageLink_1">
              <a  href="#">1</a>
            </li>
            <li >
              <a  href="#"><span  aria-hidden="true">&gt;</span></a>
            </li>
          </ul>
        </div>
      </div>
    )
  }
}

class ModalBodyComponent extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      listUser: [],
    }
    this.margin_left_page = {
      "margin-left": "60%",
    }
    this.getListUser = this.getListUser.bind(this);
  }
  getListUser(data)
  {
    this.setState({listUser: data});
  }
  render() {
    return (
      <div className="container-modal">
        <div className="row">
          <div className="col-sm-12 col-md-12 col-md-12">
            <div className="row">
              <div className="row">
                <SearchComponent getListUser = {this.getListUser}/>
              </div>
              <div className="row">
                <TableUserEmailComponent listUser = {this.state.listUser}/>
              </div>
              <div style={this.margin_left_page}>
                <Pagination />
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }
}
class ModalFooterComponent extends React.Component {
  constructor(props){
    super(props);
    this.handleClose = this.handleClose.bind(this);
  }
  handleClose() {
    this.props.bindingValueOfComponent("showModalSearch", false);
  }
  render(){
    return (
      <ReactBootstrap.Button variant="secondary" onClick={this.handleClose}>
        <span className="glyphicon glyphicon-remove"></span>
        Close
      </ReactBootstrap.Button>
    )
  }
}

class ModalComponent extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      show: this.props.showModalSearch,
    };
  }
  static getDerivedStateFromProps(nextProps, prevState) {
    if (nextProps.showModalSearch != prevState.showModalSearch)
    {
      return {
        show: nextProps.showModalSearch,
      }
    }
    return null;
  }
  render(){
    return (
      <ReactBootstrap.Modal show={this.state.show} onHide={this.handleClose} dialogClassName="feedback-mail-modal">
        <ReactBootstrap.Modal.Body className="feedback-mail-modal-body">
          <ModalBodyComponent/>
        </ReactBootstrap.Modal.Body>
        <ReactBootstrap.Modal.Footer>
          <ModalFooterComponent bindingValueOfComponent = {this.props.bindingValueOfComponent}/>
        </ReactBootstrap.Modal.Footer>
      </ReactBootstrap.Modal>
    )
  }
}

class ComponentButtonLayout extends React.Component {
    constructor(props) {
        super(props);
        this.style_component = {
            "margin-top": "15px",
            "font-size": "18px",
        }
        this.style_button = {
            "width" : "100px",
            "border-radius" : "5%",
            "font-weight" : "600",
        }
        this.saveCommand = this.saveCommand.bind(this);
        this.sendCommand = this.sendCommand.bind(this);
    }

    saveCommand(event) {
      // TODO: Change to real data binding from modal
      let mailData = [
        {
          "author_id": "1562301336829",
          "email": "vothanhhieu@gcs.com"
        },
        {
          "author_id": "1562301436629",
          "email": "zannaghazi@gcs.com"
        },
        {
          "author_id": "1562301453501",
          "email": "meoloca@gcs.com"
        }
      ];

      let is_sending_feedback = false;
      if ($('input[name=feedback_mail]:checked').val() == "send") {
        is_sending_feedback = true;
      }

      let request_param = {
        "data": mailData,
        "is_sending_feedback": is_sending_feedback
      }

      fetch(
        "/api/admin/update_feedback_mail",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify(request_param)
        }
      )
      .then(res => res.json())
      .then((result) => {
        if (result.success) {
          // TODO: Notify success message
          return;
        }else {
          // TODO: Notify error message
          error_message = result.error;
          return;
        }
      });
    }

    sendCommand(event){

    }

    render() {
      return (
        <div className="form-group" style={this.style_component}>
          <div className="col-xs-5">
            <button style={this.style_button} className="btn btn-primary" onClick={this.saveCommand}>
              Save
            </button>
          </div>
          <div className="col-xs-offset-10">
            <button style = {this.style_button} className="btn btn-primary" onClick={this.sendCommand}>
              Manual Send
            </button>
          </div>
        </div>
      )

    }
}

class MainLayout extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
          showModalSearch: false,
        }
        this.bindingValueOfComponent = this.bindingValueOfComponent.bind(this);
    }
    bindingValueOfComponent (key, value) {
      switch (key) {
        case "showModalSearch":
          this.setState({showModalSearch: value})
          break;
        default:
          break;
      }
    }
    render() {
        return (
            <div>
                <div className="row">
                    <ComponentFeedbackMail/>
                </div>
                <div className="row">
                    <ComponentExclusionTarget bindingValueOfComponent = {this.bindingValueOfComponent}/>
                </div>
                <div className="row">
                    <ComponentButtonLayout />
                </div>
                <div className="row">
                    <ModalComponent showModalSearch = {this.state.showModalSearch} bindingValueOfComponent = {this.bindingValueOfComponent}/>
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
