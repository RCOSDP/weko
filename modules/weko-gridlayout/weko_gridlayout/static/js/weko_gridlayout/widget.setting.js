class ComponentSelectField extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            repositoryId: '0',
            selectOptions: [],
        };
        this.handleChange = this.handleChange.bind(this);
    }

    componentDidMount() {
        fetch(this.props.url_request)
            .then(res => res.json())
            .then(
                (result) => {
                    let options = []
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
                    this.setState({
                        selectOptions: options,
                        repositoryId: this.props.data_load
                    });
                },

                (error) => {
                    console.log(error);
                }
            )

    }

    handleChange(event) {
        this.setState({ repositoryId: event.target.value });
        this.props.getValueOfField(this.props.key_binding, event.target.value);
        event.preventDefault();
    }

    render() {
        return (
            <div className="form-group row">
                <label htmlFor="input_type" className="control-label col-xs-2 text-right">{this.props.name}<span className="style-red">*</span></label>
                <div class="controls col-xs-6">
                    <select value={this.state.repositoryId} onChange={this.handleChange} className="form-control" name={this.props.name}>
                        <option value="0">Please select the&nbsp;{this.props.key_binding}</option>
                        {this.state.selectOptions}
                    </select>
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
        }
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
            })
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
                <label htmlFor="input_type" className="control-label col-xs-2 text-right">{this.props.name}<span className="style-red">*</span></label>
                <div class="controls col-xs-6">
                    <input name={this.props.name} type="text" name="name" value={this.state.value} onChange={this.handleChange} className="form-control" />
                </div>
            </div>
        )
    }
}

class ComponentSelectColorFiled extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            color: '#4169E1',
        };
        this.handleChange = this.handleChange.bind(this);
    }

    componentDidMount() {
        this.setState({
            color: this.props.data_load
        })
    }

    handleChange(event) {
        this.setState({ color: event.target.value });
        this.props.getValueOfField(this.props.key_binding, event.target.value);
        event.preventDefault();
    }

    render() {
        return (
            <div className="form-group row">
                <label htmlFor="input_type" className="control-label col-xs-2 text-right">{this.props.name}</label>
                <div className="controls col-xs-2">
                    <input name={this.props.name} type="color" className="style-select-color" name="favcolor" value={this.state.color} onChange={this.handleChange} />
                </div>
            </div>
        )
    }
}

class ComponentCheckboxField extends React.Component {
    constructor(props) {
        super(props);
        this.handleChange = this.handleChange.bind(this);
        this.state = {
            is_default_Checked: this.props.data_load || false,
        }
    }

    handleChange(event) {
        this.props.getValueOfField(this.props.key_binding, event.target.checked);
    }

    render() {
        return (
            <div className="form-group row">
                <label htmlFor="input_type" className="control-label col-xs-2 text-right">{this.props.name}</label>
                <div class="controls col-xs-1">
                    <input name={this.props.name} type="checkbox" onChange={this.handleChange} defaultChecked={this.state.is_default_Checked} />
                </div>
            </div>
        )
    }
}

