const { useState, useEffect  } = React;
const Trumbowyg = window['react-trumbowyg'];

const FREE_DESCRIPTION_TYPE = "Free description";
const NOTICE_TYPE = "Notice";
const NEW_ARRIVALS = "New arrivals";
const ACCESS_COUNTER = "Access counter";
const HEADER_TYPE = "Header";
const FOOTER_TYPE = "Footer";
const THEME_SETTING = [{"value" : 'default', "text": "Default"}, {"value": "simple", "text":"Simple"}, {"value": "side_line", "text":"Side Line"}];
const BORDER_STYLE_SETTING = [{"value" : "none", "text": "None"}, {"value": "solid", "text":"Solid"}, {"value":"dotted", "text":"Dotted"}, {"value": "double", "text":"Double"}];
const MENU_TYPE = "Menu";
const DEFAULT_BG_COLOR = "#FFFFFF";
const DEFAULT_BG_HEADER_FOOTER_COLOR = "#3D7FA1";
const DEFAULT_LABEL_COLOR = "#F5F5F5";
const DEFAULT_TEXT_COLOR = "#333333";
const DEFAULT_BORDER_COLOR = "#DDDDDD";
const DEFAULT_BORDER_STYLE = "solid";
const DEFAULT_THEME = "default";
const DEFAULT_MENU_BACKGROUND_COLOR = "#ffffff";
const DEFAULT_MENU_COLOR = "#000000";

function userSelectedInput(initialValue, getValueOfField, key_binding, componentHandle) {
    if(key_binding === "border_style" && !initialValue){
        initialValue = DEFAULT_BORDER_STYLE;
    }
    const [value, setValue] = useState(initialValue);
    function handleChange(e) {
        setValue(e.target.value);
        getValueOfField(key_binding, e.target.value);
        if(componentHandle) {
            componentHandle(key_binding, e.target.value);
        }
        e.preventDefault();
    }
    return {
      value,
      onChange: handleChange,
    };
  }

const ComponentSelectField = function(props){
    const selectedData = userSelectedInput(props.data_load, props.getValueOfField, props.key_binding);
    const [selectOptions, setSelectOptions] = useState([]);

    useEffect(() => {
        let options = [];
        if(props.url_request){
            fetch(props.url_request)
            .then(res => res.json())
            .then(
                (result) => {
                    if (result.options) {
                        options = result.options.map((option) => {
                            return (
                                <option key={option.value} value={option.value}>{option.text}</option>
                            )
                        });
                    } else {
                        options = result.repositories.map((repository) => {
                            return (
                                <option key={repository.id} value={repository.id}>{repository.id}</option>
                            )
                        });
                    }
                    setSelectOptions(options);
                },

                (error) => {
                    console.log(error);
                }
            )
        }
        else{
            if (props.key_binding === "border_style"){
                props.getValueOfField(props.key_binding, props.data_load || "solid");
            }
            else{
                props.getValueOfField(props.key_binding, props.data_load || props.data[0].text);
            }
            options = props.data.map((option) => {
                return (
                    <option key={option.value} value={option.value}>{option.text}</option>
                )
            });
            setSelectOptions(options);
        }
    },[]);

    return (
        <div className="form-group row">
            <label htmlFor="input_type" className="control-label col-xs-2 text-right">{props.name}{props.is_required ? <span className="style-red">*</span>:null}</label>
            <div className="controls col-xs-6">
                <select className="form-control" name={props.name} {...selectedData}>
                    {props.url_request ? <option value="0">Please select the&nbsp;{props.key_binding}</option> : null}
                    {selectOptions}
                </select>
            </div>
        </div>
    )
};

class ComponentRadioSelect extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
          menu_orientation: this.props.data_load,
        }
    }

    componentDidMount(){
        this.props.handleComponentDidMountOrientation(this.state.menu_orientation);
    }

    render() {
        return (
            <div className="form-group row">
                <label htmlFor="input_type" className="control-label col-xs-2 text-right">Orientation</label>
                <div className="controls col-xs-2">
                    <label className="radio-inline" htmlFor="radio_horizontal">
                        <input name="menu_orientation" id="radio_horizontal" value="horizontal" type="radio" onChange={this.props.handleChange} defaultChecked={this.state.menu_orientation === 'horizontal'} />
                        Horizontal
                    </label>
                    <label className="radio-inline" htmlFor="radio_vertical">
                        <input name="menu_orientation" id="radio_vertical" value="vertical" type="radio" onChange={this.props.handleChange} defaultChecked={this.state.menu_orientation === 'vertical'} />
                        Vertical
                     </label>
                </div>
            </div>
        )
    }
}

class ComponentTextboxField extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            value: '',
        };
        this.handleChange = this.handleChange.bind(this);
    }
    componentWillReceiveProps(props) {
        if (props.type !== this.props.type) {
            this.setState({
                value: ''
            })
        }
        if (props.data_change) {
            this.setState({
                value: props.data_load
            });
            this.props.getValueOfField("language", false);
        }
    }
    componentDidMount() {
        this.setState({
            value: this.props.data_load
        })
    }

    handleChange(event) {
        this.setState({ value: event.target.value });
        this.props.getValueOfField(this.props.key_binding, event.target.value.trim());
        event.preventDefault();
    }

    render() {
        return (
            <div className="form-group row">
                <label htmlFor="input_type" className="control-label col-xs-2 text-right">{this.props.name}{this.props.is_required ? <span className="style-red">*</span>:null}</label>
                <div className="controls col-xs-6">
                    <input name={this.props.name} id='label' type="text" value={this.state.value} onChange={this.handleChange} className="form-control" />
                </div>
            </div>
        )
    }
}


const ComponentTextboxForAccessCounter = function(props){
    const [value, setValue] = useState(props.value);

    function handleChange(event){
        setValue(event.target.value);
        props.handleChange(props.key_binding, event.target.value.trim());
        event.preventDefault();
    }

    useEffect(() => {
        if(props.data_change){
            let data = props.value || "";
            setValue(data);
        }
        props.getValueOfField("language", false);
      }, [props.data_change]);

    useEffect(() => {
        setValue(props.value);
      }, [props.value]);

    return(
        <div className="form-group row">
            <label htmlFor="input_type" className="control-label col-xs-2 text-right">{props.name}</label>
            <div className="controls col-xs-6">
                <input name={props.name} type="text" value={value} onChange={(event) => handleChange(event)} className="form-control" />
            </div>
        </div>
    )
};

