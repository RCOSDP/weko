const MAIN_CONTENT_TYPE = "Main contents";
const MAIN_CONTENT_BUTTON_ID = "main_content_id";
let isHasMainContent = false;

const HEADER_CLASS = "header_class";
const HEADER_TYPE = "Header";
let isHasHeader = false;

const FOOTER_CLASS = "footer_class";
const FOOTER_TYPE = "Footer";
let isHasFooter = false;

const ACCESS_COUNTER = "Access counter";

const LOAD_REPOSITORY_URL = "/api/admin/load_repository";
const LOAD_WIDGET_LIST_DESIGN_SETTING_URL = "/api/admin/load_widget_list_design_setting";
const LOAD_WIDGET_DESIGN_PAGES_URL = '/api/admin/load_widget_design_pages';
const LOAD_DESIGN_PAGE = '/api/admin/load_widget_design_page';
const DELETE_WIDGET_DESIGN_PAGE_URL = '/api/admin/delete_widget_design_page';
const ROOT_URL = '/';
const GET_SYSTEM_LANG_URL = '/api/admin/get_system_lang';
const SAVE_WIDGET_LAYOUT_SETTING_URL = "/api/admin/save_widget_layout_setting";
const LOAD_WIDGET_DESIGN_SETTING_URL = "/api/admin/load_widget_design_setting";
const LOAD_WIDGET_DESIGN_PAGE_SETTING_URL = '/api/admin/load_widget_design_page_setting/';

let windowObjectReference = null;
let previousUrl; /* global variable that will store the
                    url currently in the secondary window */
/**
 * Repository combo box.
 */
class Repository extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      repositoryId: '0_default',
      selectOptions: []
    };
    this.styleRed = {
      color: 'red',
    };
    this.handleChange = this.handleChange.bind(this);
  }

  componentDidMount() {
    let _this = this;
    $.ajax({
      url: LOAD_REPOSITORY_URL,
      type: 'GET',
      dataType: "json",
      success: function (result) {
        if (result.error) {
          addAlert(result.error);
          return;
        }
        let options = result['repositories'].map((option) => {
          return (
            <option key={option.id} value={option.id}>{option.id}</option>
          )
        });
        _this.setState({
          selectOptions: options
        });
      },
      error: function (error) {
        console.log(error);
      }
    });
  }

  handleChange(event) {
    let repositoryId = event.target.value;
    let data = {
      repository_id: repositoryId
    };
    $.ajax({
      url: LOAD_WIDGET_LIST_DESIGN_SETTING_URL,
      type: 'POST',
      dataType: "json",
      contentType: 'application/json',
      data: JSON.stringify(data),
      success: function (result) {
        if (result.error) {
          console.log(result.error);
          return;
        }
        let widgetPreview = result['widget-preview']['data'];
        let widgetList = result['widget-list']['data'];
        loadWidgetPreview(widgetPreview);
        loadWidgetList(widgetList);
      },
      error: function (error) {
        console.log(error);
      }
    });

    disableButton();
    this.setState({ repositoryId: repositoryId });
    this.props.callbackMainLayout('repositoryId', repositoryId);
    event.preventDefault();
  }

  render() {
    return (
      <div className="form-group row">
        <div id="alerts" />
        <label htmlFor="input_type" className="control-label col-xs-1">Repository<span
          style={this.styleRed}>*</span></label>
        <div className="controls col-xs-5">
          <select id="repository-id" value={this.state.repositoryId}
            onChange={this.handleChange} className="form-control">
            <option value="0">Please select the Repository</option>
            {this.state.selectOptions}
          </select>
        </div>
      </div>
    )
  }
}

/**
 * Widget list panel layout.
 */
class WidgetList extends React.Component {
  constructor(props) {
    super(props);
    this.style = {
      "border": "1px solid #eee",
      "min-height": "300px",
      "max-height": "calc(100vh - 300px)",
      "overflow": "scroll",
      "overflow-x": "hidden",
      "margin-right": "0px"
    };
  }

  render() {
    return (
      <div>
        <label className="control-label row">Widget List</label>
        <div className="row grid-stack" style={this.style} id="widgetList">
        </div>
      </div>
    )
  }
}

/**
 * Pages list select
 */
