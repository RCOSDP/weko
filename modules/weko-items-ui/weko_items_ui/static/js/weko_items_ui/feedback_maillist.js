const NUM_OF_RESULT = 10;
const LIMIT_PAGINATION_NUMBER = 5;
const COMPONENT_SEARCH_EMAIL_NAME = document.getElementById("component-search-email-name").value;
const SEARCH_BUTTON_NAME = document.getElementById("search-button-name").value;
const DELETE_BUTTON_NAME = document.getElementById("delete-button-name").value;
const DUPLICATE_ERROR_MESSAGE = document.getElementById("duplicate-error-message").value;


class ComponentExclusionTarget extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      listEmail: [],
      selectedId: null
    }
    this.deleteCommand = this.deleteCommand.bind(this);
    this.searchCommand = this.searchCommand.bind(this);
    this.generateSelectedBox = this.generateSelectedBox.bind(this);
    this.handleClick = this.handleClick.bind(this)
    this.handleKeyPress = this.handleKeyPress.bind(this)
  }

  componentDidMount(){
    const activityID = $("#hidden_activity_id").val();
    let emails = [];
    $.ajax({
      url: "/workflow/get_feedback_maillist/" + activityID,
      async: false,
      method: "GET",
      success: function (response) {
        if (response.code) {
          emails = response.data || [];
        }
      }
    })
    this.props.bindingValueOfComponent('listEmail', emails);
  }

  componentWillReceiveProps(nextProps) {
    if (nextProps.listEmail !== this.state.listEmail) {
      this.setState({
        listEmail: [...nextProps.listEmail,] || [],
      })
    }
  }

  handleClick(id) {
    this.setState({
      selectedId: id
    })
  }

  handleKeyPress(event) {
    if (event.key === 'Enter') {
      const new_email = {
        author_id: "",
        email: event.target.value.trim()
      }
      if (this.props.addEmailToList(new_email)) {
        $('#custom_input_email').val('');
        $('#sltBoxListEmail').animate({
          scrollTop: $("#custom_input_email").offset().top
        }, 1000);
      }
    }
  }

  generateSelectedBox(listEmail) {
    return (
      <div class="list-group" className="style-selected-box" id="sltBoxListEmail">
        {
          listEmail.map((item, id) => {
            return (
              <a className={`list-group-item list-group-item-action ${this.state.selectedId === id && 'active'}`}
                onClick={() => {
                    this.handleClick(id)
                  }}
                key={id}
                value={item.author_id}
                // style={itemStyle}
                >
                  {item.email}
              </a>
            )
          })
        }
        <input class="list-group-item list-group-item-action"
          id="custom_input_email"
          placeholder="テキスト入力可"
          onKeyPress={(event) => {
            this.handleKeyPress(event)
          }}
        />
      </div>
    )
  }

  deleteCommand(event) {
    let selectedElement = $(".list-group-item.list-group-item-action.active").text();
    this.props.removeEmailFromList(selectedElement);
    this.handleClick(-1);
  }

  searchCommand() {
    this.props.bindingValueOfComponent("showModalSearch", true);
  }

  render() {
    return (
      <div className="col-sm-9 form-group style-component">
        <span className="control-label col-xs-3">{COMPONENT_SEARCH_EMAIL_NAME}</span>
        <div className="controls col-xs-9">
          <div>
            <ReactBootstrap.Button variant="primary" onClick={this.searchCommand}>
              <i className="glyphicon glyphicon-search"></i>&nbsp;{SEARCH_BUTTON_NAME}
            </ReactBootstrap.Button>
          </div>
          <div className="style-full-size">
            {this.generateSelectedBox(this.state.listEmail)}
            <button className="btn btn-danger delete-button style-my-button style-deleteBtn" onClick={this.deleteCommand}>
              <span className="glyphicon glyphicon-trash" aria-hidden="true"></span>
              &nbsp;{DELETE_BUTTON_NAME}
            </button>
          </div>
        </div>
      </div>
    )
  }
}

class ModalMessageComponent extends React.Component {
  constructor(props) {
    super(props);
  }
  render() {
    return (
      <div className="alert alert-info">
        Sorry，No results.
      </div>
    )
  }
}