const ComponentSelectColorFiled = (props) => {
    let initColor = '';
    if (props.key_binding === "label_text_color") {
        initColor = DEFAULT_TEXT_COLOR;
    }
    else if (props.key_binding === "background_color") {
        if (props.type === HEADER_TYPE || props.type === FOOTER_TYPE) {
            initColor = DEFAULT_BG_HEADER_FOOTER_COLOR;
        } else {
            initColor = DEFAULT_BG_COLOR;
        }
    }
    else if (props.key_binding === "label_color") {
        initColor = DEFAULT_LABEL_COLOR;
    }else if(props.key_binding === "menu_bg_color" || props.key_binding === "menu_active_bg_color") {
        initColor = DEFAULT_MENU_BACKGROUND_COLOR;
    }else if(props.key_binding === "menu_default_color" || props.key_binding === "menu_active_color"){
        initColor = DEFAULT_MENU_COLOR;
    }
    else {
        initColor = DEFAULT_BORDER_COLOR;
    }

    const [value, setValue] = useState(props.data_load || initColor);
    useEffect(() => {
        if(props.handleChange){
            props.handleChange(props.key_binding, value);
        }
        props.getValueOfField(props.key_binding, props.data_load || initColor);
    }, []);

    useEffect(() => {
        if (props.key_binding === "background_color") {
            if (!(props.is_edit) && [HEADER_TYPE, FOOTER_TYPE].includes(props.type)) {
                setValue(DEFAULT_BG_HEADER_FOOTER_COLOR);
                props.getValueOfField(props.key_binding, DEFAULT_BG_HEADER_FOOTER_COLOR);
            }
        }
    }, [props.type]);

    function handleChange(e) {
        setValue(e.target.value);
        props.getValueOfField(props.key_binding, e.target.value);
        if (props.handleChange) {
            props.handleChange(props.key_binding, e.target.value);
        }
        e.preventDefault();
    }

    return (
        <div className="form-group row">
            <label htmlFor="input_type" className="control-label col-xs-2 text-right">{props.name}</label>
            <div className="controls col-xs-2">
                <input name={props.name} type="color" className="style-select-color" value = {value} onChange = {(event) => handleChange(event)} />
            </div>
        </div>
    )
};

function userCheckboxInput(initialValue, getValueOfField, key_binding) {
    const [value, setValue] = useState(initialValue);
    function handleChange(e) {
        setValue(e.target.value);
        getValueOfField(key_binding, e.target.checked);
    }
    return {
        defaultChecked: value,
        onChange: handleChange,
    };
  }

const ComponentCheckboxField = function(props){
    const is_default_Checked = userCheckboxInput(props.data_load || false, props.getValueOfField, props.key_binding);

    return (
        <div className="form-group row">
            <label htmlFor="input_type" className="control-label col-xs-2 text-right">{props.name}</label>
            <div className="controls col-xs-1">
                <input name={props.name} type="checkbox" {...is_default_Checked}/>
            </div>
        </div>
    )
};

class ComponentFieldContainSelectMultiple extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            selectOptions: [],
            UnauthorizedOptions: [],
            language: this.props.language,
            rightSelected: [],
            leftSelected: [],
        };
        this.handleChange = this.handleChange.bind(this);
        this.updateGlobalValues = this.updateGlobalValues.bind(this);
        this.handleMoveRightClick = this.handleMoveRightClick.bind(this);
        this.handleMoveLeftClick = this.handleMoveLeftClick.bind(this);
        this.handleMoveUpClick = this.handleMoveUpClick.bind(this);
        this.handleMoveDownClick = this.handleMoveDownClick.bind(this);
        this.initSelectBox = this.initSelectBox.bind(this);
        this.onLeftSelectChange = this.onLeftSelectChange.bind(this);
        this.onRightSelectChange = this.onRightSelectChange.bind(this);
        this.getSelectedOption = this.getSelectedOption.bind(this);
        this.isValueExist = this.isValueExist.bind(this);
    }
    componentDidMount() {
        this.initSelectBox(this.props.url_request, this.props.repositoryId);
    }

    handleChange(event) {
        this.setState({ repositoryId: event.target.value });
        event.preventDefault();
    }

    initSelectBox(url, repositoryId) {
        let data = {
          repository_id: repositoryId
        };
        fetch(url, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(data)})
            .then(res => res.json())
            .then(
                (result) => {
                    let unOptions = [];
                    let orderedOptions = [];
                    let choseOptions = [];

                    // Special case for when we use this for page services
                    if(typeof result == 'object' && 'page-list' in result) {
                        result = result['page-list']['data'];
                    }

                    // Display in order according to saved settings FIXME: High complexity, find another way
                    let current_selections = this.props.data_load;
                    let currentSelectionString = current_selections.map(select => String(select));
                    for (let i = 0; i < current_selections.length; i++) {
                        for (let j = 0; j < result.length; j++) {
                            if(String(current_selections[i]) === result[j].id.toString()) {
                                orderedOptions.push(<option key={result[j].id} value={result[j].id}>{result[j].name}</option>);
                                choseOptions.push(result[j].id);
                            }
                        }
                    }

                    let hasMainLayout = false;
                    let options = result.map((option) => {
                        if (option.is_main_layout) {
                          hasMainLayout = true;
                        }
                        if (this.props.is_edit === true) {
                            if (!currentSelectionString.includes(option.id.toString())) {
                                let innerhtml = <option key={option.id} value={option.id}>{option.name}</option>;
                                unOptions.push(innerhtml);
                            }
                        }
                        else {
                            choseOptions.push(option.id);
                            return (
                                <option key={option.id} value={option.id}>{option.name}</option>
                            )
                        }
                    });
                    options = options.filter((option)=> typeof option !== "undefined");
                    if (this.props.is_edit === true) {  // Only add ordered options if editing
                      options = orderedOptions.concat(options);
                      if (currentSelectionString.includes("0") && !hasMainLayout) {
                        options.unshift(<option key={0} value={0}>Main Layout</option>);
                        choseOptions.push("0");
                      } else if (!hasMainLayout) {
                        unOptions.unshift(<option key={0} value={0}>Main Layout</option>);
                      }
                    } else if (!hasMainLayout) {
                      options.unshift(<option key={0} value={0}>Main Layout</option>);
                      choseOptions.push("0");
                    }
                    this.setState({
                        selectOptions: options,
                        UnauthorizedOptions: unOptions
                    });
                    if(Array.isArray(choseOptions) && choseOptions.length){
                        this.props.getValueOfField(this.props.key_binding, choseOptions);
                    }
                },
                (error) => {
                    console.log(error);
                }
            )

    }

    getListOption(id) {
        let options = document.getElementById(id).options;
        let result = [];
        for (let option in options) {
            if (options[option].value) {
                let innerhtml = <option key={options[option].value} value={options[option].value}>{options[option].text}</option>;
                result.push(innerhtml);
            }
        }
        return result;
    }

    // Get the new page titles on change of lang
    componentWillReceiveProps(nextProps) {
        if((nextProps.language !== this.state.language &&
           this.props.key_binding === "menu_show_pages" )) {
              this.setState({language: nextProps.language});
              let loadPagesURL = "/api/admin/load_widget_design_pages/" +
                  nextProps.language;
              this.initSelectBox(loadPagesURL, this.props.repositoryId); // Re-ender tables select box
        }
        if(nextProps.repositoryId !== this.props.repositoryId && this.props.key_binding === "menu_show_pages"){
            let loadPagesURL = "/api/admin/load_widget_design_pages/" + this.state.language;
            this.initSelectBox(loadPagesURL, nextProps.repositoryId);
        }
    }

    isValueExist(item, array) {
      let isExisted = false;
      if (array === undefined) {
        return isExisted;
      }
      if (array.length > 0) {
        for (let prop in array) {
          if (array[prop].props.value === item) {
              isExisted = true;
              break;
          }
        }
      } else {
        return isExisted;
      }
      return isExisted;
    }

    updateGlobalValues(optionsList) {
        let data = [];
        for (let option in optionsList) {
            data.push(optionsList[option].props.value);
        }
        this.props.getValueOfField(this.props.key_binding, data);
    }

    handleMoveRightClick(event) {
        event.preventDefault();
        let options = document.getElementById(this.props.authorSelect).options;
        let selectedOptions = this.getListOption(this.props.unauthorSelect);
        let nonSelectOptions = [];
        for (let option in options) {
            if (options[option].selected) {
                let innerhtml = <option key={options[option].value} value={options[option].value}>{options[option].text}</option>;
                if (!this.isValueExist(options[option].value, selectedOptions) && options[option].value) {
                    selectedOptions.push(innerhtml);
                }
            } else {
                let innerhtml = <option key={options[option].value} value={options[option].value}>{options[option].text}</option>;
                if (options[option].value) {
                    nonSelectOptions.push(innerhtml);
                }
            }
        }
        this.setState({
            selectOptions: nonSelectOptions,
            UnauthorizedOptions: selectedOptions,
        });
        this.updateGlobalValues(nonSelectOptions);
    }

    handleMoveLeftClick(event) {
        let options = document.getElementById(this.props.unauthorSelect).options;
        let authorizedOptions = this.getListOption(this.props.authorSelect);
        let remainOption = [];
        for (let key in options) {
            let option = options[key];
            if (!option.value) {
                continue;
            }
            let innerHTML = <option key={option.value} value={option.value}>{option.text}</option>;
            if (option.selected) {
                if (!this.isValueExist(option.value, authorizedOptions)) {
                    authorizedOptions.push(innerHTML);
                }
            } else {
                remainOption.push(innerHTML);
            }
        }
        this.setState({
            selectOptions: authorizedOptions,
            UnauthorizedOptions: remainOption,
        });
        this.updateGlobalValues(authorizedOptions);
        event.preventDefault();
    }

    handleMoveUpClick(event) {
        event.preventDefault();
        let options = document.getElementById(this.props.authorSelect).options;
        let reOrderedOptions = this.getListOption(this.props.authorSelect);
        for (let option in options) {
            if(options[option].value) {
                if (options[option].selected && option > 0) {
                    let prevOption = reOrderedOptions.splice((option - 1), 1)[0];
                    reOrderedOptions.splice(option, 0, prevOption);
                }
            }
        }
        this.setState({ selectOptions: reOrderedOptions });
        this.updateGlobalValues(reOrderedOptions);
    }

    handleMoveDownClick(event){
        event.preventDefault();
        let options = document.getElementById(this.props.authorSelect).options;
        let reOrderedOptions = this.getListOption(this.props.authorSelect);
        let choseOption;
        for(let i = 0; i < options.length; i++){
            if(options[i].selected){
                choseOption = reOrderedOptions[i];
                reOrderedOptions.splice(i, 1);
                reOrderedOptions.splice(i + 1, 0, choseOption);
                this.updateGlobalValues(reOrderedOptions);
                this.setState({ selectOptions: reOrderedOptions });
                break;
            }
        }
    }

    getSelectedOption(options) {
      let data = [];
      for (let key in options) {
        let option = options[key];
        if (option.value && option.selected) {
          data.push(option.value);
        }
      }
      return data;
    }

    onLeftSelectChange(event) {
      let options = event.target.options;
      let data = this.getSelectedOption(options);
      this.setState({
        leftSelected: data
      })
    }

    onRightSelectChange(event) {
      let options = event.target.options;
      let data = this.getSelectedOption(options);
      this.setState({
        rightSelected: data
      })
    }

    render() {
        let rowClass = "col-xs-5";
        let upDownArrows = null;
        if(this.props.enableUpDownArrows) {
          rowClass = "col-xs-4";
          upDownArrows = (
              <div className="col-xs-2">
                  <br />
                  <div className="style-center-align">
                      <div className="buttons style-button-container">
                          <input type="button" value="&uarr;" className="style-button-element" onClick={this.handleMoveUpClick} />
                          <input type="button" value="&darr;" className="style-button-element" onClick={this.handleMoveDownClick} />
                      </div>
                  </div>
              </div>
          );
        }
        return (
            <div className="form-group row">
                <label htmlFor="input_type" className="control-label col-xs-2 text-right" >{this.props.name}</label>
                <div className="controls col-xs-9">
                    <fieldset className="form-group style-container">
                        { upDownArrows }
                        <div className={"style-element " + rowClass}>
                            <span>{this.props.leftBoxTitle}</span><br />
                            <select onChange={this.onLeftSelectChange} multiple className="style-select-left" value={this.state.leftSelected}
                                id={this.props.authorSelect} name={this.props.authorSelect}>
                                {this.state.selectOptions}
                            </select>
                        </div>
                        <div className="col-xs-2">
                            <br />
                            <div className="style-center-align">
                                <div className="buttons style-button-container">
                                    <input type="button" value="&rarr;" className="style-button-element" onClick={this.handleMoveRightClick} />
                                    <input type="button" value="&larr;" className="style-button-element" onClick={this.handleMoveLeftClick} />
                                </div>
                            </div>
                        </div>
                        <div className={"style-element style-element-right " + rowClass }>
                            <span>{this.props.rightBoxTitle}</span><br />
                            <select multiple onChange={this.onRightSelectChange} className="style-select-right" value={this.state.rightSelected}
                                id={this.props.unauthorSelect} name={this.props.unauthorSelect}>
                                {this.state.UnauthorizedOptions}
                            </select>
                        </div>
                    </fieldset>
                </div>
            </div>
        )
    }
}