class PagesListSelect extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      options: [],
      selectedPage: 0,
      isMainLayout: false
    };
    this.getPages = this.getPages.bind(this);
    this.handleChange = this.handleChange.bind(this);
    this.displayOptions = this.displayOptions.bind(this);
    this.getPages = this.getPages.bind(this);
    this.refreshList = this.refreshList.bind(this);
    this.getPageDesign = this.getPageDesign.bind(this);
  }

  componentDidMount() {
    this.getPages();
  }

  componentWillReceiveProps(nextProps) {
    if (nextProps.repositoryId !== this.props.repositoryId) {
      this.props.repositoryId = nextProps.repositoryId;
      this.refreshList();
    }
  }

  refreshList(selectedPage = 0) {
    this.getPages(selectedPage);
  }

  getPages(selectedPage = 0) {
    if (this.props.repositoryId) {
      let data = {
        repository_id: this.props.repositoryId
      };
      let _this = this;
      $.ajax({
        url: LOAD_WIDGET_DESIGN_PAGES_URL,
        type: 'POST',
        dataType: "json",
        contentType: 'application/json',
        data: JSON.stringify(data),
        success: function (result) {
          if (result.error) {
            alertModal("Can't get page list! \nDetail: " + result.error);
          } else {
            _this.displayOptions(result['page-list']['data'], selectedPage);  //this.state.selectedPage
          }
        },
        error: function (error) {
          console.log(error);
        }
      });
    }
  }

  displayOptions(pages, selectedPage = 0) {
    let options = [<option key={this.props.repositoryId} value={0} selected>Main
      Layout</option>];
    let isMainLayout = false;
    pages.forEach(function (page) {
      if (page.is_main_layout) {
        options.shift();
        options.unshift(<option data-is-main-layout={page.is_main_layout}
          key={page.id}
          value={page.id}>{page.name}</option>);
        if (selectedPage === 0) {
          selectedPage = page.id;
        }
        isMainLayout = page.is_main_layout;
      } else {
        options.push(<option data-is-main-layout={page.is_main_layout}
          key={page.id}
          value={page.id}>{page.name}</option>);
      }
    });
    this.setState({
      options: options,
      selectedPage: selectedPage,
      isMainLayout: isMainLayout,
    });
    this.props.callbackMainLayout('pageId', selectedPage);  // Must set to change Preview
  }

  getPageDesign(id, isMainLayout) {
    let url;
    let requestType = 'GET';
    let data;
    if (String(id) === '0' || isMainLayout) {  // If zero, then the main layout was selected
      url = LOAD_WIDGET_DESIGN_SETTING_URL;
      data = {
        repository_id: this.props.repositoryId
      };
      requestType = 'POST'
    } else {  // Get design setting for page not repository
      url = LOAD_WIDGET_DESIGN_PAGE_SETTING_URL + id;
    }
    $.ajax({
      url: url,
      type: requestType,
      dataType: "json",
      contentType: 'application/json',
      data: JSON.stringify(data),
      success: function (result) {
        if (result.error) {
          alertModal(result.error);
          return;
        }
        let widgetList = result['widget-settings'];
        loadWidgetPreview(widgetList);
      },
      error: function (error) {
        alertModal(error);
        console.log(error);
      }
    });
  }

  handleChange(event) {
    let target = event.target;
    let option = target.options[target.selectedIndex];
    let isMainLayout = (String(option.dataset.isMainLayout) === "true");
    this.setState({
      selectedPage: event.target.value,
      isMainLayout: isMainLayout
    });
    this.props.callbackMainLayout('pageId', event.target.value);
    this.getPageDesign(event.target.value, isMainLayout);
  }

  render() {
    const selectedOption = this.state.selectedPage;
    return (
      <div className="form-group row">
        <label htmlFor="pages-list-select"
          className="control-label col-xs-1">Pages</label>
        <div className="controls col-xs-5">
          <select id="pages-list-select" onChange={this.handleChange}
            className="form-control">
            {this.state.options}
          </select>
        </div>
        <PagesListSelectControls isMainLayout={this.state.isMainLayout}
          refreshList={this.refreshList}
          selectedOption={selectedOption}
          repositoryId={this.props.repositoryId} />
      </div>
    );
  }
}

/**
 * Page list controls
 */
class PagesListSelectControls extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      deleteModalOpen: false,
      pageModalOpen: false,
      page: {},
      isEdit: false,
    };
    this.handleEdit = this.handleEdit.bind(this);
    this.handleDelete = this.handleDelete.bind(this);
  }

  handleEdit(event) {
    event.preventDefault();
    let requestData = {
      page_id: this.props.selectedOption,
      repository_id: this.props.repositoryId
    };
    $.ajax({
      context: this,
      url: LOAD_DESIGN_PAGE,
      type: 'POST',
      dataType: "json",
      contentType: 'application/json',
      data: JSON.stringify(requestData),
      success: function (result) {
        if (result.error) {
          this.setState({ page: {} });
          alertModal("Can't get page! \nDetail: " + result.error);
        } else {  // Set the data for the modal
          this.setState({
            page: result.data,
            pageModalOpen: true
          });
        }
      },
      error: function (error) {
        this.setState({ page: {} });
        alertModal("Can't get page! \nDetail: " + error);
      }
    });
  }

  handleDelete() {
    this.setState({ deleteModalOpen: false });
    let postData = { page_id: this.props.selectedOption };
    $.ajax({
      context: this,
      url: DELETE_WIDGET_DESIGN_PAGE_URL,
      type: 'POST',
      dataType: "json",
      contentType: 'application/json',
      data: JSON.stringify(postData),
      success: function (result) {
        if (result.error) {  // Exception occurred while saving
          alertModal(result.error);
        } else if (!result.result) {  // No exception, but problem with request data
          alertModal('Unable to delete page: Unexpected error.');
        } else {
          this.props.refreshList();
          addAlert('Successfully deleted page.');
        }
      }
    });
  }

  render() {
    const selected = this.props.selectedOption;
    let buttons = [];
    let addButton = <IconButton id={'add-page'} onClick={() => this.setState({
      pageModalOpen: true,
      isEdit: false
    })} iconClass={'fa fa-plus glyphicon glyphicon-plus'} />;
    let editButton = <IconButton id={'edit-page'} onClick={(e) => {
      this.handleEdit(e);
      this.setState({ isEdit: true })
    }} iconClass={'fa fa-pencil glyphicon glyphicon-pencil'} />;
    let deleteButton = <IconButton id={'delete-page'}
      onClick={() => this.setState({ deleteModalOpen: true })}
      iconClass={'fa fa-trash glyphicon glyphicon-trash'} />;
    if (parseInt(selected) !== 0 && !this.props.isMainLayout) {  // Do not allow the deletion of parent layout
      buttons.push(editButton);
      buttons.push(deleteButton);
    } else {
      buttons.push(addButton);
      buttons.push(editButton);
    }
    return (
      [
        <div className="col-xs-3">
          <div className="btn-toolbar">
            {buttons}
          </div>
        </div>,
        <DeletePageModal deleteModalOpen={this.state.deleteModalOpen}
          handleDelete={this.handleDelete}
          handleClose={() => this.setState({ deleteModalOpen: false })} />,
        <AddPageModal isEdit={this.state.isEdit}
          isOpen={this.state.pageModalOpen}
          handleClose={() => this.setState({ pageModalOpen: false })}
          repositoryId={this.props.repositoryId}
          addPageEndpoint={'/api/admin/save_widget_design_page'}
          pageId={selected} page={this.state.page}
          refreshList={this.props.refreshList} />
      ]
    )
  }
}