class ComponentFieldContainSelectMultiple extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            selectOptions: [],
            UnauthorizedOptions: [],
            unauthorList: []
        };
        this.handleChange = this.handleChange.bind(this);
        this.handleMoveRightClick = this.handleMoveRightClick.bind(this);
        this.handleMoveLeftClick = this.handleMoveLeftClick.bind(this);
        this.onSelect = this.onSelect.bind(this);
    }
    componentDidMount() {
        fetch(this.props.url_request)
            .then(res => res.json())
            .then(
                (result) => {
                    let unOptions = [];
                    let options = result.map((option) => {
                        if (this.props.is_edit == true) {
                            let role_array = this.props.data_load.split(',');
                            if (role_array.includes(option.id.toString())) {
                                return (
                                    <option key={option.id} value={option.id}>{option.name}</option>
                                )
                            }
                            else {
                                let innerhtml = <option key={option.id} value={option.id}>{option.name}</option>;
                                unOptions.push(innerhtml);
                            }
                        }
                        else {
                            return (
                                <option key={option.id} value={option.id}>{option.name}</option>
                            )
                        }
                    });
                    this.setState({
                        selectOptions: options,
                        UnauthorizedOptions: unOptions
                    });
                },

                (error) => {
                    console.log(error);
                }
            )

    }

    handleChange(event) {
        this.setState({ repositoryId: event.target.value });
        event.preventDefault();
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

    isValueExist(item, array) {
        if (array == undefined) {
            return true;
        }
        if (array.length != 0) {
            for (let prop in array) {
                if (array[prop].props.value == item) {
                    return true;
                } else {
                    return false;
                }
            }
        } else {
            return false;
        }
        return true;
    }

    handleMoveRightClick(event) {
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
            unauthorList: []
        });
        let data = [];
        for (let option in nonSelectOptions) {
            data.push(nonSelectOptions[option].props.value);
        }
        this.props.getValueOfField(this.props.key_binding, data);
    }

    handleMoveLeftClick(event) {
        let selectedIndex = this.state.unauthorList;
        let options = document.getElementById(this.props.unauthorSelect).options;
        let authorizedOptions = this.getListOption(this.props.authorSelect);
        let remainOption = [];
        for (let option in options) {
            let registed = false;
            for (let index in selectedIndex) {
                if (options[option].value == selectedIndex[index] && options[option].value) {
                    let innerhtml = <option key={options[option].value} value={options[option].value}>{options[option].text}</option>;
                    if (!this.isValueExist(options[option].value, authorizedOptions)) {
                        authorizedOptions.push(innerhtml);
                    }
                    registed = true;
                    break;
                }
            }
            if (!registed) {
                let innerhtml = <option key={options[option].value} value={options[option].value}>{options[option].text}</option>;
                if (options[option].value) {
                    remainOption.push(innerhtml);
                }
            }
        }
        this.setState({
            selectOptions: authorizedOptions,
            UnauthorizedOptions: remainOption
        });
        let data = [];
        for (let option in authorizedOptions) {
            data.push(authorizedOptions[option].props.value);
        }
        this.props.getValueOfField(this.props.key_binding, data);
    }

    onSelect(event) {
        var options = event.target.options;
        var value = [];
        for (var i = 0, l = options.length; i < l; i++) {
            if (options[i].selected) {
                value.push(options[i].value);
            }
        }
        this.setState({
            unauthorList: value
        });
    }

    render() {
        return (
            <div className="form-group row">
                <label htmlFor="input_type" className="control-label col-xs-2 text-right">{this.props.name}</label>
                <div class="controls col-xs-9">
                    <fieldset className="form-group style-container" >
                        <span>Role</span><br />
                        <div className="col-xs-5 style-element" >
                            <span >Authorized</span><br />
                            <select name={this.props.name} multiple className="style-select-left" id={this.props.authorSelect} name={this.props.authorSelect}>
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
                        <div className="col-xs-5 style-element style-element-right">
                            <span>Unauthorized</span><br />
                            <select multiple value={this.state.unauthorList} className="style-select-right" onChange={this.onSelect} id={this.props.unauthorSelect} name={this.props.unauthorSelect}>
                                {this.state.UnauthorizedOptions}
                            </select>
                        </div>
                    </fieldset>
                </div>
            </div>
        )
    }
}