const TrumbowygWrapper = props => {
  const [value, setValue] = useState();

  useEffect(() => {
    if (props.value != $("#" + props.id)[0].innerHTML) {
      setValue(props.value);
    }
  }, [props.value]);

  function handleChange(e) {
    props.onChange(e.target.innerHTML);
  }

  return (
    <React.Fragment>
      <Trumbowyg.default
        autogrow
        id={props.id}
        onChange={handleChange}
        data={value}
        buttons={props.buttons}
        btnsDef={props.btnsDef}
        plugins={props.plugins}
      />
    </React.Fragment>
  );
};

const ComponentFieldEditor = function (props) {
  const [value, setValue] = useState(props.data_load || "");
  const btnsDef = {
    image: {
      dropdown: ["insertImage", "base64"],
      ico: "insertImage"
    }
  };
  const buttons = [
    ["viewHTML"],
    ["undo", "redo"], // Only supported in Blink browsers
    ["formatting"],
    ['fontfamily', 'fontsize'],
    ["strong", "em", "del", 'underline', "superscript", "subscript"],
    ['foreColor', 'backColor'],
    ["link"],
    ["image"],
    ["justifyLeft", "justifyCenter", "justifyRight", "justifyFull"],
    ["unorderedList", "orderedList"],
    ["horizontalRule"],
    ["removeformat"],
    ["fullscreen"]
  ];

  const plugins = {
    resizimg: {
      minSize: 64,
      step: 16
    },
  };

  useEffect(() => {
    if (props.data_change) {
      setValue(props.data_load);
      props.getValueOfField("language", false);
    }
  }, [props.data_change]);

  const handleChange = data => {
    setValue(data);
    props.handleChange(props.key_binding, data);
  };

  return (
    <div className="form-group row">
      <label htmlFor="input_type" className="control-label col-xs-2 text-right">
        {props.name}
      </label>
      <div className="controls col-xs-9">
        <TrumbowygWrapper
          key={props.language}
          id={props.key_binding}
          onChange={handleChange}
          value={value}
          buttons={buttons}
          btnsDef={btnsDef}
          plugins={plugins}
        />
      </div>
    </div>
  );
};