/**
 * Icon buttons for controlling page
 */
class IconButton extends React.Component {
  constructor(props) {
    super(props);
  }

  render() {
    return (
      <button id={this.props.id} className="icon" onClick={this.props.onClick}>
        <span className={this.props.iconClass} aria-hidden="true" />
      </button>
    )
  }
}

/**
 * Delete page modal
 */
class DeletePageModal extends React.Component {
  constructor(props) {
    super(props);
  }

  render() {
    return (
      <div className="modal" tabIndex="-1" role="dialog"
        style={this.props.deleteModalOpen ? { display: 'block' } : { display: 'none' }}>
        <div className="modal-dialog" role="document">
          <div className="modal-content">
            <div className="modal-header">
              <button type="button" className="close"
                onClick={this.props.handleClose} aria-label="Close"><span
                  aria-hidden="true">&times;</span></button>
              <h4 className="modal-title">Delete Page</h4>
            </div>
            <div className="modal-body">
              <p className="text-center">Are you sure you want to delete the
                page?</p>
            </div>
            <div className="modal-footer">
              <button id="delete-page" className="btn btn-primary save-button"
                onClick={this.props.handleDelete}>
                <span className="glyphicon glyphicon-check" />
                Submit
              </button>
              <button type="button" className="btn btn-info close-button"
                onClick={this.props.handleClose}>
                <span className="glyphicon glyphicon-remove" />
                Close
              </button>
            </div>
          </div>
        </div>
      </div>
    )
  }
}

/**
 * Add page modal
 */