class ComponentFieldEditor extends React.Component {
    constructor(props) {
        super(props)
        this.quillRef = null;
        this.reactQuillRef = null;
        this.state = {
            editorHtml: this.props.data_load,
            modules: {
                toolbar: [
                    [{ 'font': [] }, { size: [] }],
                    ['bold', 'italic', 'underline', 'strike'],
                    [{ 'color': ["#000000", "#e60000", "#ff9900", "#ffff00", "#008a00", "#0066cc", "#9933ff", "#ffffff", "#facccc", "#ffebcc", "#ffffcc", "#cce8cc", "#cce0f5", "#ebd6ff", "#bbbbbb", "#f06666", "#ffc266", "#ffff66", "#66b966", "#66a3e0", "#c285ff", "#888888", "#a10000", "#b26b00", "#b2b200", "#006100", "#0047b2", "#6b24b2", "#444444", "#5c0000", "#663d00", "#666600", "#003700", "#002966", "#3d1466", 'custom-color'] }, { 'background': ["#000000", "#e60000", "#ff9900", "#ffff00", "#008a00", "#0066cc", "#9933ff", "#ffffff", "#facccc", "#ffebcc", "#ffffcc", "#cce8cc", "#cce0f5", "#ebd6ff", "#bbbbbb", "#f06666", "#ffc266", "#ffff66", "#66b966", "#66a3e0", "#c285ff", "#888888", "#a10000", "#b26b00", "#b2b200", "#006100", "#0047b2", "#6b24b2", "#444444", "#5c0000", "#663d00", "#666600", "#003700", "#002966", "#3d1466", 'custom-color'] }],
                    [{ 'script': 'sub' }, { 'script': 'super' }],
                    [{ 'header': '1' }, { 'header': '2' }, 'blockquote', 'code-block'],
                    [{ 'list': 'ordered' }, { 'list': 'bullet' },
                    { 'indent': '-1' }, { 'indent': '+1' }],
                    ['direction', 'align'],
                    ['link', 'image', 'video', 'formula'],
                    ['clean']
                ],
                clipboard: {
                    // toggle to add extra line breaks when pasting HTML:
                    matchVisual: false,
                }
            },
            formats: [
                'font', 'size',
                'bold', 'italic', 'underline', 'strike', 'color', 'background',
                'script', 'script', 'header', 'blockquote', 'code-block',
                'list', 'bullet', 'indent', 'direction', 'align',
                'link', 'image', 'video', 'formula', 'clean'
            ]
        };
        this.handleChange = this.handleChange.bind(this)
        this.attachQuillRefs = this.attachQuillRefs.bind(this);
    }
    componentDidMount() {
        this.attachQuillRefs();
    }

    componentDidUpdate() {
        this.attachQuillRefs();
    }

    attachQuillRefs() {
        // Ensure React-Quill reference is available:
        if (typeof this.reactQuillRef.getEditor !== 'function') {
            return false;
        }
        // Skip if Quill reference is defined:
        if (this.quillRef != null) {
            return false;
        }

        const quillRef = this.reactQuillRef.getEditor();
        if (quillRef != null) this.quillRef = quillRef;
    }
    componentWillReceiveProps(props) {
        if (props.data_change) {
            let setting = undefined;
            setting = props.data_load;
            this.setState({
                editorHtml: setting
            })
            this.props.getValueOfField("language", false);
        }
    }

    handleChange(html) {
        if (this.quillRef == null) {
            return false;
        }
        let length = this.quillRef.getText().trim().length;
        if (length == 0) {
            html = '';
        }
        this.setState({ editorHtml: html });
        this.props.handleChange(this.props.key_binding, html);
    }

    render() {
        return (
            <div className="form-group row">
                <label htmlFor="input_type" className="control-label col-xs-2 text-right">{this.props.name}</label>
                <div class="controls col-xs-9 my-editor">
                    <ReactQuill
                        ref={(el) => { this.reactQuillRef = el }}
                        onChange={this.handleChange}
                        value={this.state.editorHtml || ''}
                        modules={this.state.modules}
                        formats={this.state.formats}
                        bounds={'.app'}
                    />
                </div>
            </div>
        )
    }
}

class ExtendComponent extends React.Component {
    constructor(props) {
        super(props);
        if (this.props.type == "Notice") {
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
    }
    static getDerivedStateFromProps(nextProps, prevState) {
        if (nextProps.type !== prevState.type) {
            return {
                type: nextProps.type,
                settings: {},
                write_more: false
            };
        }
        if (nextProps.data_change) {
            let setting = {};
            setting = nextProps.data_load;
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
            return {
                settings: setting
            }
        }
        return null;
    }

    handleChange(field, value) {
        let data = this.state.settings;
        switch (field) {
            case "description":
                data["description"] = value;
                break;
            case "read_more":
                data["read_more"] = value;
                break;
            case "more_description":
                data["more_description"] = value;
                break;
            case "hide_the_rest":
                data["hide_the_rest"] = value;
                break;
        }
        this.setState({
            settings: data
        })
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
        })
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