class ExtendComponent extends React.Component {
    constructor(props) {
        super(props);
        if (this.props.type === NOTICE_TYPE) {
            if (this.props.data_load.more_description) {
                this.state = {
                    type: this.props.type,
                    settings: this.props.data_load,
                    write_more: true,
                };
            }
            else {
                this.state = {
                    type: this.props.type,
                    settings: this.props.data_load,
                    write_more: false,
                };
            }
        }
        else {
            this.state = {
                type: this.props.type,
                settings: this.props.data_load,
            }
        }
        this.handleChange = this.handleChange.bind(this);
        this.handleChangeCheckBox = this.handleChangeCheckBox.bind(this);
        this.handleChangeHideTheRest = this.handleChangeHideTheRest.bind(this);
        this.handleChangeReadMore = this.handleChangeReadMore.bind(this);
        this.handleChangeAccessCounter = this.handleChangeAccessCounter.bind(this);
        this.handleChangeNewDates = this.handleChangeNewDates.bind(this);
        this.handleChangeDisplayResult = this.handleChangeDisplayResult.bind(this);
        this.handleChangeRssFeed = this.handleChangeRssFeed.bind(this);
        this.generateNewDate = this.generateNewDate.bind(this);
        this.generateDisplayResult = this.generateDisplayResult.bind(this);
        this.handleOrientationRadio = this.handleOrientationRadio.bind(this);
        this.handleChangeMenuColor = this.handleChangeMenuColor.bind(this);
        this.handleComponentDidMountOrientation = this.handleComponentDidMountOrientation.bind(this);
    }
    static getDerivedStateFromProps(nextProps, prevState) {
        if (nextProps.data_load && !prevState.write_more && nextProps.data_load.more_description) {
            return {
                write_more: true,
                settings: nextProps.data_load
            }
        }
        if (nextProps.type !== prevState.type) {
            let defaultSettings = {};
            if (nextProps.type === NEW_ARRIVALS){
                defaultSettings['new_dates'] = '5';
                defaultSettings['display_result'] = '5';
            }
            else {
                defaultSettings = {};
            }
            return {
                type: nextProps.type,
                settings: defaultSettings,
                write_more: false
            };
        }
        if (nextProps.data_change) {
            let setting = nextProps.data_load;
            nextProps.getValueOfField("language", false);
            let read_more = document.getElementById("read_more");
            let hide_the_rest = document.getElementById("hide_the_rest");
            if (read_more) {
                if (setting['read_more']) {
                    read_more.value = setting['read_more'];
                } else {
                    read_more.value = '';
                }
            }
            if (hide_the_rest) {
                if (setting['hide_the_rest']) {
                    hide_the_rest.value = setting['hide_the_rest'];
                } else {
                    hide_the_rest.value = '';
                }
            }
            if (nextProps.type === ACCESS_COUNTER) {
                setting["access_counter"] = nextProps.init_value;
            }
            return {
                settings: setting
            }
        }
        return null;
    }

    generateNewDate(){
        let newDates =['Today'];
        for(let i=1; i<31; i++)
        {
            newDates.push(i+"");
        }

        let options = newDates.map((value) => {
            return (
                <option>{value}</option>
            )
        });

        return (
            <select value={this.state.settings.new_dates} onChange={this.handleChangeNewDates} className="form-control" name="new_dates">
                {options}
            </select>
        )
    }

    generateDisplayResult(){
        let displayResult =['5','10','20','50','100'];

        let options = displayResult.map((value) => {
            return (
                <option>{value}</option>
            )
        });

        return (
            <select value={this.state.settings.display_result} onChange={this.handleChangeDisplayResult} className="form-control" name="new_dates">
                {options}
            </select>
        )
    }

    handleChange(field, value) {
        let data = this.state.settings;
        data[field] = value;
        this.setState({
            settings: data
        });
        this.props.getValueOfField(this.props.key_binding, data);
    }

    handleChangeCheckBox(event) {
        let data = this.state.settings;
        data.more_description = '';
        data.read_more = '';
        data.hide_the_rest = '';
        this.setState({
            write_more: event.target.checked,
            settings: data,
        });
        this.props.getValueOfField(this.props.key_binding, data);
        this.render();
    }

    handleChangeHideTheRest(event) {
        let setting = this.state.settings;
        setting['hide_the_rest'] = event.target.value;
        this.setState({ settings: setting });
        this.handleChange("hide_the_rest", event.target.value);
    }

    handleChangeReadMore(event) {
        let setting = this.state.settings;
        setting['read_more'] = event.target.value;
        this.setState({ settings: setting });
        this.handleChange("read_more", event.target.value);
    }

    handleChangeAccessCounter(event){
        let setting = this.state.settings;
        setting['access_counter'] = event.target.value;
        this.setState({ settings: setting });
        this.handleChange("access_counter", event.target.value);
        this.props.getValueOfField('accessInitValue', event.target.value);
    }

    handleChangeNewDates(event) {
        let setting = this.state.settings;
        setting['new_dates'] = event.target.value;
        this.setState({ settings: setting });
        this.handleChange("new_dates", event.target.value);
    }

    handleChangeDisplayResult(event){
        let setting = this.state.settings;
        setting['display_result'] = event.target.value;
        this.setState({ settings: setting });
        this.handleChange("display_result", event.target.value);
    }

    handleChangeRssFeed(event){
        let setting = this.state.settings;
        setting['rss_feed'] = event.target.checked;
        this.setState({ settings: setting });
        this.handleChange("rss_feed", event.target.checked);
    }

    handleChangeMenuColor(event, part){  //No longer used???
        let setting = this.state.settings;
        setting[part] = event.target.value;
        this.setState({ settings: setting });
        this.handleChange(part, event.target.value);
    }

    handleOrientationRadio(event){
        let setting = this.state.settings;
        setting['menu_orientation'] = event.target.value;
        this.setState({ settings: setting });
        this.handleChange('menu_orientation', event.target.value);
    }

    handleComponentDidMountOrientation(typeOfOrientation){
        let setting = this.state.settings;
        setting['menu_orientation'] = typeOfOrientation;
        this.setState({ settings: setting });
        this.props.getValueOfField(this.props.key_binding, typeOfOrientation);
    }