class AddPageModal extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      title: (this.props.page.title || 'Page Title'),
      url: (this.props.page.url || '/'),
      content: (this.props.page.content || ''),
      multiLangData: (this.props.page.multi_lang_data || {}),
      errorMessage: '',
      isMainLayout: (this.props.page.is_main_layout || false),
    };
    this.handleSave = this.handleSave.bind(this);
    this.handleInputChange = this.handleInputChange.bind(this);
    this.handleClose = this.handleClose.bind(this);
  }

  handleInputChange(name, value) {
    this.setState({ [name]: value });
  }

  componentWillReceiveProps(nextProps) {
    if (nextProps.page !== this.props.page) {
      this.setState({
        page: nextProps.page,
        title: nextProps.page.title,
        url: nextProps.page.url,
        content: nextProps.page.content,
        multiLangData: nextProps.page.multi_lang_data,
        isMainLayout: nextProps.page.is_main_layout,
      });
    }
  }

  validateInput() {
    if (!this.props.repositoryId) {
      this.setState({ 'errorMessage': 'Please select the repository.' });
      return false;
    }

    if (!/\/[a-z0-9?&/=]*/.test(this.state.url)) {
      this.setState({ 'errorMessage': 'Not a valid URL.' });
      return false;
    }
    return true;
  }

  handleSave(event) {
    event.preventDefault();
    let url = '';
    if ((this.props.repositoryId === 'Root Index') || (this.props.repositoryId === '0') || (this.props.repositoryId.length === 0)) {
      url = this.state.url
    } else {
      if (this.state.url.startsWith('/c/' + this.props.repositoryId + '/page')) {
        url = this.state.url
      } else {
        url = '/c/' + this.props.repositoryId + '/page' + this.state.url;
      }
    }
    if (this.validateInput()) {
      this.setState({ 'errorMessage': '' });
      this.props.handleClose();
      let postData = {
        page_id: this.props.pageId,
        repository_id: this.props.repositoryId,
        title: this.state.title,
        url: url,
        content: this.state.content,
        multi_lang_data: this.state.multiLangData,
        is_main_layout: this.state.isMainLayout,
        is_edit: this.props.isEdit,
      };
      let _this = this;
      $.ajax({
        url: this.props.addPageEndpoint,
        type: 'POST',
        dataType: "json",
        contentType: 'application/json',
        data: JSON.stringify(postData),
        success: function (result) {
          if (result.error) {  // Exception occurred while saving
            alertModal(result.error);
          } else if (!result.result) {  // No exception, but problem with request data
            alertModal('Unable to save page: Unexpected error.');
          } else {
            _this.props.refreshList(_this.props.pageId);
            _this.handleClose(event);
            addAlert('Successfully saved page.');
          }
        },
        error: function () {
          alertModal('Unable to save page: Unexpected error.');
        }
      });
    }
  }

  handleClose(event) {
    this.setState({
      page: {},
      title: 'Page Title',
      url: ROOT_URL,
      content: '',
      multiLangData: {},
      isMainLayout: false,
    });
    this.props.handleClose(event);
  }

  render() {
    return (
      <div className="modal" tabIndex="-1" role="dialog"
        style={this.props.isOpen ? { display: 'block' } : { display: 'none' }}>
        <div className="modal-dialog modal-lg" role="document">
          <div className="modal-content">
            <div className="modal-header">
              <button type="button" className="close" onClick={this.handleClose}
                aria-label="Close"><span aria-hidden="true">&times;</span>
              </button>
              <h4 className="modal-title">Page</h4>
            </div>
            <div className="modal-body">
              <p
                className="text-center text-danger">{this.state.errorMessage}</p>
              {(this.props.repositoryId === 'Root Index') || (this.props.repositoryId === '0') || (this.props.repositoryId.length === 0) ?
                null :
                <p>※ For &nbsp;{this.props.repositoryId}&nbsp; page,&nbsp;"/c/{this.props.repositoryId}/page"&nbsp;will be automatically added to before the URL</p>
              }
              <AddPageForm
                pageModalOpen={this.props.isOpen}
                values={{
                  title: this.state.title,
                  url: this.state.url,
                  content: this.state.content,
                  multiLangData: this.state.multiLangData,
                  isMainLayout: this.state.isMainLayout
                }}
                handleInputChange={this.handleInputChange}
              />
            </div>
            <div className="modal-footer">
              <button className="btn btn-primary save-button"
                onClick={this.handleSave}>
                <span className="glyphicon glyphicon-check" />
                Save
              </button>
              <button type="button" className="btn btn-info close-button"
                onClick={this.handleClose}>
                <span className="glyphicon glyphicon-remove" />
                Close
              </button>
            </div>
          </div>
        </div>
      </div>
    )
  }
}

/**
 * Add page modal form
 */
class AddPageForm extends React.Component {
  constructor(props) {
    super(props);
  }

  render() {
    return (
      <div>
        <div className="form-group row">
          <label htmlFor="" className="control-label col-xs-2 text-right">
            URL<span className="text-red">*</span>
          </label>
          <div className="col-xs-6">
            <input name="url" type="text" value={this.props.values.url}
              onChange={(e) => this.props.handleInputChange(e.target.name, e.target.value)}
              className="form-control"
              disabled={this.props.values.isMainLayout} />
          </div>
        </div>
        <div className="form-group row">
          <label htmlFor="" className="control-label col-xs-2 text-right">
            Title
          </label>
          <PageTitle title={this.props.values.title}
            multiLangData={this.props.values.multiLangData}
            handleChange={this.props.handleInputChange}
            pageModalOpen={this.props.pageModalOpen} />
        </div>
      </div>
    )
  }
}

