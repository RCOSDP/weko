const mainContentType = "Main contents";
const freeDescriptionType = "Free description";
const noticeType = "Notice";
const hideRestDefaultText = "Hide the rest";
const readMoreDefaultText = "Read more";

(function() {
    getWidgetDesignSetting();
    window.lodash = _.noConflict();
}());

let PageBodyGrid = function() {
    this.init = function() {
        let options = {
            width: 12,
            float: true,
            verticalMargin: 4,
            cellHeight: 100,
            acceptWidgets: '.grid-stack-item'
        };
        let widget = $('#page_body');
        widget.gridstack(options);
        this.grid = widget.data('gridstack');
    };

    this.addNewWidget = function(node, index) {
        this.grid.addWidget($(this.widgetTemplate(node, index)), node.x, node.y, node.width, node.height);
        return false;
    }.bind(this);

    this.updateMainContent = function(node) {
        let mainContents = $("#main_contents");
        this.grid.update(mainContents, node.x, node.y, node.width, node.height);
    };

    this.loadGrid = function(widgetListItems) {
        let items = GridStackUI.Utils.sort(widgetListItems);
        items.forEach(function(node) {
            if (mainContentType == node.type) {
                this.updateMainContent(node);
                return false;
            }
        }, this);

        for (var i = 0; i < items.length; i++) {
            let node = items[i];
            if (mainContentType != node.type) {
                this.addNewWidget(node, i);
            }
        }
        return false;
    }.bind(this);

    this.widgetTemplate = function(node, index) {

        let labelColor = node.label_color;
        let frameBorderColor = ((node.frame_border) ? node.frame_border_color : "");
        let backgroundColor = node.background_color;
        let description = "";
        let leftStyle = 0;
        let paddingHeading = "";
        let overFlowBody = "";

        if (node.type == freeDescriptionType) {
            description = node.description;
            leftStyle = "initial";
            paddingHeading = "inherit";
            overFlowBody = "scroll";
        }

        if (node.type == noticeType) {
            let moreDescriptionID = (node.type + "_" + index).trim();
            let linkID = "writeMoreNotice_" + index;
            let moreDescription = "";
            let templateWriteMoreNotice = '<div id="' + moreDescriptionID + '" style="display: none;">' +
                moreDescription + '</div>';

            if (typeof node.more_description != 'undefined') {
                moreDescription = node.more_description;
                let hideRest = ((node.hide_the_rest != "") ? node.hide_the_rest : hideRestDefaultText);
                let readMore = ((node.read_more != "") ? node.read_more : readMoreDefaultText);
                templateWriteMoreNotice = '</br>' +
                    '<div id="' + moreDescriptionID + '" style="display: none;">' + moreDescription + '</div>' +
                    '<a id="' + linkID + '" class="writeMoreNoT" onclick="handleMoreNoT(\'' + moreDescriptionID + '\',\'' +
                    linkID + '\',\'' + readMore + '\', \'' + hideRest + '\')">' +
                    ((node.read_more != "") ? node.read_more : readMoreDefaultText) +
                    '</a>';
            }

            description = node.description + templateWriteMoreNotice;

            leftStyle = "initial";
            paddingHeading = "inherit";
            overFlowBody = "scroll";
        }

        let template =
            '<div class="grid-stack-item">' +
            ' <div class="grid-stack-item-content panel panel-default widget" style="background-color: ' +
            backgroundColor + '; border-color: ' + frameBorderColor + ';">' +
            '     <div class="panel-heading widget-header widget-header-position" style="color: ' + labelColor + ';left: ' +
            leftStyle + ';">' +
            '       <strong style="padding: ' + paddingHeading + ';">' + node.name + '</strong>' +
            '     </div>' +
            '     <div class="panel-body ql-editor" style="padding-top: 30px; overflow-y: ' + overFlowBody + ';">' +
            description + '</div>' +
            '   </div>' +
            '</div>';

        return template;
    };

};

function getWidgetDesignSetting() {
    let community_id = $("#community-id").text();
    if (!community_id) {
        community_id = 'Root Index';
    }
    let url = '/api/admin/load_widget_design_setting/' + community_id;
    $.ajax({
        type: 'GET',
        url: url,
        success: function(data) {
            if (data.error) {
                alert(error);
                toggleWidgetUI();
                return;
            } else {
                let widgetList = data['widget-settings'];
                if (Array.isArray(widgetList) && widgetList.length) {
                    $("#main_contents").addClass("grid-stack-item");
                    let pageBodyGrid = new PageBodyGrid();
                    pageBodyGrid.init();
                    pageBodyGrid.loadGrid(widgetList);
                }
            }
            toggleWidgetUI();
        }
    });
}

function toggleWidgetUI() {
    $("div#page_body").each(function() {
        $(this).css("display", "block");
        $('footer#footer').css("display", "block");
        $('footer-fix#footer').remove();
    });
}

function handleMoreNoT(moreDescriptionID, linkID, readMore, hideRest) {
    var moreDes = $("#" + moreDescriptionID);
    if (moreDes) {
        if (moreDes.is(":hidden")) {
            moreDes.show();
            $("#" + linkID).text(hideRest);
        } else {
            moreDes.hide();
            $("#" + linkID).text(readMore);
        }
    }
}