    render() {
        if (this.state.type === FREE_DESCRIPTION_TYPE) {
            return (
                <div>
                    <ComponentFieldEditor key={this.state.type + this.props.language} language={this.props.language} handleChange={this.handleChange} name="Free description" key_binding="description" data_load={this.state.settings.description} data_change={this.props.data_change} getValueOfField={this.props.getValueOfField} />
                </div>
            )
        }
        else if (this.state.type === HEADER_TYPE || this.state.type === FOOTER_TYPE){
            return (
                <div>
                    <ComponentFieldEditor key={this.state.type + this.props.language} language={this.props.language} handleChange={this.handleChange} name={this.state.type === HEADER_TYPE ? "Header setting" : "Footer setting"} key_binding="description" data_load={this.state.settings.description} data_change={this.props.data_change} getValueOfField={this.props.getValueOfField} />
                </div>
            )
        }
        else if (this.state.type === NOTICE_TYPE) {
            if (this.state.write_more === false) {
                return (
                    <div>
                        <div>
                            <ComponentFieldEditor key={this.state.type + this.props.language + "description"} language={this.props.language} handleChange={this.handleChange} name="Notice description" key_binding="description" data_load={this.state.settings.description} data_change={this.props.data_change} getValueOfField={this.props.getValueOfField} />
                        </div>
                        <div className="row">
                            <div className="controls col-xs-offset-2 col-xs-10">
                                <input name="write_more" type="checkbox" onChange={this.handleChangeCheckBox} defaultChecked={this.state.settings.write_more} />
                                <span>&nbsp;Write more</span>
                            </div>
                        </div>
                    </div>
                )
            }
            else {
                return (
                    <div>
                        <div>
                            <ComponentFieldEditor key={this.state.type + this.props.language + "description"} language={this.props.language} handleChange={this.handleChange} name="Notice description" key_binding="description" data_load={this.state.settings.description} data_change={this.props.data_change} getValueOfField={this.props.getValueOfField} />
                        </div>
                        <div className="row">
                            <div className="controls col-xs-offset-2 col-xs-10">
                                <div>
                                    <input name="write_more" type="checkbox" onChange={this.handleChangeCheckBox} defaultChecked={this.state.write_more} />
                                    <span>&nbsp;Write more</span>
                                </div>
                                <br />
                                <div className="sub-text-box">
                                    <input type="text"  id="read_more" name="read_more" onChange={this.handleChangeReadMore} className="form-control" placeholder="Read more" value={this.state.settings.read_more} />
                                </div>
                                <br />
                            </div>
                        </div>
                        <div>
                            <ComponentFieldEditor key={this.state.type + this.props.language + "more_description"} language={this.props.language} handleChange={this.handleChange} name="" key_binding="more_description" data_load={this.state.settings.more_description} data_change={this.props.data_change} getValueOfField={this.props.getValueOfField} />
                        </div>
                        <div className="row">
                            <div className="controls col-xs-offset-2 col-xs-10">
                                <div className="sub-text-box">
                                    <input type="text" id="hide_the_rest" name="hide_the_rest" onChange={this.handleChangeHideTheRest} className="form-control" placeholder="Hide the rest" value={this.state.settings.hide_the_rest} />
                                </div>
                                <br />
                            </div>
                        </div>
                    </div>
                )
            }
        }
        else if(this.state.type === ACCESS_COUNTER){
            return(
                <div>
                    <div className="form-group row">
                        <label htmlFor="Access_counter" className="control-label col-xs-2 text-right">Access counter initial value</label>
                        <div className="controls col-xs-3">
                            <input name="Access_counter" id='Access_counter' type="input" value={this.state.settings.access_counter || "0"} onChange={this.handleChangeAccessCounter} className="form-control" />
                        </div>
                    </div>
                    <div className="form-group">
                        <ComponentTextboxForAccessCounter name = "Preceding message" key_binding="preceding_message" handleChange={this.handleChange} getValueOfField={this.props.getValueOfField} value = {this.state.settings.preceding_message || ""} data_change={this.props.data_change}/>
                    </div>
                    <div className="form-group">
                        <ComponentTextboxForAccessCounter name = "Following message" key_binding="following_message" handleChange={this.handleChange} getValueOfField={this.props.getValueOfField} value = {this.state.settings.following_message || ""} data_change={this.props.data_change}/>
                    </div>
                    <div className="form-group">
                        <ComponentTextboxForAccessCounter name = "Other message to display" key_binding="other_message" handleChange={this.handleChange} getValueOfField={this.props.getValueOfField} value = {this.state.settings.other_message || ""} data_change={this.props.data_change}/>
                    </div>
                </div>
            )
        }
        else if(this.state.type === NEW_ARRIVALS){
            return(
                <div>
                    <div className="form-group row">
                        <label htmlFor="new_dates" className="control-label col-xs-2 text-right">New date</label>
                        <div className="controls col-xs-3">
                            {this.generateNewDate()}
                        </div>
                    </div>
                    <div className="form-group row">
                        <label htmlFor="display_result" className="control-label col-xs-2 text-right">Display Results</label>
                        <div className="controls col-xs-3">
                            {this.generateDisplayResult()}
                        </div>
                    </div>
                    <div className="form-group row">
                        <label htmlFor="rss_feed" className="control-label col-xs-2 text-right">RSS feed</label>
                        <div className="controls col-xs-1">
                            <input name="rss_feed" type="checkbox" onChange={this.handleChangeRssFeed} defaultChecked={this.state.settings.rss_feed} />
                        </div>
                    </div>
                </div>
            )
        }
        else if(this.state.type === MENU_TYPE){
            let loadPagesURL = "/api/admin/load_widget_design_pages/" +
                this.props.language;
            return(
                <div>
                  <ComponentRadioSelect handleComponentDidMountOrientation={this.handleComponentDidMountOrientation} handleChange={this.handleOrientationRadio} getValueOfField={this.props.getValueOfField} name="Display Orientation" key_binding="menu_orientation" data_load={this.state.settings.menu_orientation || 'horizontal'} />
                  <ComponentSelectColorFiled getValueOfField={this.props.getValueOfField} handleChange={this.handleChange} name="Background Color" key_binding="menu_bg_color" data_load={this.state.settings.menu_bg_color} />
                  <ComponentSelectColorFiled getValueOfField={this.props.getValueOfField} handleChange={this.handleChange} name="Active Background Color" key_binding="menu_active_bg_color" data_load={this.state.settings.menu_active_bg_color} />
                  <ComponentSelectColorFiled getValueOfField={this.props.getValueOfField} handleChange={this.handleChange} name="Default Color" key_binding="menu_default_color" data_load={this.state.settings.menu_default_color} />
                  <ComponentSelectColorFiled getValueOfField={this.props.getValueOfField} handleChange={this.handleChange} name="Active Color" key_binding="menu_active_color" data_load={this.state.settings.menu_active_color} />
                  <ComponentFieldContainSelectMultiple getValueOfField={this.handleChange} name="Show/Hide Pages"
                      authorSelect="showPageSelect" unauthorSelect="hidePageSelect" url_request={loadPagesURL}
                      key_binding="menu_show_pages" data_load={this.state.settings.menu_show_pages || []} is_edit={this.props.is_edit}
                      leftBoxTitle="Show" rightBoxTitle="Hide" enableUpDownArrows={true} data_change={this.props.data_change}
                      language={this.props.language} repositoryId={this.props.repositoryId} />
                </div>
            )
        }
        else {
            return (
                <div>
                </div>
            )
        }
    }
}

class ComponentButtonLayout extends React.Component {
    constructor(props) {
        super(props);
        this.saveCommand = this.saveCommand.bind(this);
        this.deleteCommand = this.deleteCommand.bind(this);
        this.isLabelValid = this.isLabelValid.bind(this);
        this.validateFieldIsValid = this.validateFieldIsValid.bind(this);
        this.showErrorMessage = this.showErrorMessage.bind(this);
    }