class TableUserEmailComponent extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      listUser: this.props.listUser,
      firstRender: true,
    }
    this.generateBodyTableUser = this.generateBodyTableUser.bind(this);
    this.importEmail = this.importEmail.bind(this);
  }

  static getDerivedStateFromProps(nextProps, prevState) {
    if (nextProps.listUser != prevState.listUser) {
      return {
        listUser: nextProps.listUser,
        firstRender: false,
      }
    }
    return null;
  }

  generateBodyTableUser() {
    let tBodyElement = this.state.listUser.map((row) => (
      <tr key={row._source.pk_id.toString()}>
        <td>{row._source.authorNameInfo[0].fullName}</td>
        <td>{row._source.emailInfo[0].email}</td>
        <td className="text-right"><button className="btn btn-info" onClick={(event) => this.importEmail(event, row._source.pk_id, row._source.emailInfo[0].email)}>&nbsp;&nbsp;Import&nbsp;&nbsp;</button></td>
      </tr>
    )
    )
    return (
      <tbody >
        {tBodyElement}
      </tbody>
    )
  }

  importEmail(event, pk_id, email) {
    let listUser = [];
    $("#sltBoxListEmail > a").each(function () {
      listUser.push(this.value);
    });
    let isExist = listUser.includes(pk_id);
    if (!isExist) {
      event.target.disabled = true;
      let data = {
        "author_id": pk_id,
        "email": email
      }
      this.props.addEmailToList(data);
    }
    else {
      alert(DUPLICATE_ERROR_MESSAGE);
    }
  }
  render() {
    return (
      <div className="col-sm-12 col-md-12">
        <table className="table table-striped style-table-modal" id="table_data">
          <caption ></caption>
          <thead >
            <tr className="success">
              <th className="thWidth style-column">Name</th>
              <th className="thWidth style-column">Mail Address</th>
              <th className="alignCenter" ></th>
            </tr>
          </thead>
          {this.generateBodyTableUser()}
        </table>
        {this.state.firstRender == false && this.state.listUser.length == 0 ? <ModalMessageComponent /> : ""}
      </div>
    )
  }
}

class SearchComponent extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      searchKey: this.props.searchKey,
    }
    this.searchEmail = this.searchEmail.bind(this);
    this.handleChange = this.handleChange.bind(this);
  }
  searchEmail() {
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
        this.props.getListUser(result.hits.hits, result.hits.total);
      });
  }
  handleChange(event) {
    this.setState({ searchKey: event.target.value });
    this.props.getSearchKey(event.target.value);
    event.preventDefault();
  }
  render() {
    return (
      <div>
        <div className="col-sm-5 col-md-5">
          <input className="form-control" placeholder="" type="text" onChange={this.handleChange} value={this.state.searchKey} />
        </div>
        <div className="col-sm-1 col-md-1">
          <button class="btn btn-primary search-button" type="button" onClick={this.searchEmail}>&nbsp;&nbsp;
            <i class="fa fa-search-plus"></i>
            &nbsp;
            Search &nbsp;&nbsp;
          </button>
        </div>
      </div>
    )
  }
}

