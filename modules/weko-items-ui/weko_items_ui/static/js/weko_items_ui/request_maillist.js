const NUM_OF_RESULT = 10;
const LIMIT_PAGINATION_NUMBER = 5;
const ENABLE_REQUEST_EMAIL_CHECKBOX_LABEL = document.getElementById("enable-request-email-checkbox-label").value;
const REQUEST_EMAIL_LIST_LABEL = document.getElementById("request-email-list-label").value;
const OPEN_MODAL_SEARCH_BUTTON_NAME = document.getElementById("open-modal-search-button-name").value;
const DELETE_BUTTON_NAME = document.getElementById("delete-button-name").value;
const DUPLICATE_ERROR_MESSAGE = document.getElementById("duplicate-error-message").value;
const INPUT_TEXT_PLACEHOLDER = document.getElementById("input-text-placeholder").value;
const CLOSE_BUTTON_NAME = document.getElementById("close-button-name").value;
const NAME_LABEL = document.getElementById("name-label").value;
const MAIL_ADDRESS_LABEL = document.getElementById("mail-address-label").value;
const SEARCH_BUTTON_NAME = document.getElementById("search-button-name").value;
const IMPORT_BUTTON_NAME = document.getElementById("import-button-name").value;


class RequestMailTarget extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      listEmail: [],
      selectedId: []
    };
    this.deleteCommand = this.deleteCommand.bind(this);
    this.searchCommand = this.searchCommand.bind(this);
    this.generateSelectedBox = this.generateSelectedBox.bind(this);
    this.handleClick = this.handleClick.bind(this);
    this.handleKeyPress = this.handleKeyPress.bind(this);
  }

  componentDidMount() {
    const activityID = $("#activity_id").text();
    let emails = [];
    let display_request_mail_btn = false
    $.ajax({
      url: "/workflow/get_request_maillist/" + activityID,
      async: false,
      method: "GET",
      success: function (response) {
        if (response.code) {
          emails = response.request_maillist || [];
          display_request_mail_btn = response.is_display_request_button || false
        }
      },
      error: function(jqXHR, status) {
          alert(jqXHR.responseJSON.msg);
      }
    })
    this.setState({showRequestMailSender: display_request_mail_btn})
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
    const selectedId = this.state.selectedId
    if (id < 0) {
      this.setState({
        selectedId: []
      });
    } else {
      if (this.state.selectedId.indexOf(id) == -1) {
        selectedId.push(id);
        this.setState({
          selectedId: selectedId
        });
      } else {
        this.setState({
          selectedId: selectedId.filter(e => e !== id)
        });
      }
    }
  }

  handleKeyPress(event) {
    if (event.key === 'Enter') {
      const new_email = {
        author_id: "",
        email: event.target.value.trim()
      }
      if (this.props.addEmailToList(new_email)) {
        $('div#sltBoxListRequestEmail>input#custom_input_email').val('');
        $('#sltBoxListRequestEmail').animate({
          scrollTop: $("#custom_input_email").offset().top
        }, 1000);
      }
    }
  }

  generateSelectedBox(listEmail) {
    return (
      <div class="list-group" className="style-selected-box" id="sltBoxListRequestEmail">
        {
          listEmail.map((item, id) => {
            let v = item.author_id + '_' + item.email
            if (item.author_id) {
              return (
                <a className={`list-group-item list-group-item-action ${this.state.selectedId.indexOf(id) > -1 ? 'active' : ''}`}
                  onClick={() => { this.handleClick(id) }}
                  key={id}
                  value={v}>
                  {item.email}&nbsp;&nbsp;(Author&nbsp;ID:&nbsp;{item.author_id})
                </a>
              )
            } else {
              return (
                <a className={`list-group-item list-group-item-action ${this.state.selectedId.indexOf(id) > -1 ? 'active' : ''}`}
                  onClick={() => { this.handleClick(id) }}
                  key={id}
                  value={v}>
                  {item.email}
                </a>
              )
            }
          })
        }
        <input class="list-group-item list-group-item-action"
          id="custom_input_email"
          placeholder={INPUT_TEXT_PLACEHOLDER}
          onKeyPress={(event) => { this.handleKeyPress(event) }}
        />
      </div>
    )
  }

  deleteCommand(event) {
    const listEmail = this.state.listEmail;
    const selectedId = this.state.selectedId;
    var selectedEmails = [];
    for (var index=0; index < listEmail.length; index++){
      if (selectedId.indexOf(index) > -1){
        selectedEmails.push(listEmail[index].email);
      }
    }
    this.props.removeEmailFromList(selectedEmails);
    this.handleClick(-1);
  }

  searchCommand() {
    this.props.bindingValueOfComponent("showModalSearch", true);
  }

  render() {
    return (
      <div>
        <div className="row">
          <div className="col-sm-12 form-group style-component">
            <label className="col-xs-3 text-right">
              <ReactBootstrap.Checkbox id='display_request_btn_checkbox' checked={this.state.showRequestMailSender}
                onChange={() => {this.setState({showRequestMailSender: !this.state.showRequestMailSender})}}>
                {ENABLE_REQUEST_EMAIL_CHECKBOX_LABEL}
              </ReactBootstrap.Checkbox>
            </label>
          </div>
        </div>
        <div className={`row ${this.state.showRequestMailSender ? 'show': 'hidden'}`} >
          <div className="col-sm-12 form-group style-component">
            <label className="control-label col-xs-3 text-right">
              {REQUEST_EMAIL_LIST_LABEL}
            </label>
            <div className="controls col-xs-9">
              <div>
                <ReactBootstrap.Button variant="primary" onClick={this.searchCommand}>
                  <i className="glyphicon glyphicon-search"></i>&nbsp;{OPEN_MODAL_SEARCH_BUTTON_NAME}
                </ReactBootstrap.Button>
              </div>
              <div className="style-full-size">
                {this.generateSelectedBox(this.state.listEmail)}
                <button className="btn btn-danger style-deleteBtn" onClick={this.deleteCommand}>
                  <span className="glyphicon glyphicon-trash" aria-hidden="true"></span>
                  &nbsp;{DELETE_BUTTON_NAME}
                </button>
              </div>
            </div>
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
    let tBodyElement = this.state.listUser.map((row) => {
      let name = "";
      if (row._source.authorNameInfo[0]) {
        name = row._source.authorNameInfo[0].fullName;
        if (!name) {
          let familyName = row._source.authorNameInfo[0].familyName || "";
          let firstName = row._source.authorNameInfo[0].firstName || "";
          name = familyName + firstName;
        }
      }
      if (row._source.emailInfo.length == 1) {
        return (
          <tr key={row._source.pk_id.toString()}>
                <td>{name}</td>
            <td>{row._source.emailInfo[0].email}</td>
            <td className="text-right">
              <button className="btn btn-info"
                onClick={(event) => this.importEmail(event, row._source.pk_id, row._source.emailInfo[0].email)}>
                  &nbsp;&nbsp;{IMPORT_BUTTON_NAME}&nbsp;&nbsp;
              </button>
            </td>
          </tr>
        )
      } else {
        return (
          <tr key={row._source.pk_id.toString()}>
            <td>{name}</td>
            <td></td>
            <td className="text-right">
              <button disabled className="btn btn-info">
                  &nbsp;&nbsp;{IMPORT_BUTTON_NAME}&nbsp;&nbsp;
              </button>
            </td>
          </tr>
        )
      }
    }
    )
    return (
      <tbody >
        {tBodyElement}
      </tbody>
    )
  }

  importEmail(event, pk_id, email) {
    let listUser = [];
    $("#sltBoxListRequestEmail > a").each(function () {
      listUser.push(this.value);
    });
    if (listUser.indexOf(pk_id) == -1) {
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
        <table className="table table-striped style-table-modal" id="table_data_request">
          <caption ></caption>
          <thead >
            <tr className="success">
              <th className="thWidth style-column">{NAME_LABEL}</th>
              <th className="thWidth style-column">{MAIL_ADDRESS_LABEL}</th>
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
    $.ajax({
      context: this,
      url: "/api/admin/search_email",
      type: 'POST',
      contentType: 'application/json',
      data: JSON.stringify(request),
      success: function (result) {
        this.props.getListUser(result.hits.hits, result.hits.total);
      },
      error: function (error) {
        console.log(error);
      }
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
            {SEARCH_BUTTON_NAME} &nbsp;&nbsp;
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
    $.ajax({
      context: this,
      url: "/api/admin/search_email",
      type: 'POST',
      contentType: 'application/json',
      data: JSON.stringify(request),
      success: function (result) {
        this.props.getListUser(result.hits.hits, result.hits.total);
      },
      error: function (error) {
        console.log(error);
      }
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
        <span className="glyphicon glyphicon-remove"></span> {CLOSE_BUTTON_NAME}
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
      showRequestMailSender: false,
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
    if (this.isDuplicateEmail(data, listEmail)) {
      alert(DUPLICATE_ERROR_MESSAGE)
      return false;
    } else {
      if (!data.author_id || !this.isDuplicateAuthorId(listEmail, data.author_id)) {
        listEmail.push(data);
        this.setState({ listEmail: listEmail })
        return true;
      } else {
        const newList = listEmail.filter(item => item.author_id !== data.author_id)
        newList.push(data)
        this.setState({
          listEmail: newList
        })
        return true;
      }
    }
  }

  removeEmailFromList(listData) {
    let listEmail = this.state.listEmail;
    var listRemainEmail = [];
    for (var index in listEmail){
      if (listData.indexOf(listEmail[index].email) == -1){
        listRemainEmail.push(listEmail[index])
      }
    }
    this.setState({ listEmail: listRemainEmail });
  }

  isDuplicateAuthorId(listEmail, author_id) {
    const authorIdList = Array.from(listEmail, item => {
      if (item.author_id) {
        return item.author_id
      }
    })
    return authorIdList.indexOf(author_id) > -1
  }

  isDuplicateEmail(data, listEmail) {
    const existEmail = listEmail.filter(item => {
      console.log(data);
      return item.email === data.email
    })
    return !!existEmail.length
  }

  render() {
    return (
      <div>
        { (this.props.enable_request_maillist) ? (
                  <div>
            <RequestMailTarget
              bindingValueOfComponent={this.bindingValueOfComponent}
              removeEmailFromList={this.removeEmailFromList}
              listEmail={this.state.listEmail}
              addEmailToList={(data) => {
                return this.addEmailToList(data)
              }}
            />
          <div className="row">
            <ModalComponent showModalSearch={this.state.showModalSearch} bindingValueOfComponent={this.bindingValueOfComponent} addEmailToList={this.addEmailToList} />
          </div>
          </div>
          ) : null }
        </div>

    )
  }
}

$(function () {
  let enable_request_maillist = document.getElementById('enable_request_maillist').value === 'True';
  ReactDOM.render(
    <MainLayout enable_request_maillist = {enable_request_maillist} />,
    document.getElementById('request-maillist')
  )
});