    saveCommand(event) {
        function addAlert(message) {
            $('#alerts').append(
                '<div class="alert alert-light" id="alert-style">' +
                '<button type="button" class="close" data-dismiss="alert">' +
                '&times;</button>' + message + '</div>');
        }
        // Convert data
        let data = this.props.data;
        let multiLangData = data['multiLangSetting'];
        let currentLabel = data['label'];
        let currentDescription = data['settings'];
        let currentLanguage = $("#language")[0].value;

        let noData = true;
        for (let currentDescriptionKey in currentDescription) {
            if (currentDescription[currentDescriptionKey]) {
                noData = false;
                break;
            }
        }
        if (currentLabel || !noData) {
            let currentLangData = {
                label: currentLabel,
            };
            if([FREE_DESCRIPTION_TYPE, NOTICE_TYPE, ACCESS_COUNTER, HEADER_TYPE, FOOTER_TYPE].includes(data['widget_type'])){
                currentLangData["description"] = currentDescription;
            }
            multiLangData[currentLanguage] = currentLangData;
        }else {
            delete multiLangData[currentLanguage];
        }
        if ((data['widget_type'] + "") === ACCESS_COUNTER) {
            for (let [key, value] of Object.entries(multiLangData)) {
                value.description['access_counter'] = data.accessInitValue
            }
        }
        this.props.getValueOfField('multiLangData', multiLangData);
        this.props.getValueOfField('accessInitValue', data.accessInitValue);
        data['multiLangSetting'] = multiLangData;
        delete data['accessInitValue'];

        let request = {
            flag_edit: this.props.is_edit,
            data: data,
            data_id: '',
        };
        request.data_id = this.props.data_id;
        let data_validate = this.validateFieldIsValid(data.widget_type);
        if (data.repository === "0" || data.repository === "") {
            let errorMessage = "Repository is required!";
            this.showErrorMessage(errorMessage);
        } else if (data.widget_type === "0" || data.widget_type === "") {
            let errorMessage = "Type is required.";
            this.showErrorMessage(errorMessage);
        } else if (!this.isLabelValid(data['multiLangSetting'])) {
            let errorMessage = "Label is required!";
            this.showErrorMessage(errorMessage);
        } else if(!data_validate.status){
            let errorMessage = data_validate.error;
            this.showErrorMessage(errorMessage);
        }else {
            return fetch(this.props.url_request, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(request),
            })
                .then(res => res.json())
                .then((result) => {
                    if (result.success) {
                        addAlert(result.message);
                    } else {
                        let errorMessage = result.message;
                        this.showErrorMessage(errorMessage);
                    }
                });
        }
    }

    showErrorMessage(errorMessage) {
      $("#inputModal").html(errorMessage);
      $("#allModal").modal("show");
    }

    validateFieldIsValid(widget_type){
        if(widget_type === ACCESS_COUNTER){
            let access_val = $('#Access_counter').val() || "0";
            if (Number.isNaN(Number(access_val)) || Number(access_val) < 0){
                return {
                    status : false,
                    error: "Please enter half-width numbers."
                };
            }
            else if(access_val.length > 9){
                return {
                    status : false,
                    error: "The input value exceeds 9 digits."
                };
            }
        }
        return{
            status : true,
            error: ""
        }
    }

    isLabelValid(multiLangData) {
        if ($.isEmptyObject(multiLangData)) {
            return false;
        }
        let selectedLanguage = $("#language")[0].value;
        if (!multiLangData[selectedLanguage]) {
            return false;
        } else {
            if (!multiLangData[selectedLanguage]['label']) {
                return false;
            }
        }

        let isValid = true;
        for (let data in multiLangData) {
            let label = multiLangData[data]['label'];
            let noData = true;
            if (!$.isEmptyObject(multiLangData[data]['description'])) {
                let description = multiLangData[data]['description'];
                for (data in description) {
                    if (description[data]) {
                        noData = false;
                        break;
                    }
                }
            }
            if (!label) {
                if (!noData) {
                    isValid = false;
                    break;
                }
            }
        }
        return isValid;
    }

    deleteCommand(event) {
        function addAlert(message) {
            $('#alerts').append(
                '<div class="alert alert-light" id="alert-style">' +
                '<button type="button" class="close" data-dismiss="alert">' +
                '&times;</button>' + message + '</div>');
        }

        let request = {
            data_id: this.props.data_id
        };
        if (confirm("Are you sure to delete this widget Item ?")) {
            return fetch('/api/admin/delete_widget_item', {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(request),
            })
                .then(res => res.json())
                .then((result) => {
                    if (result.success) {
                        addAlert(result.message);
                        window.location = this.props.return_url;
                    } else {
                        //alert(result.message);
                        let errorMessage = result.message;
                        this.showErrorMessage(errorMessage);
                    }
                });
        }
    }

    render() {
        if (this.props.is_edit) {
            return (
                <div className="form-group row">
                    <div className="col-xs-offset-2 col-xs-5">
                        <button className="btn btn-primary save-button" onClick={this.saveCommand}>
                            <span className="glyphicon glyphicon-download-alt" aria-hidden="true"/>
                            &nbsp;Save
                        </button>
                        <a href={this.props.return_url} className="form-group btn btn-info cancel-button style-my-button">
                            <span className="glyphicon glyphicon-remove" aria-hidden="true"/>
                            &nbsp;Cancel
                        </a>
                        <button className="btn btn-danger delete-button style-my-button" onClick={this.deleteCommand}>
                            <span className="glyphicon glyphicon-trash" aria-hidden="true"/>
                            &nbsp;Delete
                        </button>
                    </div>
                </div>
            )
        }
        else {
            return (
                <div className="form-group row">
                    <div className="col-xs-offset-2 col-xs-5">
                        <button className="btn btn-primary save-button " onClick={this.saveCommand}>
                            <span className="glyphicon glyphicon-download-alt" aria-hidden="true"/>
                            &nbsp;Save
                        </button>
                        <a href={this.props.return_url} className="form-group btn btn-info cancel-button style-my-button">
                            <span className="glyphicon glyphicon-remove" aria-hidden="true"/>
                            &nbsp;Cancel
                        </a>
                    </div>
                </div>
            )
        }
    }
}