class Pagination extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      numOfResult: this.props.numOfResult,
      startPage: 1,
      endPage: 1,
      currentPage: 1,
      numOfPage: 1,
    }
    this.generatePagination = this.generatePagination.bind(this);
  }
  static getDerivedStateFromProps(nextProps, prevState) {
    if (nextProps.numOfResult != prevState.numOfResult) {
      let pageCount = nextProps.numOfResult / NUM_OF_RESULT;
      pageCount = parseInt(pageCount);
      if (nextProps.numOfResult % NUM_OF_RESULT != 0) {
        pageCount += 1;
      }
      let endPage = pageCount;
      let startPage = 1;
      if (pageCount > 5) {
        endPage = 5;
      }
      return {
        numOfResult: nextProps.numOfResult,
        numOfPage: pageCount,
        endPage: endPage,
        startPage: startPage,
      }
    }
    return null;
  }
  locatePageResult(pageNumber) {
    if (pageNumber < 1 || pageNumber > this.state.numOfPage) {
      return;
    }
    let startPage = this.state.startPage;
    let endPage = this.state.endPage;
    if (this.state.numOfPage > 5) {
      if (pageNumber > 2 && pageNumber < this.state.numOfPage - 2) {
        startPage = pageNumber - 2;
        endPage = pageNumber + 2;
      }
      else {
        if (pageNumber < 3) {
          startPage = 1;
          endPage = 5;
        }
        if (pageNumber > this.state.numOfPage - 2) {
          startPage = this.state.numOfPage - 4;
          endPage = this.state.numOfPage;
        }
      }
    }
    this.setState({
      currentPage: pageNumber,
      startPage: startPage,
      endPage: endPage
    });
    let request = {
      searchKey: this.props.searchKey,
      pageNumber: pageNumber,
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
        this.props.getListUser(result.hits.hits, result.hits.total);
      });
  }
  generatePagination() {
    let listPage = [];
    for (let i = this.state.startPage; i <= this.state.endPage; i++) {
      listPage.push(
        <li key={i.toString()} className={this.state.currentPage == i ? 'active' : ''}>
          <a href="#" onClick={() => this.locatePageResult(i)}>{i}</a>
        </li>
      )
    }
    return (
      <ul className="pagination">
        {this.state.numOfPage > LIMIT_PAGINATION_NUMBER ?
          <li >
            <a href="#" onClick={() => this.locatePageResult(1)} className={this.state.currentPage == 1 ? 'my-pagination-disabled' : ''}><span aria-hidden="true">&#8810;</span></a>
          </li> : null}
        <li >
          <a href="#" onClick={() => this.locatePageResult(this.state.currentPage - 1)} className={this.state.currentPage == 1 ? 'my-pagination-disabled' : ''}><span aria-hidden="true">&lt;</span></a>
        </li>
        {listPage}
        <li >
          <a href="#" onClick={() => this.locatePageResult(this.state.currentPage + 1)} className={this.state.currentPage == this.state.numOfPage ? 'my-pagination-disabled' : ''}><span aria-hidden="true">&gt;</span></a>
        </li>
        {this.state.numOfPage > LIMIT_PAGINATION_NUMBER ?
          <li >
            <a href="#" onClick={() => this.locatePageResult(this.state.numOfPage)} className={this.state.currentPage == this.state.numOfPage ? 'my-pagination-disabled' : ''}><span aria-hidden="true">&#8811;</span></a>
          </li> : null}
      </ul>
    )
  }
  render() {
    return (
      <div className="row">
        <div className="col-sm-12 col-md-12 text-center">
          {this.generatePagination()}
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
      numOfResult: 0,
      searchKey: "",
    }
    this.getListUser = this.getListUser.bind(this);
    this.getSearchKey = this.getSearchKey.bind(this);
  }
  getListUser(data, count) {
    this.setState({
      listUser: data,
      numOfResult: count
    });
  }
  getSearchKey(data) {
    this.setState({ searchKey: data });
  }
  render() {
    return (
      <div className="container-modal">
        <div className="row">
          <div className="col-sm-12 col-md-12 col-md-12">
            <div className="row">
              <div className="row">
                <SearchComponent getListUser={this.getListUser} searchKey={this.state.searchKey} getSearchKey={this.getSearchKey} />
              </div>
              <div className="row">
                <TableUserEmailComponent listUser={this.state.listUser} addEmailToList={this.props.addEmailToList} />
              </div>
              <div className="row">
                <Pagination numOfResult={this.state.numOfResult} searchKey={this.state.searchKey} getListUser={this.getListUser} />
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }
}
class ModalFooterComponent extends React.Component {
  constructor(props) {
    super(props);
    this.handleClose = this.handleClose.bind(this);
  }
  handleClose() {
    this.props.bindingValueOfComponent("showModalSearch", false);
  }
  render() {
    return (
      <ReactBootstrap.Button variant="secondary" onClick={this.handleClose}>
        <span className="glyphicon glyphicon-remove"></span> Close
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
    if (nextProps.showModalSearch != prevState.showModalSearch) {
      return {
        show: nextProps.showModalSearch,
      }
    }
    return null;
  }
  render() {
    return (
      <ReactBootstrap.Modal show={this.state.show} onHide={this.handleClose} dialogClassName="feedback-mail-modal">
        <ReactBootstrap.Modal.Body className="feedback-mail-modal-body">
          <ModalBodyComponent addEmailToList={this.props.addEmailToList} />
        </ReactBootstrap.Modal.Body>
        <ReactBootstrap.Modal.Footer>
          <ModalFooterComponent bindingValueOfComponent={this.props.bindingValueOfComponent} />
        </ReactBootstrap.Modal.Footer>
      </ReactBootstrap.Modal>
    )
  }
}

class MainLayout extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      showModalSearch: false,
      listEmail: [],
      flagSend: false,
    }
    this.bindingValueOfComponent = this.bindingValueOfComponent.bind(this);
    this.addEmailToList = this.addEmailToList.bind(this);
    this.removeEmailFromList = this.removeEmailFromList.bind(this);
    this.isDuplicateEmail = this.isDuplicateEmail.bind(this);
  }

  bindingValueOfComponent(key, value) {
    switch (key) {
      case "showModalSearch":
        this.setState({ showModalSearch: value });
        break;
      case "listEmail":
        this.setState({ listEmail: value });
        break;
      case "flagSend":
        this.setState({ flagSend: value });
        break;
    }
  }

  addEmailToList(data) {
    let listEmail = this.state.listEmail;
    if(this.isDuplicateEmail(data, listEmail)){
      alert(DUPLICATE_ERROR_MESSAGE)
      return false;
    } else {
      listEmail.push(data);
      this.setState({ listEmail: listEmail })
      return true;
    }
  }

  removeEmailFromList(listData) {
    let listEmail = this.state.listEmail;
    listEmail = listEmail.filter((el) => !listData.includes(el.email));
    this.setState({ listEmail: listEmail });
  }

  isDuplicateEmail(data, listEmail){
    const existEmail = listEmail.filter(item=>{
      console.log(data);
      return item.email === data.email
    })
    return !!existEmail.length
  }

  render() {
    return (
      <div>
        <div className="row">
          <ComponentExclusionTarget
            bindingValueOfComponent={this.bindingValueOfComponent}
            removeEmailFromList={this.removeEmailFromList}
            listEmail={this.state.listEmail}
            addEmailToList={(data) => { return this.addEmailToList(data) }}
          />
        </div>
        <div className="row">
          <ModalComponent showModalSearch={this.state.showModalSearch} bindingValueOfComponent={this.bindingValueOfComponent} addEmailToList={this.addEmailToList} />
        </div>
      </div>
    )
  }
}

$(function () {
  ReactDOM.render(
    <MainLayout />,
    document.getElementById('react')
  )
});