class PageTitle extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      title: this.props.title || '',
      multiLangData: this.props.multiLangData || {},
      pageModalOpen: this.props.pageModalOpen,
      languageList: [],
      languageNameList: {},
      options: [],
      selectedLanguage: '0',  // Temporary, changed after data retrieval
      defaultLanguage: ''
    };
    this.handleChange = this.handleChange.bind(this);
    this.handleChangeLanguage = this.handleChangeLanguage.bind(this);
    this.initLanguageList = this.initLanguageList.bind(this);
    this.displayOptions = this.displayOptions.bind(this);
  }

  initLanguageList() {
    let langList = [];
    let langName = {};
    let systemRegisteredLang = [];
    let _this = this;
    $.ajax({
      url: GET_SYSTEM_LANG_URL,
      type: 'GET',
      dataType: "json",
      success: function (result) {
        if (result.error) {
          let message = "Can't get system language! \nDetail: " + result.error;
          addAlert(message);
        } else {
          let systemLang = result.language;
          systemLang.forEach(function (lang) {
            if (lang.is_registered) {
              let newLang = {
                'code': lang.lang_code,
                'sequence': lang.sequence
              };
              systemRegisteredLang.push(newLang);
            } else {
              langList.push(lang.lang_code);
            }
            langName[lang.lang_code] = lang['lang_name'];
          });
          for (let i = systemRegisteredLang.length; i >= 0; i--) {
            for (let j = 0; j < systemRegisteredLang.length; j++) {
              if (systemRegisteredLang[j].sequence === i) {
                langList.unshift(systemRegisteredLang[j].code);
              }
            }
          }
          // Set default language to top one
          // TODO: Should we even worry about defaults, --- yes because we have to save one as default
          // TODO: Think about the case for when the default changes
          //        after the widget page is already saved once *** ASK about this case
          let selectedLang;
          let defaultLang;
          selectedLang = langList[0];
          defaultLang = langList[0];

          _this.displayOptions(langList, langName, selectedLang);
          _this.setState({
            languageList: langList,
            languageNameList: langName,
            selectedLanguage: selectedLang,
            defaultLanguage: defaultLang
          });
        }
      }
    });
  }

  componentDidMount() {
    this.initLanguageList();
  }

  displayOptions(languageList, languageNameList, selected = null) {
    let optionList = [];
    let state = this.state;
    languageList.forEach(function (lang) {
      let innerHTML;
      let langName = languageNameList[lang]
      if (lang === state.defaultLanguage) {
        innerHTML = <option key={lang} value={lang} selected>{langName}</option>;
      } else if (lang === selected) {
        innerHTML = <option key={lang} value={lang} selected>{langName}</option>;
      } else {
        innerHTML = <option key={lang} value={lang}>{langName}</option>;
      }
      optionList.push(innerHTML);
    });
    this.setState({
      options: optionList
    });
  }

  handleChange(event) {
    // Add the default as the 'title' of the model
    let selectedLanguage = this.state.selectedLanguage;
    let inputValue = event.target.value;
    if (selectedLanguage === this.state.defaultLanguage) {
      this.props.handleChange(event.target.name, inputValue);
    }

    // Add to current multi-language data in state
    let multiLangData = this.state.multiLangData;
    multiLangData[selectedLanguage] = inputValue;
    this.setState({
      multiLangData: multiLangData,
      title: inputValue,
    });
    this.props.handleChange('multiLangData', multiLangData);
  }

  handleChangeLanguage(event) {
    let selectedValue = event.target.value;
    let multiLangData = this.state.multiLangData;
    console.log(selectedValue, multiLangData);
    if (multiLangData.hasOwnProperty(selectedValue)) {
      this.setState({ title: multiLangData[selectedValue] });
    } else if (selectedValue === this.state.defaultLanguage) {  // Default language is main one
      this.setState({ title: this.props.title });
    } else {
      this.setState({ title: '' });
    }
    this.setState({ selectedLanguage: selectedValue });
  }

  componentWillReceiveProps(nextProps) {
    if (nextProps.pageModalOpen !== this.state.pageModalOpen) {
      let lang = this.state.defaultLanguage;
      let title = lang in nextProps.multiLangData ?
        nextProps.multiLangData[lang] : nextProps.title;
      this.setState({
        title: title,
        multiLangData: nextProps.multiLangData,
        pageModalOpen: nextProps.pageModalOpen,
        selectedLanguage: lang,
      });
    }
  }

  render() {
    return (
      <div>
        <div className="col-xs-6">
          <input id="page-title-input"
            name="title" type="text"
            value={this.state.title}
            onChange={this.handleChange}
            className="form-control" />
        </div>
        <div key={this.state.pageModalOpen} className="col-xs-2">
          <select id="page-language-select"
            onChange={this.handleChangeLanguage}
            className="form-control">
            {this.state.options}
          </select>
        </div>
      </div>
    );
  }
}

/**
 * Preview widget panel layout.
 */
class PreviewWidget extends React.Component {
  constructor(props) {
    super(props);
    this.style = {
      "border": "1px solid #eee"
    };
  }

  render() {
    return (
      <div>
        <label className="control-label row">Preview</label>
        <div className="row grid-stack" style={this.style} id="gridPreview">
        </div>
      </div>
    )
  }

}

/**
 * Button layout.
 */
class ButtonLayout extends React.Component {
  constructor(props) {
    super(props);
    this.style = {
      "margin-right": "10px",
      "margin-left": "-15px"

    };
    this.handleSave = this.handleSave.bind(this);
    this.handleCancel = this.handleCancel.bind(this);
  }

  handleSave() {
    PreviewGrid.saveGrid();  // Pass the repo id here and stuff
  }

  handleCancel() {  // Reset to current settings
    let url;
    let requestType = 'GET';
    let data;
    if (this.props.pageId === 0) {  // If zero, then the main layout is selected
      url = LOAD_WIDGET_DESIGN_SETTING_URL;
      data = {
        repository_id: this.props.repositoryId
      };
      requestType = 'POST'
    } else {  // Get design setting for page not repository
      url = LOAD_WIDGET_DESIGN_PAGE_SETTING_URL + this.props.pageId;
    }
    $.ajax({
      url: url,
      type: requestType,
      dataType: "json",
      contentType: 'application/json',
      data: JSON.stringify(data),
      success: function (result) {
        if (result.error) {
          alertModal(error);
          PreviewGrid.clearGrid();
          return;
        }
        let widgetList = result['widget-settings'];
        loadWidgetPreview(widgetList);
      },
      error: function (error) {
        PreviewGrid.clearGrid();
        console.log(error);
      }
    });
  }

