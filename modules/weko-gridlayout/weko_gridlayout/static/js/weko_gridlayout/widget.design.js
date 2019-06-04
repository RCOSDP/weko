const MAIN_CONTENT_TYPE = "Main contents";
const MAIN_CONTENT_BUTTON_ID = "main_content_id";
let isHasMainContent = false;

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
        fetch("/api/admin/load_repository")
            .then(res => res.json())
            .then(
                (result) => {
                    if (result.error) {
                        alter(result.error);
                        return;
                    }
                    let options = result.repositories.map((option) => {
                        return (
                            <option key={option.id} value={option.id}>{option.id}</option>
                        )
                    });
                    this.setState({
                        selectOptions: options
                    });
                },

                (error) => {
                    console.log(error);
                }
            );

    }

    handleChange(event) {
        let repositoryId = event.target.value;
        let url = "/api/admin/load_widget_list_design_setting/" + repositoryId;
        fetch(url)
            .then(res => res.json())
            .then(
                (result) => {
                    if (result.error) {
                        console.log(result.error);
                        return;
                    }
                    let widgetPreview = result['widget-preview'];
                    let widgetList = result['widget-list'];
                    let data = widgetPreview['data'];
                    loadWidgetPreview(data);
                    data = widgetList['data'];
                    loadWidgetList(data);
                },
                (error) => {
                    console.log(error);
                }
            );

        disableButton();

        this.setState({ repositoryId: repositoryId });
        this.props.callbackMainLayout(repositoryId);
        event.preventDefault();
    }

    render() {
        return (
            <div className="form-group row">
              <div id="alerts"></div>  
              <label htmlFor="input_type" className="control-label col-xs-1">Repository<span style={this.styleRed}>*</span></label>
                <div class="controls col-xs-5">
                    <select id="repository-id" value={this.state.repositoryId} onChange={this.handleChange} className="form-control">
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
 * Preview widget panel layout.
 */
class PreviewWidget extends React.Component {
    constructor(props) {
        super(props);
        this.style = {
            "border": "1px solid #eee",
            "min-height": "300px",
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
        PreviewGrid.saveGrid();
    }

    handleCancel() {
        let url = "/api/admin/load_widget_design_setting/" + this.props.repositoryId;
        fetch(url)
            .then(res => res.json())
            .then(
                (result) => {
                    if (result.error) {
                        console.log(result.error);
                        return;
                    }
                    let widgetList = result['widget-settings'];
                    loadWidgetPreview(widgetList);
                },
                (error) => {
                    console.log(error);
                }
            );
    }

    render() {
        return (
            <div className="form-group col-xs-10">
                <button id="save-grid" className="btn btn-primary save-button" style={this.style} onClick={this.handleSave}>
                    <span className="glyphicon glyphicon-download-alt" aria-hidden="true"></span>
                    &nbsp;Save
                </button>
                <button id="clear-grid" className="form-group btn btn-info cancel-button" onClick={this.handleCancel} >
                    <span className="glyphicon glyphicon-remove"  aria-hidden="true"></span>
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
            repositoryId: ""
        };
        this.props.repositoryId = "";
    }

    callbackMainLayout(repositoryId) {
        this.setState({ repositoryId: repositoryId });
    }

    render() {
        return (
            <div>
                <div className="row">
                    <Repository callbackMainLayout={this.callbackMainLayout.bind(this)} />
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
                    <ButtonLayout repositoryId={this.state.repositoryId} />
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
        var options = {
            width: 12,
            float: true,
            removeTimeout: 100,
            acceptWidgets: '.grid-stack-item'
        };

        $('#gridPreview').gridstack(_.defaults(options));

        this.serializedData = [];

        this.grid = $('#gridPreview').data('gridstack');
    }

    this.loadGrid = function (widgetListItems) {
        this.grid.removeAll();
        var items = GridStackUI.Utils.sort(widgetListItems);
        isHasMainContent = false;
        _.each(items, function (node) {
            if(MAIN_CONTENT_TYPE == node.type){
                isHasMainContent = true;
                disableMainContentButton(true);
            }
            this.grid.addWidget($(this.widgetTemplate(node, false)),
                node.x, node.y, node.width, node.height);
        }, this);
        return false;
    }.bind(this);

    this.saveGrid = function () {
        this.serializedData = _.map($('.grid-stack > .grid-stack-item:visible'), function (el) {
            el = $(el);
            var node = el.data('_gridstack_node');
            let name = el.data("name");
            let id = el.data("id");
            let type = el.data("type");
            let widgetLanguage = el.data("language")
            let nameDisplay = el.data("name_display")
            if (!id) {
                return;
            } else if(MAIN_CONTENT_TYPE == type){
                isHasMainContent = true;
            }
            return {
                x: node.x,
                y: node.y,
                width: node.width,
                height: node.height,
                name: name,
                id: id,
                type: type,
                name_display: nameDisplay,
                widget_language: widgetLanguage,
            };
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

    this.widgetTemplate = function(node, isAutoPosition) {
        let autoPosition = "";
        if(isAutoPosition){
            autoPosition = 'data-gs-auto-position="true"';
        }
        let template = '<div data-type="' + node.type + '" data-name="' + node.name + '" data-id="' + node.id + '"'
        + '" data-language="' + node.widget_language + '"' + autoPosition + '>'
        + ' <div class="center-block text-right"><div class="glyphicon glyphicon-remove" style="z-index: 90;"></div></div>'
        + ' <div class="grid-stack-item-content">'
        + '     <span class="widget-label">&lt;' + node.type + '&gt;</span>'
        + '     <span class="widget-label">' + node.name_display + '</span>'
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
}

/**
 * Add widget from List panel to Preview panel.
 */
function addWidget() {
    $('.add-new-widget').each(function () {
        var $this = $(this);
        $this.on("click", function () {
            let widgetName = $(this).data('widgetName');
            let widgetId = $(this).data('widgetId');
            let widgetType = $(this).data('widgetType');
            let widgetNameDisplay = $(this).data('widgetNameDisplay');
            let widgetLanguage = $(this).data('widgetLanguage');
            if(MAIN_CONTENT_TYPE == widgetType && isHasMainContent){
                alert("Main Content has been existed in Preview panel.");
                disableMainContentButton(true);
                return false;
            }
            let node = {
                x: 0,
                y: 0,
                width: 2,
                height: 1,
                auto_position: true,
                name: widgetName,
                id: widgetId,
                type:widgetType,
                name_display: widgetNameDisplay,
                widget_language: widgetLanguage,
            };
            PreviewGrid.addNewWidget(node);
            if(MAIN_CONTENT_TYPE == widgetType){
                isHasMainContent = true;
                disableMainContentButton(true);
            }
            removeWidget();
        });
    });

}

/**
 * Load Widget list panel
 * @param {*} widgetListItems
 */
function loadWidgetList(widgetListItems) {
    var options = {
        width: 2,
        ddPlugin: false,
        cellHeight: 80,
        acceptWidgets: '.grid-stack-item'
    };
    $('#widgetList').gridstack(options);
    var widgetList = $('#widgetList').data('gridstack');
    widgetList.removeAll();
    let x = 0;
    let y = 0;
    _.each(widgetListItems, function (widget) {
        let buttonId = "";
        if(MAIN_CONTENT_TYPE ==  widget.widgetType) {
            buttonId = 'id="' + MAIN_CONTENT_BUTTON_ID + '"';
        }
        widgetList.addWidget($(
            '<div>'
            + '<div class="grid-stack-item-content">'
            + ' <span class="widget-label" >&lt;' + widget.widgetType + '&gt;</span>'
            + ' <span class="widget-label">' + widget.widgetLabelDisplay + '</span>'
            + ' <button ' + buttonId + ' data-widget-type="' + widget.widgetType
            + '" data-widget-name="' + widget.widgetLabel + '" data-widget-id="' + widget.widgetId
            + '" data-widget-name-display="' + widget.widgetLabelDisplay + '" data-widget-language="' + widget.widgetLanguage
            +  '" class="btn btn-default add-new-widget">'
            + ' Add Widget'
            + ' </button>'
            + '</div>'
            + '<div/>'),
            x, y, 2, 1);
        x++;
        y++;
    }, this);
    addWidget();
}

/**
 * Load Preview panel
 * @param {*} widgetListItems
 */
function loadWidgetPreview(widgetListItems) {
    PreviewGrid.init();
    PreviewGrid.loadGrid(widgetListItems);
    removeWidget();
}

/**
 * Remove widget on Preview panel
 */
function removeWidget() {
    $('.glyphicon-remove').on("click", function (e) {
        let widget = $(this).closest(".grid-stack-item");
        let widgetType = widget.data('type');
        PreviewGrid.deleteWidget(widget);
        if(MAIN_CONTENT_TYPE == widgetType){
            isHasMainContent = false;
            disableMainContentButton(false);
        }
        return false;
    });
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
 * @param {*} repositoryId
 */
function disableButton() {
    let repositoryId = $("#repository-id").val();
    if(!repositoryId) {
        repositoryId = "0";
    }
    if (repositoryId == "0") {
        $("#save-grid").attr('disabled','disabled');
        $("#clear-grid").attr('disabled','disabled');
    } else {
        $("#save-grid").removeAttr('disabled');
        $("#clear-grid").removeAttr('disabled');
    }
}

function disableMainContentButton(isDisable){
    if(isDisable){
        $("#" + MAIN_CONTENT_BUTTON_ID).attr('disabled','disabled');
    } else {
        $("#" + MAIN_CONTENT_BUTTON_ID).removeAttr('disabled');
    }
}

function addAlert(message) {
   $('#alerts').append(
        '<div class="alert alert-light" id="alert-style">' +
        '<button type="button" class="close" data-dismiss="alert">' +
        '&times;</button>' + message + '</div>');
         }

/**
 * Save widget design setting.
 * @param {*} widgetDesignData
 */
function saveWidgetDesignSetting(widgetDesignData) {
    let repositoryId = $("#repository-id").val();
    if (repositoryId == "0") {
        //alert('Please select the Repository.');
        var modalcontent =  "Please select the Repository.";
        $("#inputModal").html(modalcontent);
        $("#allModal").modal("show");
        return false;
    } else if (!widgetDesignData) {
        //alert('Please add Widget to Preview panel.');
        var modalcontent =  "Please add Widget to Preview panel";
        $("#inputModal").html(modalcontent);
        $("#allModal").modal("show");
        return false;
    } else if(!isHasMainContent){
        //alert('Please add Main Content to Preview panel.');
        var modalcontent =  "Please add Main Content to Preview panel.";
        $("#inputModal").html(modalcontent);
        $("#allModal").modal("show");
        return false;
    }

    let saveData = JSON.stringify(widgetDesignData);
    if (saveData && Object.keys(widgetDesignData).length) {
        let postData = {
            'repository_id': repositoryId,
            'settings': saveData
        };
        $.ajax({
            url: "/api/admin/save_widget_layout_setting",
            type: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            data: JSON.stringify(postData),
            dataType: 'json',
            success: function (data, status) {
                let err_msg = data.error;
                if (err_msg) {
                    //alert(err_msg);
                    var modalcontent = err_msg;
                    $("#inputModal").html(modalcontent);
                    $("#allModal").modal("show");
                } else if (!data.result) {
                    //alert('Fail to save Widget design. Please check again.');
                    var modalcontent = "Fail to save Widget design. Please check again.";
                    $("#inputModal").html(modalcontent);
                    $("#allModal").modal("show");
                    return;
                } else {
                    addAlert('Widget design has been saved successfully.');
                    return;
                }
            },
            error: function (error) {
                console.log(error);
            }
        });
    } else {
        //alert('Please add Widget to Preview panel.');
        var modalcontent =  "Please add Widget to Preview panel.";
        $("#inputModal").html(modalcontent);
        $("#allModal").modal("show");
        return;
    }
}