class ComponentLanguage extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            languageList: [],
            languageNameList: {},
            registeredLanguage: [],
            options: [],
            selectedLanguage: '0',
            defaultLanguage: ''
        };
        this.initLanguageList = this.initLanguageList.bind(this);
        this.handleChange = this.handleChange.bind(this);
        this.displayOptions = this.displayOptions.bind(this);
        this.removeDuplicatedLang = this.removeDuplicatedLang.bind(this);
    }
    removeDuplicatedLang(langList, registeredLang) {
        registeredLang.forEach(function(lang) {
            let index = langList.indexOf(lang);
            if (index !== -1) {
                langList.splice(index, 1);
            }
        });
        return langList;
    }
    initLanguageList() {
        let langList = [];
        let langName = {};
        let systemRegisteredLang = [];
        let registeredLang = [];
        fetch('/api/admin/get_system_lang')
            .then(res => res.json())
            .then((result) => {
                if (result.error) {
                    let modalcontent = "Can't get system language! \nDetail: " + result.error;
                    $("#inputModal").html(modalcontent);
                    $("#allModal").modal("show");
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
                        langName[lang.lang_code] = lang.lang_name;
                    });
                    for (let i = systemRegisteredLang.length; i >= 0; i--) {
                        for (let j = 0; j < systemRegisteredLang.length; j++) {
                            if (systemRegisteredLang[j].sequence == i) {
                                langList.unshift(systemRegisteredLang[j].code);
                            }
                        }
                    }
                    if (!$.isEmptyObject(this.props.data_load)) {
                        registeredLang = Object.keys(this.props.data_load);
                        langList.forEach(function (lang) {
                            if (registeredLang.indexOf(lang) !== -1) {
                                let index = langList.indexOf(lang);
                                langList.slice(index, 1);
                            }
                        });
                    }
                    langList = this.removeDuplicatedLang(langList, registeredLang);

                    // Load data for edit UI
                    let selectedLang;
                    let defaultLang;
                    if ($.isEmptyObject(registeredLang)) {
                        selectedLang = langList[0];
                        defaultLang = langList[0];
                    } else {
                        selectedLang = registeredLang[0];
                        defaultLang = registeredLang[0];
                        this.props.initEditData(selectedLang);
                    }
                    this.displayOptions(langList, registeredLang, langName, true, selectedLang);
                    // this.props.getValueOfField('lang', langList[0]);
                    this.props.getValueOfField('lang', defaultLang);
                    this.setState({
                        languageList: langList,
                        registeredLanguage: registeredLang,
                        languageNameList: langName,
                        selectedLanguage: selectedLang,
                        defaultLanguage: defaultLang
                    });
                }
            });
    }

    componentDidMount() {
        this.initLanguageList();
    }
    componentWillReceiveProps(nextProps) {
        if (nextProps.type !== this.props.type) {
            this.initLanguageList();
            this.setState({
                registeredLanguage: []
            });
        }
    }

    displayOptions(languageList, registeredLanguage, languageNameList, isReset = false, selected = null) {
        let optionList = [];
        let state = this.state;
        if (registeredLanguage) {
            registeredLanguage.forEach(function (lang) {
                let innerHTML;
                if (lang === selected) {
                    innerHTML = <option key={lang} value={lang} style={{ fontWeight: 'bold' }} selected>{languageNameList[lang]}&nbsp;(Registered)</option>;
                }else {
                    innerHTML = <option key={lang} value={lang} style={{ fontWeight: 'bold' }}>{languageNameList[lang]}&nbsp;(Registered)</option>;
                }
                optionList.push(innerHTML);
            });
        }
        languageList.forEach(function (lang) {
            let innerHTML;
            if ($.isEmptyObject(registeredLanguage) && lang === state.defaultLanguage && isReset) {
                innerHTML = <option key={lang} value={lang} selected>{languageNameList[lang]}</option>;
            } else if (lang === selected) {
                innerHTML = <option key={lang} value={lang} selected>{languageNameList[lang]}</option>;
            } else {
                innerHTML = <option key={lang} value={lang}>{languageNameList[lang]}</option>;
            }
            optionList.push(innerHTML);
        });
        this.setState({
            options: optionList
        });
    }

    handleChange(event) {
        let language = event.target.value;
        this.props.getValueOfField('lang', language);  // Update what language is selected for other portions
        if (this.state.selectedLanguage === "0") {
            this.setState({
                selectedLanguage: language
            });
        } else {
            let dataChange = this.props.storeMultiLangSetting(this.state.selectedLanguage, language);
            if (dataChange) {
                let langList = this.state.languageList;
                let registeredLang = this.state.registeredLanguage;
                let index = langList.indexOf(this.state.selectedLanguage);
                if (index !== -1) {
                    langList.splice(index, 1);
                    registeredLang.push(this.state.selectedLanguage);
                }
                this.displayOptions(langList, registeredLang, this.state.languageNameList, false, language);

                this.setState({
                    languageList: langList,
                    registeredLanguage: registeredLang,
                    selectedLanguage: language
                });
            } else {
                let langList = this.state.languageList;
                let registeredLang = this.state.registeredLanguage;
                let index = registeredLang.indexOf(this.state.selectedLanguage);
                if (index !== -1) {
                    if (this.state.selectedLanguage === this.state.defaultLanguage) {
                        langList.unshift(this.state.selectedLanguage);
                        registeredLang.splice(index, 1);
                    } else {
                        langList.push(this.state.selectedLanguage);
                        registeredLang.splice(index, 1);
                    }
                }
                this.displayOptions(langList, registeredLang, this.state.languageNameList, false, language);
                this.setState({
                    selectedLanguage: language
                });
            }
        }
    }

    render() {
        return (
            <div className="form-group row">
                <label htmlFor="input_type" className="control-label col-xs-2 text-right">{this.props.name}{this.props.is_required ? <span className="style-red">*</span>:null}</label>
                <div className="controls col-xs-6">
                    <select onChange={this.handleChange} className="form-control" id="language">
                        {this.state.options}
                    </select>
                </div>
            </div>
        );
    }
}