  render() {
    return (
      <div className="form-group col-xs-10">
        <button id="save-grid" className="btn btn-primary save-button"
          style={this.style} onClick={this.handleSave}>
          <span className="glyphicon glyphicon-saved" aria-hidden="true" />
          &nbsp;Save
        </button>
        <button id="clear-grid"
          className="form-group btn btn-info cancel-button"
          onClick={this.handleCancel}>
          <span className="glyphicon glyphicon-remove" aria-hidden="true" />
          Cancel
        </button>
      </div>
    )
  }
}

/**
 * Main layout.
 */
class MainLayout extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      repositoryId: "",
      pageId: 0
    };
    this.props.repositoryId = "";
  }

  callbackMainLayout(name, value) {
    this.setState({ [name]: value });
  }

  render() {
    const repositoryId = this.state.repositoryId;
    return (
      <div>
        <div className="row">
          <Repository callbackMainLayout={this.callbackMainLayout.bind(this)} />
          {(repositoryId !== 0 || repositoryId !== '0' && repositoryId.length) ?  // Only show if parent data is available
            <PagesListSelect
              callbackMainLayout={this.callbackMainLayout.bind(this)}
              repositoryId={repositoryId} /> :
            null
          }
        </div>
        <div className="row">
          <div className="form-group col-xs-2">
            <WidgetList repositoryId={this.state.repositoryId} />
          </div>
          <div className="form-group col-xs-10">
            <PreviewWidget />
          </div>
        </div>
        <div className="row">
          <ButtonLayout repositoryId={this.state.repositoryId}
            pageId={this.state.pageId} />
        </div>
      </div>
    )
  }
}

/**
 *Preview grid.
 */
var PreviewGrid = new function () {
  this.init = function () {
    let options = {
      width: 12,
      removeTimeout: 100,
      cellHeight: 6,
      verticalMargin: 10,
      acceptWidgets: '.grid-stack-item'
    };

    let gridPreview = $('#gridPreview');

    gridPreview.gridstack(_.defaults(options));

    this.serializedData = [];

    this.grid = gridPreview.data('gridstack');
  };

  this.loadGrid = function (widgetListItems) {
    this.grid.removeAll();
    let items = GridStackUI.Utils.sort(widgetListItems);
    isHasMainContent = false;
    isHasHeader = false;
    isHasFooter = false;
    _.each(items, function (node) {
      if (MAIN_CONTENT_TYPE === node.type) {
        isHasMainContent = true;
        disableMainContentButton(true); // Figure this out
      }
      if (node.type === HEADER_TYPE) {
        isHasHeader = true;
        disableHeaderButton(true);
      }
      if (node.type === FOOTER_TYPE) {
        isHasFooter = true;
        disableFooterButton(true);
      }
      this.grid.addWidget($(this.widgetTemplate(node, false)),
        node.x, node.y, node.width, node.height);
    }, this);
    // Re enable button if Main content not true
    if (!isHasMainContent) {
      disableMainContentButton(false);
    }
    if (!isHasHeader) {
      disableHeaderButton(false);
    }
    if (!isHasFooter) {
      disableFooterButton(false);
    }

    return false;
  }.bind(this);

  this.saveGrid = function () {
    this.serializedData = _.map($('.grid-stack > .grid-stack-item:visible'), function (el) {
      el = $(el);
      let node = el.data('_gridstack_node');
      let name = el.data("name");
      let id = el.data("id");
      let type = el.data("type");
      let widget_id = el.data("widget_id");
      let created_date = el.data("created_date");
      if (!id) {
        return;
      } else if (MAIN_CONTENT_TYPE === type) {
        isHasMainContent = true;
      }
      let result = {
        x: node.x,
        y: node.y,
        width: node.width,
        height: node.height,
        name: name,
        id: id,
        type: type,
        widget_id: widget_id,
      };
      if (created_date) {
        result.created_date = created_date;
      }
      return result;
    }, this);
    var filtered = this.serializedData.filter(function (el) {
      return el != null;
    });
    saveWidgetDesignSetting(filtered);
    return false;
  }.bind(this);

  this.clearGrid = function () {
    this.grid.removeAll();
    return false;
  }.bind(this);

  this.addNewWidget = function (node) {
    this.grid.addWidget($(this.widgetTemplate(node, true)),
      node.x, node.y, node.width, node.height);
    return false;
  }.bind(this);

  this.widgetTemplate = function (node, isAutoPosition) {
    let autoPosition = "";
    if (isAutoPosition) {
      autoPosition = 'data-gs-auto-position="true"';
    }
    let createdDate = "";
    if (node.created_date) {
      createdDate = '" data-created_date="' + node.created_date + '"';
    }
    let template = '<div data-type="' + node.type + '" data-name="' + node.name + '" data-id="' + node.id + '"'
      + '" data-widget_id="' + node.widget_id + '"' + autoPosition + createdDate + '>'
      + ' <div class="center-block" style="margin-top: 4px;">'
      + '   <div class="col-xs-6 text-left" style="z-index: 90;">'
      + '     <div class="glyphicon glyphicon-cog pointer" data-id="' + node.widget_id + '"></div>'
      + '   </div>'
      + '   <div class="col-xs-6 text-right" style="z-index: 90;">'
      + '      <div class="glyphicon glyphicon-remove pointer"></div>'
      + '   </div>'
      + '</div>'
      + ' <div class="grid-stack-item-content">'
      + '     <span class="widget-label">&lt;' + node.type + '&gt;</span>'
      + '     <span class="widget-label">' + node.name + '</span>'
      + ' </div>'
      + '<div/>';
    return template;
  }.bind(this);

  this.deleteWidget = function (item) {
    try {
      this.grid.removeWidget(item);
    } catch (err) {
    }
    return false;
  };
};

