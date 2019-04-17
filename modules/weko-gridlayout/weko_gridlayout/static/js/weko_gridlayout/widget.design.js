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
                            <option key={option.id} value={option.id}>{option.title}</option>
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
        let url = "/api/admin/load_widget_design_setting/" + event.target.value;
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


        this.setState({ repositoryId: event.target.value });
        this.props.callbackMainLayout(event.target.value);
        event.preventDefault();
    }

    render() {
        return (
            <div className="form-group row">
                <label htmlFor="input_type" className="control-label col-xs-1">Repository<span style={this.styleRed}>*</span></label>
                <div class="controls col-xs-5">
                    <select id="repository-id" value={this.state.repositoryId} onChange={this.handleChange} className="form-control">
                        <option value="0">Please selected the Repository</option>
                        {this.state.selectOptions}
                    </select>
                </div>
            </div>
        )
    }

}

class WidgetList extends React.Component {
    constructor(props) {
        super(props);
        this.style = {
            "border": "1px solid #eee",
            "min-height": "300px",
            "overflow": "scroll",
            "overflow-x": "hidden",
            "margin-right": "0px"
        };
    }

    componentDidMount() {
        fetch("/api/admin/load_widget_list/0")
            .then(res => res.json())
            .then(
                (result) => {
                    if (result.error) {
                        console.log(result.error);
                        return;
                    }
                    let widgetList = result['widget-list'];
                    loadWidgetList(widgetList);
                },

                (error) => {
                    console.log(error);
                }
            );
    }

    reloadWidgetListPanel(repositoryId) {
        let url = "/api/admin/load_widget_list/" + repositoryId;
        fetch(url)
            .then(res => res.json())
            .then(
                (result) => {
                    if (result.error) {
                        console.log(result.error);
                        return;
                    }
                    let widgetList = result['widget-list'];
                    loadWidgetList(widgetList);
                },

                (error) => {
                    console.log(error);
                }
            );
    }

    componentWillReceiveProps(props) {
        const { repositoryId } = this.props;
        if (props.repositoryId !== repositoryId) {
            this.reloadWidgetListPanel(props.repositoryId);
        }
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

class PreviewWidget extends React.Component {
    constructor(props) {
        super(props);
        this.style = {
            "border": "1px solid #eee",
            "min-height": "200px",
            "height": "80%"
        };
    }

    componentDidMount() {
        fetch("/api/admin/load_widget_design_setting/0")
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
            <div>
                <label className="control-label row">Preview</label>
                <div className="row grid-stack" style={this.style} id="gridPreview">
                </div>
            </div>
        )
    }

}

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
        loadPreview.saveGrid();
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
                <button id="save-grid" className="btn btn-primary" style={this.style} onClick={this.handleSave}>Save</button>
                <button id="clear-grid" className="form-group btn btn-danger" onClick={this.handleCancel}>Cancel</button>
            </div>
        )
    }
}

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
 *
 */
var loadPreview = new function () {
    this.init = function () {
        var options = {
            width: 12,
            float: true,
            animate: true,
            removeTimeout: 100,
            acceptWidgets: '.grid-stack-item'
        };

        $('#gridPreview').gridstack(_.defaults({
            float: true
        }, options));

        this.serializedData = [
        ];

        this.grid = $('#gridPreview').data('gridstack');
    }

    this.loadGrid = function (widgetListItems) {
        this.grid.removeAll();
        var items = GridStackUI.Utils.sort(widgetListItems);
        _.each(items, function (node) {
            this.grid.addWidget($(
                '<div data-name="' + node.name + '" data-id="' + node.id + '">'
                + '<div class="center-block text-right"><div class="glyphicon glyphicon-remove" style="z-index: 90;"></div></div>'
                + '<div class="grid-stack-item-content">'
                + '<span class="widget-label">&lt;' + node.type + '&gt;</span>'
                + '<span class="widget-label">' + node.name + '</span>'
                + '</div>'
                + '<div/>'),
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
            if (!id) {
                return;
            }
            return {
                x: node.x,
                y: node.y,
                width: node.width,
                height: node.height,
                name: name,
                id: id,
                type: type
            };
        }, this);
        var filtered = this.serializedData.filter(function (el) {
            return el != null;
        });
        let saveData = JSON.stringify(filtered);
        if (saveData && Object.keys(filtered).length) {
            let postData = {
                'repository_id': $("#repository-id").val(),
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
                        alert(err_msg);
                    } else if (!data.result) {
                        alert('Fail to save Widget design. Please check again.');
                    } else {
                        alert('Widget design has been saved successfully.');
                    }
                },
                error: function (error) {
                    console.log(error);
                }
            });
        } else {
            alert('Please add Widget to Preview panel.');
            return;
        }

        return false;
    }.bind(this);

    this.clearGrid = function () {
        this.grid.removeAll();
        return false;
    }.bind(this);

    this.addNewWidget = function (node) {
        this.grid.addWidget($(
            '<div data-type="' + node.type + '" data-name="' + node.name + '" data-id="' + node.id + '" data-gs-auto-position="true">'
            + ' <div class="center-block text-right"><div class="glyphicon glyphicon-remove" style="z-index: 90;"></div></div>'
            + ' <div class="grid-stack-item-content">'
            + '<span class="widget-label">&lt;' + node.type + '&gt;</span>'
            + '<span class="widget-label">' + node.name + '</span>'
            + '  </div>'
            + '<div/>'),
            node.x, node.y, node.width, node.height);
        return false;
    }.bind(this);

    this.deleteWidget = function (item) {
        this.grid.removeWidget(item);
        return false;
    };
}

/**
 * Add widget
 */
function addWidget() {
    $('.add-new-widget').each(function () {
        var $this = $(this);
        $this.on("click", function () {
            let widgetName = $(this).data('widgetName');
            let widgetId = $(this).data('widgetId');
            let widgetType = $(this).data('widgetType');
            let node = {
                x: 0,
                y: 0,
                width: 2,
                height: 1,
                auto_position: true,
                name: widgetName,
                id: widgetId,
                type: widgetType
            };
            loadPreview.addNewWidget(node);
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
        float: false,
        animate: true,
        ddPlugin: false,
        removable: '.trash',
        removeTimeout: 100,
        cellHeight: 80,
        acceptWidgets: '.grid-stack-item'

    };
    $('#widgetList').gridstack(options);
    var widgetList = $('#widgetList').data('gridstack');
    widgetList.removeAll();
    let x = 0;
    let y = 0;
    _.each(widgetListItems, function (widget) {
        widgetList.addWidget($(
            '<div>'
            + '<div class="grid-stack-item-content">'
            + '<span class="widget-label">&lt;' + widget.widgetType + '&gt;</span>'
            + '<span class="widget-label">' + widget.widgetLabel + '</span>'
            + '<a data-widget-type="' + widget.widgetType + '"data-widget-name="' + widget.widgetLabel + '" data-widget-id="' + widget.widgetId + '" class="btn btn-default add-new-widget" href="#">Add Widget</a>'
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
    loadPreview.init();
    loadPreview.loadGrid(widgetListItems);
    removeWidget();
}

/**
 * Remove widget on Preview panel
 */
function removeWidget() {
    $('.glyphicon-remove').each(function () {
        var $this = $(this);
        $this.on("click", function () {
            let widget = $this.closest(".grid-stack-item");
            loadPreview.deleteWidget(widget);
        });
    });
}

$(function () {
    ReactDOM.render(
        <MainLayout />,
        document.getElementById('root')
    );
});