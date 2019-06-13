const MAIN_CONTENT_TYPE = "Main contents";
const FREE_DESCRIPTION_TYPE = "Free description";
const NOTICE_TYPE = "Notice";
const HIDE_REST_DEFAULT = "Hide the rest";
const READ_MORE_DEFAULT = "Read more";
const NEW_ARRIVALS = "New arrivals";
const ACCESS_COUNTER = "Access counter";

(function () {
    getWidgetDesignSetting();
    window.lodash = _.noConflict();
}());

let PageBodyGrid = function () {
    this.init = function () {
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

    this.addNewWidget = function (node, index) {
        this.grid.addWidget($(this.widgetTemplate(node, index)), node.x, node.y, node.width, node.height);
        return false;
    }.bind(this);

    this.updateMainContent = function (node) {
        let mainContents = $("#main_contents");
        this.grid.update(mainContents, node.x, node.y, node.width, node.height);
    };

    this.loadGrid = function (widgetListItems) {
        let items = GridStackUI.Utils.sort(widgetListItems);
        items.forEach(function (node) {
            if (MAIN_CONTENT_TYPE == node.type) {
                this.updateMainContent(node);
                return false;
            }
        }, this);

        for (var i = 0; i < items.length; i++) {
            let node = items[i];
            if (MAIN_CONTENT_TYPE != node.type) {
                this.addNewWidget(node, i);
            }
        }
        return false;
    }.bind(this);

    this.buildNoticeType = function (languageDescription, index) {
        let description = "";
        let moreDescriptionID = (NOTICE_TYPE + "_" + index).trim();
        let linkID = "writeMoreNotice_" + index;
        let moreDescription = "";
        let templateWriteMoreNotice = '<div id="' + moreDescriptionID + '" style="display: none;">' +
            moreDescription + '</div>';

        if (languageDescription.more_description) {
            moreDescription = languageDescription.more_description;
            let hideRest = (languageDescription.hide_the_rest) ? languageDescription.hide_the_rest : HIDE_REST_DEFAULT;
            let readMore = (languageDescription.read_more) ? languageDescription.read_more : READ_MORE_DEFAULT;
            templateWriteMoreNotice = '</br>' +
                '<div id="' + moreDescriptionID + '" style="display: none;">' + moreDescription + '</div>' +
                '<a id="' + linkID + '" class="writeMoreNoT" onclick="handleMoreNoT(\'' + moreDescriptionID + '\',\'' +
                linkID + '\',\'' + readMore + '\', \'' + hideRest + '\')">' + readMore +
                '</a>';
        }

        if (!$.isEmptyObject(languageDescription)) {
            description = languageDescription.description + templateWriteMoreNotice;
        }
        return description;
    };

    this.buildAccessCounter = function(initNumber) {
        // TODO: Get access count from API
        let dummyData = 123456789;

        // Convert to display-able number
        let initNum = Number(initNumber);
        let result = Number(dummyData);
        if (Number.isNaN(initNum)) {
            result = dummyData + initNumber;
        }
        return '<div style="text-align: center; font-size: 20px; font-weight: bold; margin: auto; width: 50%;">'+result+'</div>';
    }

    this.buildNewArrivals = function(request_data, id) {
        $.ajax({
            method: 'POST',
            url: '/api/admin/get_new_arrivals',
            headers: {
                'Content-Type': 'application/json'
              },
            data: JSON.stringify(request_data),
            dataType: 'json',
            success: function(response) {
                let result = response['data'];
                let host = window.location.origin;
                let innerHTML = '';
                for (let data in result) {
                    innerHTML += '<li><a href="' + host + result[data]['url'] + '">' + result[data]['name'] +'</a></li>';
                }
                innerHTML = '<div class="no-li-style">' + innerHTML + '</div>';
                $("#"+id).append(innerHTML)
            }
        })
    }

    this.widgetTemplate = function (node, index) {
        let labelColor = "";
        let frameBorderColor = "";
        let backgroundColor = "";
        let content = "";
        let multiLangSetting = node.multiLangSetting;
        let languageDescription = "";
        let leftStyle = "left: initial; ";
        let paddingHeading = "padding: inherit; ";
        let overFlowBody = "overflow-y: scroll; ";
        let id = '';
        // Handle css style
        if (node.background_color) {
            backgroundColor = "background-color: " + node.background_color + "; ";
        }

        if(node.frame_border && node.frame_border_color) {
            frameBorderColor = "border-color: " + node.frame_border_color + "; ";
        }

        if (node.label_color) {
            labelColor = "color: " + node.label_color + "; ";
        }

        if (!$.isEmptyObject(multiLangSetting.description)) {
            languageDescription = multiLangSetting.description;
        }

        if (node.type == FREE_DESCRIPTION_TYPE) {
            if (!$.isEmptyObject(languageDescription)){
                content = languageDescription.description;
            }
        } else if (node.type == NOTICE_TYPE) {
            content = this.buildNoticeType(languageDescription, index);
        } else if (node.type == ACCESS_COUNTER) {
            content = this.buildAccessCounter(5);
        } else if (node.type == NEW_ARRIVALS) {
            let innerID = 'new_arrivals'+ '_' + index;
            id = 'id="' + innerID + '"';
            let fake_data = {
                'list_dates':
                [
                    "2019-06-13",
                    "2019-06-12"
                ],
                'number_result': '3',
                'rss_status': true
            }
            this.buildNewArrivals(fake_data, innerID);
        }

        let template =
            '<div class="grid-stack-item">' +
            ' <div class="grid-stack-item-content panel panel-default widget" style="' +
            backgroundColor + frameBorderColor + '">' +
            '     <div class="panel-heading widget-header widget-header-position" style="' + labelColor + leftStyle + '">' +
            '       <strong style="' + paddingHeading + '">' + multiLangSetting.label + '</strong>' +
            '     </div>' +
            '     <div class="panel-body ql-editor pad-top-30"' + id +' style="' + overFlowBody + '">' +
            content + '</div>' +
            '   </div>' +
            '</div>';

        return template;
    };

};

function getWidgetDesignSetting() {
    let community_id = $("#community-id").text();
    let current_language = $("#current_language").val();
    if (!community_id) {
        community_id = 'Root Index';
    }
    if (!current_language) {
        current_language = "en";
    }
    let url = '/api/admin/load_widget_design_setting/' + community_id + '/' + current_language;
    $.ajax({
        type: 'GET',
        url: url,
        success: function (data) {
            if (data.error) {
                console.log(data.error);
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
    $("div#page_body").each(function () {
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