class MainLayout extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            repository: this.props.data_load.repository_id,
            widget_type: this.props.data_load.widget_type,
            label: '',
            theme: this.props.data_load.theme,
            label_color: this.props.data_load.label_color,
            label_text_color: this.props.data_load.label_text_color,
            border_style: this.props.data_load.border_style,
            label_enable: this.props.data_load.label_enable,
            frame_border_color: this.props.data_load.frame_border_color,
            background_color: this.props.data_load.background_color,
            enable: this.props.data_load.is_enabled,
            settings: this.props.data_load.settings,
            language: this.props.data_load.language,
            multiLangSetting: this.props.data_load.multiLangSetting,
            multiLanguageChange: false,
            accessInitValue: 0
        };
        this.getValueOfField = this.getValueOfField.bind(this);
        this.storeMultiLangSetting = this.storeMultiLangSetting.bind(this);
        this.initEditData = this.initEditData.bind(this);
        this.accessCounterValidation = this.accessCounterValidation.bind(this);
    }

    getValueOfField(key, value) {
        switch (key) {
            case 'repository':
                this.setState({ repository: value });
                break;
            case 'type':
                let labelEnable = true;
                let theme = DEFAULT_THEME;
                if (value === HEADER_TYPE || value === FOOTER_TYPE) {
                    labelEnable = false;
                    theme = "simple";
                }
                this.setState({
                    label_enable: labelEnable,
                    theme: theme,
                    widget_type: value,
                    multiLangSetting: {},
                    label: '',
                    settings: {}
                });
                break;
            case 'label':
                this.setState({ label: value });
                break;
            case 'label_color':
                this.setState({ label_color: value });
                break;
            case 'label_text_color':
                this.setState({ label_text_color: value });
                    break;
            case 'label_enable':
                this.setState({ label_enable: value });
                break;
            case 'frame_border_color':
                this.setState({ frame_border_color: value });
                break;
            case 'background_color':
                this.setState({ background_color: value });
                break;
            case 'enable':
                this.setState({ enable: value });
                break;
            case 'settings':
                this.setState({ settings: value });
                break;
            case 'language':
                this.setState({ multiLanguageChange: value });
                break;
            case 'lang':
                this.setState({ language: value });
                break;
            case 'multiLangData':
                this.setState({ multiLangSetting: value });
                break;
            case "theme":
                this.setState({theme: value});
                break;
            case "border_style":
                this.setState({border_style: value});
                break;
            case 'accessInitValue':
                this.setState({ accessInitValue: value });
                break;
        }
    }

    initEditData(selectedLang) {
        if (!selectedLang) {
            return;
        }
        let multiLangData = this.state.multiLangSetting[selectedLang];
        let accessInitValue = 0;
        if ((this.state.widget_type+ "") === ACCESS_COUNTER && multiLangData.description) {
            accessInitValue = multiLangData.description.access_counter
        }
        if (multiLangData) {
            if([FREE_DESCRIPTION_TYPE, NOTICE_TYPE, ACCESS_COUNTER, HEADER_TYPE, FOOTER_TYPE].includes(this.state.widget_type)){
                this.setState({
                    multiLanguageChange: true,
                    label: multiLangData['label'],
                    settings: multiLangData['description'],
                    accessInitValue: accessInitValue
                });
            }
            else{
                this.setState({
                    multiLanguageChange: true,
                    label: multiLangData['label'],
                });
            }

        }
    }

    storeMultiLangSetting(lang, newLanguage) {
        let result = true;
        if (this.state.label === '' && $.isEmptyObject(this.state.settings)) {
            result = false;
        } else {
            if (!this.state.label) {
                let noData = true;
                for (let data in this.state.settings) {
                    if (this.state.settings[data]) {
                        noData = false;
                    }
                }
                result = !noData;
            }
        }

        let setting = {
            label: this.state.label,
        };

        if([FREE_DESCRIPTION_TYPE, NOTICE_TYPE, ACCESS_COUNTER, HEADER_TYPE, FOOTER_TYPE].includes(this.state.widget_type)){
            setting["description"] = this.state.settings;
        }
        let accessInitValue = this.state.accessInitValue;
        if ((this.state.widget_type+ "") === ACCESS_COUNTER) {
            if (setting.description.access_counter) {
                accessInitValue = setting.description.access_counter;
            }else {
                setting.description.access_counter = accessInitValue;
            }
        }
        if ((this.state.widget_type+ "") === ACCESS_COUNTER && this.accessCounterValidation(setting)) {
            delete setting.description["access_counter"];
            result = false;
        }
        let storage = this.state.multiLangSetting;
        if (setting.label || !$.isEmptyObject(setting.description)) {
            storage[lang] = setting;
        } else {
            if (storage[lang]) {
                delete storage[lang];
            }
        }
        let currentLabel = '';
        let currentSetting = {};
        if (this.state.multiLangSetting[newLanguage]) {
            currentLabel = this.state.multiLangSetting[newLanguage]['label'];
            currentSetting = this.state.multiLangSetting[newLanguage]['description'];

        }
        if ([FREE_DESCRIPTION_TYPE, NOTICE_TYPE, ACCESS_COUNTER, HEADER_TYPE, FOOTER_TYPE].includes(this.state.widget_type)) {
            this.setState({
                label: currentLabel,
                settings: currentSetting,
                multiLanguageChange: true,
                language: newLanguage,
                accessInitValue: accessInitValue
            });
        } else {
            this.setState({
                label: currentLabel,
                multiLanguageChange: true,
                language: newLanguage,
                accessInitValue: accessInitValue
            });
        }
        this.setState({
            multiLangSetting: storage
        });
        if ([NEW_ARRIVALS, MENU_TYPE].includes(this.state.widget_type)) {
          result = this.state.label !== '';
        }
        return result;
    }

    accessCounterValidation(setting) {
        if (setting.label !== "" ) {
            return false;
        }
        if (setting.description.preceding_message) {
            return false;
        }
        if (setting.description.following_message) {
            return false;
        }
        if (setting.description.other_message) {
            return false;
        }
        return true;
    }

    render() {
        return (
            <div>
                <br />
                <div className="row">
                    <ComponentSelectField getValueOfField={this.getValueOfField} name="Repository" url_request="/api/admin/load_repository" key_binding="repository" data_load={this.state.repository || '0'}  is_required = {true}/>
                </div>
                <div className="row">
                    <ComponentSelectField getValueOfField={this.getValueOfField} name="Type" url_request="/api/admin/load_widget_type" key_binding="type" data_load={this.state.widget_type} is_required = {true}/>
                </div>
                <div className="row">
                    <ComponentLanguage getValueOfField={this.getValueOfField} key_binding="language" name="Language" is_edit={this.props.is_edit} initEditData={this.initEditData}
                        storeMultiLangSetting={this.storeMultiLangSetting} data_load={this.state.multiLangSetting} type={this.state.widget_type} loaded_data={this.props.data_load.multiLangSetting} is_required = {true}/>
                </div>
                <div className="row">
                    <ComponentTextboxField getValueOfField={this.getValueOfField} name="Name" key_binding="label" data_load={this.state.label} data_change={this.state.multiLanguageChange} type={this.state.widget_type} is_required = {true}/>
                </div>
                {this.state.widget_type !== HEADER_TYPE && this.state.widget_type !== FOOTER_TYPE ?
                <div className="row">
                    <ComponentSelectField getValueOfField={this.getValueOfField} name="Theme" data = {THEME_SETTING} key_binding="theme" data_load={this.state.theme} is_required = {false}/>
                </div> : null}
                {this.state.widget_type !== HEADER_TYPE && this.state.widget_type !== FOOTER_TYPE ?
                <div className="row">
                    <ComponentCheckboxField name="Label Enable" getValueOfField={this.getValueOfField} key_binding="label_enable" data_load={this.state.label_enable} />
                </div> : null}
                {this.state.label_enable ?
                <div className="row">
                    <ComponentSelectColorFiled getValueOfField={this.getValueOfField} name="Label Color" key_binding="label_color" data_load={this.state.label_color} />
                </div> : null }
                {this.state.label_enable ?
                <div className="row">
                    <ComponentSelectColorFiled getValueOfField={this.getValueOfField} name="Label Text Color" key_binding="label_text_color" data_load={this.state.label_text_color} />
                </div> : null }
                {this.state.theme !== "simple" ?
                <div className="row">
                    <ComponentSelectField getValueOfField={this.getValueOfField} name="Border Style" data = {BORDER_STYLE_SETTING} key_binding="border_style" data_load={this.state.border_style} is_required = {false}/>
                </div> : null }
                {this.state.theme !== "simple" ?
                <div className="row">
                    <ComponentSelectColorFiled getValueOfField={this.getValueOfField} name="Border Color" key_binding="frame_border_color" data_load={this.state.frame_border_color} />
                </div> :null}
                <div className="row">
                    <ComponentSelectColorFiled getValueOfField={this.getValueOfField} name="Background Color" key_binding="background_color" data_load={this.state.background_color} type={this.state.widget_type} is_edit={this.props.is_edit} />
                </div>
                <div className="row">
                    <ComponentCheckboxField name="Enable" getValueOfField={this.getValueOfField} key_binding="enable" data_load={this.state.enable} />
                </div>
                <div className="row">
                    <ExtendComponent type={this.state.widget_type} is_edit={this.props.is_edit} repositoryId={this.state.repository}
                        getValueOfField={this.getValueOfField} key_binding="settings" data_load={this.state.settings}
                        language={this.state.language} data_change={this.state.multiLanguageChange}
                        init_value={this.state.accessInitValue}/>
                </div>
                <div className="row">
                    <ComponentButtonLayout data={this.state} getValueOfField={this.getValueOfField} url_request="/api/admin/save_widget_item" is_edit={this.props.is_edit} return_url={this.props.return_url} data_id={this.props.data_id} />
                </div>
            </div>
        )
    }
}

$(function () {
    let editData = $("#model_data").data("editdata");
    let isEdit = false;
    let data_id;
    if (editData) {
        isEdit = true;
        data_id = editData['widget_id'];
    }
    else {
        editData = {
            repository_id: '',
            widget_type: '',
            label: '',
            label_color: DEFAULT_LABEL_COLOR,
            label_text_color: DEFAULT_TEXT_COLOR,
            border_style: DEFAULT_BORDER_STYLE,
            theme: DEFAULT_THEME,
            label_enable: true,
            frame_border_color: DEFAULT_BORDER_COLOR,
            background_color: DEFAULT_BG_COLOR,
            is_enabled: true,
            language: '',
            multiLangSetting: {},
            settings:{},
        }
    }
    let returnURL = $("#return_url").val();
    ReactDOM.render(
        <MainLayout data_load={editData} is_edit={isEdit} return_url={returnURL} data_id={data_id} />,
        document.getElementById('root')
    )
});