    render() {
        if (this.state.type == "Free description") {
            return (
                <div>
                    <ComponentFieldEditor handleChange={this.handleChange} name="Free description" key_binding="description" data_load={this.state.settings.description} data_change={this.props.data_change} getValueOfField={this.props.getValueOfField} />
                </div>
            )
        }
        else if (this.state.type == "Notice") {
            if (this.state.write_more == false) {
                return (
                    <div>
                        <div>
                            <ComponentFieldEditor handleChange={this.handleChange} name="Notice description" key_binding="description" data_load={this.state.settings.description} data_change={this.props.data_change} getValueOfField={this.props.getValueOfField} />
                        </div>
                        <div className="row">
                            <label className="control-label col-xs-2 text-right"></label>
                            <div class="controls col-xs-10">
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
                            <ComponentFieldEditor handleChange={this.handleChange} name="Notice description" key_binding="description" data_load={this.state.settings.description} data_change={this.props.data_change} getValueOfField={this.props.getValueOfField} />
                        </div>
                        <div className="row">
                            <label className="control-label col-xs-2 text-right"></label>
                            <div class="controls col-xs-10">
                                <div>
                                    <input name="write_more" type="checkbox" onChange={this.handleChangeCheckBox} defaultChecked={this.state.write_more} />
                                    <span>&nbsp;Write more</span>
                                </div>
                                <br />
                                <div className="sub-text-box">
                                    <input type="text"  id="read_more" name="read_more" onChange={this.handleChangeReadMore} className="form-control" placeholder="Read more" value={this.state.settings.read_more} data_change={this.props.data_change} getValueOfField={this.props.getValueOfField} />
                                </div>
                                <br />
                            </div>
                        </div>
                        <div>
                            <ComponentFieldEditor handleChange={this.handleChange} name="" key_binding="more_description" data_load={this.state.settings.more_description} data_change={this.props.data_change} getValueOfField={this.props.getValueOfField} />
                        </div>
                        <div className="row">
                            <label className="control-label col-xs-2 text-right"></label>
                            <div class="controls col-xs-10">
                                <div className="sub-text-box">
                                    <input type="text" id="hide_the_rest" name="hide_the_rest" onChange={this.handleChangeHideTheRest} className="form-control" placeholder="Hide the rest" value={this.state.settings.hide_the_rest} data_change={this.props.data_change} getValueOfField={this.props.getValueOfField} />
                                </div>
                                <br />
                            </div>
                        </div>
                    </div>
                )
            }
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
        this.state = {
            repository: '',
            widget_type: '',
            label: ''
        }
        this.saveCommand = this.saveCommand.bind(this);
        this.deleteCommand = this.deleteCommand.bind(this);
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
        let currentLanguage = data['language'];

        if (currentLabel || !$.isEmptyObject(currentDescription)) {
            let currentLangData = {
                label: currentLabel,
                description: currentDescription
            }
            if($.isEmptyObject(multiLangData)) {
                currentLangData['isDefault'] = true;
            }else {
                currentLangData['isDefault'] = false;
            }
            multiLangData[currentLanguage] = currentLangData;
        }
        data['multiLangSetting'] = multiLangData;

        for (let object in multiLangData) {
            let langData = multiLangData[object];
            if (langData['isDefault']) {
                currentLabel = langData['label'];
                currentDescription = langData['description'];
                currentLanguage = object;
                break;
            }
        }
        data['label'] = currentLabel;
        data['settings'] = currentDescription;
        data['language'] = currentLanguage;

        let request = {
            flag_edit: this.props.is_edit,
            data: data,
            data_id: '',
        };
        if (this.state.repository == '' && this.state.widget_type == '' && this.state.label == '')
            request.data_id = this.props.data_id;
        else
            request.data_id = this.state;

        if (this.props.data.repository == "0" || this.props.data.repository == "") {
            var modalcontent = "Repository is required!";
            $("#inputModal").html(modalcontent);
            $("#allModal").modal("show");
        } else if (this.props.data.widget_type == "0" || this.props.data.widget_type == "") {
            var modalcontent = "Type is required.";
            $("#inputModal").html(modalcontent);
            $("#allModal").modal("show");
        } else if (this.props.data.label === null || this.props.data.label.match(/^ *$/) !== null) {
            var modalcontent = "Label is required!";
            $("#inputModal").html(modalcontent);
            $("#allModal").modal("show");
        } else {
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
                        this.setState({
                            repository: this.props.data.repository,
                            widget_type: this.props.data.widget_type,
                            label: this.props.data.label
                        })
                    } else {
                        //alert(result.message);
                        var modalcontent = result.message;
                        $("#inputModal").html(modalcontent);
                        $("#allModal").modal("show");
                    }
                });
        }
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
        }
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
                        var modalcontent = result.message;
                        $("#inputModal").html(modalcontent);
                        $("#allModal").modal("show");
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
                            <span className="glyphicon glyphicon-download-alt" aria-hidden="true"></span>
                            &nbsp;Save
                        </button>
                        <a href={this.props.return_url} className="form-group btn btn-info cancel-button style-my-button">
                            <span className="glyphicon glyphicon-remove" aria-hidden="true"></span>
                            &nbsp;Cancel
                        </a>
                        <button className="btn btn-danger delete-button style-my-button" onClick={this.deleteCommand}>
                            <span class="glyphicon glyphicon-trash" aria-hidden="true"></span>
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
                            <span className="glyphicon glyphicon-download-alt" aria-hidden="true"></span>
                            &nbsp;Save
                        </button>
                        <a href={this.props.return_url} className="form-group btn btn-info cancel-button style-my-button">
                            <span className="glyphicon glyphicon-remove" aria-hidden="true"></span>
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
        }
        this.initLanguageList = this.initLanguageList.bind(this);
        this.handleChange = this.handleChange.bind(this);
        this.displayOptions = this.displayOptions.bind(this);
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
                            }
                            systemRegisteredLang.push(newLang);
                        } else {
                            langList.push(lang.lang_code);
                        }
                        langName[lang.lang_code] = lang.lang_name;
                    });
                    for (let i = systemRegisteredLang.length; i > 0; i--) {
                        for (let j = 0; j < systemRegisteredLang.length; j++) {
                            if (systemRegisteredLang[j].sequence == i) {
                                langList.unshift(systemRegisteredLang[j].code);
                            }
                        }
                    }
                    if (!$.isEmptyObject(this.props.data_load)) {
                        registeredLang = Object.keys(this.props.data_load);
                        langList.forEach(function (lang) {
                            if (registeredLang.indexOf(lang) != -1) {
                                let index = langList.indexOf(lang);
                                langList.slice(index, 1);
                            }
                        });
                    }
                    this.displayOptions(langList, registeredLang, langName);
                    this.props.getValueOfField('lang', langList[0]);
                    this.setState({
                        languageList: langList,
                        registeredLanguage: registeredLang,
                        languageNameList: langName,
                        selectedLanguage: langList[0],
                        defaultLanguage: langList[0]
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
        }
    }

    displayOptions(languageList, registeredLanguage, languageNameList) {
        let optionList = [];
        if (registeredLanguage) {
            registeredLanguage.forEach(function (lang) {
                let innerHTML = <option value={lang} style={{ fontWeight: 'bold' }}>{languageNameList[lang]}&nbsp;(Registered)</option>;
                optionList.push(innerHTML);
            });
        }
        languageList.forEach(function (lang) {
            let innerHTML;
            if (!registeredLanguage && lang == defaultLanguage) {
                innerHTML = <option value={lang} selected>{languageNameList[lang]}</option>;
            } else {
                innerHTML = <option value={lang}>{languageNameList[lang]}</option>;
            }
            optionList.push(innerHTML);
        });
        this.setState({
            options: optionList
        });
    }

    handleChange(event) {

        var language = document.getElementById("language").value;
        if (this.state.selectedLanguage == "0") {
            this.setState({
                selectedLanguage: language
            });
        } else {
            let dataChange = this.props.storeMultiLangSetting(this.state.selectedLanguage, language);
            if (dataChange) {
                let langList = this.state.languageList;
                let registeredLang = this.state.registeredLanguage;
                let index = langList.indexOf(this.state.selectedLanguage);
                if (index != -1) {
                    langList.splice(index, 1);
                    registeredLang.push(this.state.selectedLanguage);
                }
                this.displayOptions(langList, registeredLang, this.state.languageNameList);
                this.setState({
                    languageList: langList,
                    registeredLanguage: registeredLang,
                    selectedLanguage: language
                });
            } else {
                let langList = this.state.languageList;
                let registeredLang = this.state.registeredLanguage;
                let index = registeredLang.indexOf(this.state.selectedLanguage);
                if (index != -1) {
                    if (this.state.selectedLanguage == this.state.defaultLanguage) {
                        langList.unshift(this.state.selectedLanguage);
                        registeredLang.splice(index, 1);
                    } else {
                        langList.push(this.state.selectedLanguage);
                        registeredLang.splice(index, 1);
                    }
                }
                this.displayOptions(langList, registeredLang, this.state.languageNameList);
                this.setState({
                    selectedLanguage: language
                });
            }
        }
    }

    render() {
        return (
            <div className="form-group row">
                <label htmlFor="input_type" className="control-label col-xs-2 text-right">{this.props.name}<span className="style-red">*</span></label>
                <div class="controls col-xs-6">
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
            label: this.props.data_load.label,
            label_color: this.props.data_load.label_color,
            frame_border: this.props.data_load.has_frame_border,
            frame_border_color: this.props.data_load.frame_border_color,
            text_color: this.props.data_load.text_color,
            background_color: this.props.data_load.background_color,
            browsing_role: this.props.data_load.browsing_role,
            edit_role: this.props.data_load.edit_role,
            enable: this.props.data_load.is_enabled,
            settings: {},
            language: this.props.data_load.language,
            multiLangSetting: this.props.data_load.multiLangSetting,
            multiLanguageChange: false,
        };
        this.getValueOfField = this.getValueOfField.bind(this);
        this.storeMultiLangSetting = this.storeMultiLangSetting.bind(this);
    }
    componentDidMount() {
        // For edit option - Convert data
        let registeredLang = [];
        let description = {};
        if (!$.isEmptyObject(this.state.multiLangSetting)) {
            for (let object in this.state.multiLangSetting) {
                registeredLang.push(object);
                if (this.state.multiLangSetting[object]['isDefault']) {
                    description = this.state.multiLangSetting[object]['description'];
                }
            }
        }
        this.setState({
            settings: description,
            multiLanguageChange: true
        })
    }
    getValueOfField(key, value) {
        switch (key) {
            case 'repository':
                this.setState({ repository: value });
                break;
            case 'type':
                this.setState({
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
            case 'frame_border':
                this.setState({ frame_border: value });
                break;
            case 'frame_border_color':
                this.setState({ frame_border_color: value });
                break;
            case 'text_color':
                this.setState({ text_color: value });
                break;
            case 'background_color':
                this.setState({ background_color: value });
                break;
            case 'browsing_role':
                this.setState({ browsing_role: value });
                break;
            case 'edit_role':
                this.setState({ edit_role: value });
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
                this.setState({
                    language: value
                })
        }
    }
    storeMultiLangSetting(lang, newLanguage) {
        var result = true;
        if (this.state.label == '' && $.isEmptyObject(this.state.settings)) {
            result = false;
        }
        let setting = {
            label: this.state.label,
            description: this.state.settings
        };

        let storage = this.state.multiLangSetting;
        if ($.isEmptyObject(storage)) {
            setting['isDefault'] = true;
        } else {
            setting['isDefault'] = false;
        }
        storage[lang] = setting;
        if (this.state.multiLangSetting[newLanguage]) {
            let currentLabel = this.state.multiLangSetting[newLanguage]['label'];
            let currentSetting = this.state.multiLangSetting[newLanguage]['description'];
            this.setState({
                label: currentLabel,
                settings: currentSetting,
                multiLanguageChange: true,
                language: newLanguage
            });
        } else {
            this.setState({
                label: '',
                settings: {},
                multiLanguageChange: true,
                language: newLanguage
            });
        }
        this.setState({
            multiLangSetting: storage
        });
        return result;
    }

    render() {
        return (
            <div>
                <br />
                <div className="row">
                    <ComponentSelectField getValueOfField={this.getValueOfField} name="Repository" url_request="/api/admin/load_repository" key_binding="repository" data_load={this.state.repository} />
                </div>
                <div className="row">
                    <ComponentSelectField getValueOfField={this.getValueOfField} name="Type" url_request="/api/admin/load_widget_type" key_binding="type" data_load={this.state.widget_type} />
                </div>
                <div className="row">
                    <ComponentLanguage getValueOfField={this.getValueOfField} key_binding="language" name="Language" storeMultiLangSetting={this.storeMultiLangSetting} data_load={this.state.multiLangSetting} type={this.state.widget_type} />
                </div>
                <div className="row">
                    <ComponentTextboxField getValueOfField={this.getValueOfField} name="Label" key_binding="label" data_load={this.state.label} data_change={this.state.multiLanguageChange} type={this.state.widget_type} />
                </div>
                <div className="row">
                    <ComponentSelectColorFiled getValueOfField={this.getValueOfField} name="Label Color" key_binding="label_color" data_load={this.state.label_color} />
                </div>
                <div className="row">
                    <ComponentCheckboxField name="Frame Border" getValueOfField={this.getValueOfField} key_binding="frame_border" data_load={this.state.frame_border} />
                </div>
                <div className="row">
                    <ComponentSelectColorFiled getValueOfField={this.getValueOfField} name="Frame Border Color" key_binding="frame_border_color" data_load={this.state.frame_border_color} />
                </div>
                <div className="row">
                    <ComponentSelectColorFiled getValueOfField={this.getValueOfField} name="Text Color" key_binding="text_color" data_load={this.state.text_color} />
                </div>
                <div className="row">
                    <ComponentSelectColorFiled getValueOfField={this.getValueOfField} name="Background Color" key_binding="background_color" data_load={this.state.background_color} />
                </div>
                <div className="row">
                    <ComponentFieldContainSelectMultiple getValueOfField={this.getValueOfField} name="Browsing Privilege" authorSelect="browseAuthorSelect" unauthorSelect="browseUnauthorSelect" url_request="/api/admin/get_account_role" key_binding="browsing_role" data_load={this.state.browsing_role} is_edit={this.props.is_edit} />
                </div>
                <div className="row">
                    <ComponentFieldContainSelectMultiple getValueOfField={this.getValueOfField} name="Edit Privilege" authorSelect="editAuthorSelect" unauthorSelect="editUnauthorSelect" url_request="/api/admin/get_account_role" key_binding="edit_role" data_load={this.state.edit_role} is_edit={this.props.is_edit} />
                </div>
                <div className="row">
                    <ComponentCheckboxField name="Enable" getValueOfField={this.getValueOfField} key_binding="enable" data_load={this.state.enable} />
                </div>
                <div className="row">
                    <ExtendComponent type={this.state.widget_type} getValueOfField={this.getValueOfField} key_binding="settings" data_load={this.state.settings} data_change={this.state.multiLanguageChange} />
                </div>
                <div className="row">
                    <ComponentButtonLayout data={this.state} url_request="/api/admin/save_widget_item" is_edit={this.props.is_edit} return_url={this.props.return_url} data_id={this.props.data_id} />
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
        data_id = {
            repository: editData.repository_id,
            widget_type: editData.widget_type,
            label: editData.label
        }
    }
    else {
        editData = {
            repository_id: '',
            widget_type: '',
            label: '',
            label_color: '#4169E1',
            has_frame_border: true,
            frame_border_color: '#4169E1',
            text_color: '#4169E1',
            background_color: '#4169E1',
            browsing_role: [1, 2, 3, 4, 99],
            edit_role: [1, 2, 3, 4, 99],
            is_enabled: true,
            language: '',
            multiLangSetting: {}
        }
    }
    let returnURL = $("#return_url").val();
    ReactDOM.render(
        <MainLayout data_load={editData} is_edit={isEdit} return_url={returnURL} data_id={data_id} />,
        document.getElementById('root')
    )
});