/**
 * Add widget from List panel to Preview panel.
 */
function addWidget() {
  $('.add-new-widget').each(function () {
    let $this = $(this);
    $this.on("click", function () {
      let widgetName = $(this).data('widgetName');
      let widgetId = $(this).data('widgetId');
      let widgetType = $(this).data('widgetType');
      let id = $(this).data('id');
      if (MAIN_CONTENT_TYPE === widgetType && isHasMainContent) {
        alertModal("Main Content has been existed in Preview panel.");
        disableMainContentButton(true);
        return false;
      }
      if (HEADER_TYPE === widgetType && isHasHeader) {
        alertModal("Header has been existed in Preview panel.");
        disableHeaderButton(true);
        return false;
      }
      if (FOOTER_TYPE === widgetType && isHasFooter) {
        alertModal("Footer has been existed in Preview panel.");
        disableFooterButton(true);
        return false;
      }
      let node = {
        x: 0,
        y: 0,
        width: 2,
        height: 6,
        auto_position: true,
        name: widgetName,
        id: widgetId,
        type: widgetType,
        widget_id: id,
      };
      PreviewGrid.addNewWidget(node);
      if (MAIN_CONTENT_TYPE === widgetType) {
        isHasMainContent = true;
        disableMainContentButton(true);
      }
      if (HEADER_TYPE === widgetType) {
        isHasHeader = true;
        disableHeaderButton(true);
      }
      if (FOOTER_TYPE === widgetType) {
        isHasFooter = true;
        disableFooterButton(true);
      }
      removeWidget();
      editWidget();
    });
  });

}

/**
 * Load Widget list panel
 * @param {*} widgetListItems
 */
function loadWidgetList(widgetListItems) {
  let options = {
    width: 2,
    ddPlugin: false,
    cellHeight: 80,
    acceptWidgets: '.grid-stack-item'
  };
  let widgetListPanel = $('#widgetList');
  widgetListPanel.gridstack(options);
  let widgetList = widgetListPanel.data('gridstack');
  widgetList.removeAll();
  let x = 0;
  let y = 0;
  _.each(widgetListItems, function (widget) {
    let buttonId = "";
    let buttonClass = "";
    let widgetType = widget['widgetType'];
    if (widgetType === MAIN_CONTENT_TYPE) {
      buttonId = 'id="' + MAIN_CONTENT_BUTTON_ID + '"';
    } else if (widgetType === HEADER_TYPE) {
      buttonClass = HEADER_CLASS;
    } else if (widgetType === FOOTER_TYPE) {
      buttonClass = FOOTER_CLASS;
    }
    widgetList.addWidget($(
      '<div>'
      + '<div class="grid-stack-item-content">'
      + ' <div class="text-left" style="z-index: 90;position: absolute;margin: 5px;">'
      + '<div class="glyphicon glyphicon-cog pointer" data-id="' + widget.Id + '"></div>'
      + ' </div>'
      + ' <span class="widget-label" >&lt;' + widgetType + '&gt;</span>'
      + ' <span class="widget-label">' + widget.label + '</span>'
      + ' <button ' + buttonId + ' data-widget-type="' + widgetType
      + '" data-widget-name="' + escapeHtml(widget.label) + '" data-widget-id="' + widget['widgetId']
      + '" data-id="' + widget.Id + '" class="btn btn-default add-new-widget ' + buttonClass + '">'
      + ' Add Widget'
      + ' </button>'
      + '</div>'
      + '<div/>'),
      x, y, 2, 1);
    x++;
    y++;
  }, this);
  addWidget();
  editWidget();
}

/**
 * Load Preview panel
 * @param {*} widgetListItems
 */
function loadWidgetPreview(widgetListItems) {
  PreviewGrid.init();
  PreviewGrid.loadGrid(widgetListItems);
  removeWidget();
  editWidget();
}

/**
 * Remove widget on Preview panel
 */
function removeWidget() {
  $('.glyphicon-remove').on("click", function (e) {
    let widget = $(this).closest(".grid-stack-item");
    let widgetType = widget.data('type');
    PreviewGrid.deleteWidget(widget);
    if (MAIN_CONTENT_TYPE === widgetType) {
      isHasMainContent = false;
      disableMainContentButton(false);
    }
    if (HEADER_TYPE === widgetType) {
      isHasHeader = false;
      disableHeaderButton(false);
    }
    if (FOOTER_TYPE === widgetType) {
      isHasFooter = false;
      disableFooterButton(false);
    }
    return false;
  });
}

function editWidget() {
  $('.glyphicon-cog').on("click", function (e) {
    let widgetId = $(this).data("id");
    const url = "/admin/widgetitem/edit/?id=" + widgetId + "&modal=true";
    openRequestedSinglePopup(url, "Edit Widget");
  });
}

function openRequestedSinglePopup(url, windowName) {
  if (windowObjectReference == null || windowObjectReference.closed) {
    windowObjectReference = window.open(url, windowName,
      "resizable,scrollbars,status");
  } else if (previousUrl !== url) {
    windowObjectReference = window.open(url, windowName,
      "resizable=yes,scrollbars=yes,status=yes");
    /* if the resource to load is different,
       then we load it in the already opened secondary window and then
       we bring such window back on top/in front of its parent window. */
    windowObjectReference.focus();
  } else {
    windowObjectReference.focus();
  }

  previousUrl = url;
  /* explanation: we store the current url in order to compare url
     in the event of another call of this function. */
}

$(function () {
  ReactDOM.render(
    <MainLayout />,
    document.getElementById('root')
  );
  disableButton();
});

/**
 * Handle disable Save and Cancel button.
 */
function disableButton() {
  let repositoryId = document.getElementById("repository-id").value;
  if (!repositoryId) {
    repositoryId = "0";
  }
  let saveGrid = document.getElementById("save-grid");
  let clearGrid = document.getElementById("clear-grid");
  if (String(repositoryId) === "0") {
    saveGrid.setAttribute('disabled', 'disabled');
    clearGrid.setAttribute('disabled', 'disabled');
  } else {
    saveGrid.removeAttribute('disabled');
    clearGrid.removeAttribute('disabled');
  }
}

function disableMainContentButton(isDisable) {
  if (isDisable) {
    $("#" + MAIN_CONTENT_BUTTON_ID).attr('disabled', 'disabled');
  } else {
    $("#" + MAIN_CONTENT_BUTTON_ID).removeAttr('disabled');
  }
}

function disableHeaderButton(isDisable) {
  if (isDisable) {
    $("." + HEADER_CLASS).attr("disabled", "disabled");
  } else {
    $("." + HEADER_CLASS).removeAttr("disabled");
  }
}

function disableFooterButton(isDisable) {
  if (isDisable) {
    $("." + FOOTER_CLASS).attr("disabled", "disabled");
  } else {
    $("." + FOOTER_CLASS).removeAttr("disabled");
  }
}

function addAlert(message) {
  $('#alerts').append(
    '<div class="alert alert-light" id="alert-style">' +
    '<button type="button" class="close" data-dismiss="alert">' +
    '&times;</button>' + message + '</div>'
  );
}

function alertModal(message) {
  document.querySelector("#inputModal").innerHTML = message;
  $("#allModal").modal("show");
}

/**
 * Save widget design setting.
 * @param {*} widgetDesignData
 */
function saveWidgetDesignSetting(widgetDesignData) {
  let repositoryId = document.getElementById("repository-id").value;
  let pageListSelectElement = document.getElementById("pages-list-select");
  let pageId = "0";
  let isMainLayout = true;
  if (pageListSelectElement && pageListSelectElement.options) {
    pageId = pageListSelectElement.value;
    let option = pageListSelectElement.options[pageListSelectElement.selectedIndex];
    if (option.dataset) {
      isMainLayout = (String(option.dataset.isMainLayout) === "true");
    }
  }
  if (String(repositoryId) === "0") {
    alertModal("Please select the Repository.");
    return false;
  } else if (!widgetDesignData) {
    //alert('Please add Widget to Preview panel.');
    alertModal("Please add Widget to Preview panel.");
    return false;
  }

  let saveData = JSON.stringify(widgetDesignData);
  let postData = {
    'repository_id': repositoryId,
    'settings': saveData
  };
  if (pageId && String(pageId) !== "0" && !isMainLayout) {  // Saving a page not the main layout
    postData.page_id = pageId
  }

  if (saveData && Object.keys(widgetDesignData).length) {
    $.ajax({
      url: SAVE_WIDGET_LAYOUT_SETTING_URL,
      type: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      data: JSON.stringify(postData),
      dataType: 'json',
      success: function (data) {
        let err_msg = data.error;
        if (err_msg) {
          alertModal(err_msg);
        } else if (!data.result) {
          alertModal("Failed to save Widget design.");
        } else {
          addAlert('Widget design has been saved successfully.');
          let elements = document.querySelectorAll('[data-type="' + ACCESS_COUNTER + '"]');
          let d = new Date();
          let date = d.getFullYear() + '-' + (d.getMonth() > 8 ? '' : '0') + (d.getMonth() + 1)
            + '-' + (d.getDate() > 9 ? '' : '0') + d.getDate();
          for (let index = 0; index < elements.length; index++) {
            if (!elements[index].getAttribute('data-created_date')) {
              elements[index].setAttribute('data-created_date', date);
            }
          }
        }
      },
      error: function (error) {
        console.log(error);
      }
    });
  } else {
    alertModal("Please add Widget to Preview panel.");
  }
}


function escapeHtml(unsafe) {
  return unsafe
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
