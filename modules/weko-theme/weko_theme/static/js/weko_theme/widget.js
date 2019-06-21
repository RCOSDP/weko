const MAIN_CONTENT_TYPE = "Main contents";
const FREE_DESCRIPTION_TYPE = "Free description";
const NOTICE_TYPE = "Notice";
const HIDE_REST_DEFAULT = "Hide the rest";
const READ_MORE_DEFAULT = "Read more";
const NEW_ARRIVALS = "New arrivals";
const ACCESS_COUNTER = "Access counter";
const INTERVAL_TIME = 60000; //one minute

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

    this.buildAccessCounter = function (initNumber) {
        let data = this.getAccessTopPageValue();
        // Convert to display-able number
        let initNum = Number(initNumber);
        let result = Number(data);
        if (!Number.isNaN(initNum)) {
            result = result + initNumber;
        }
        return '<div class="widget-access-counter" data-init-number="' + initNumber + '" style="text-align: center; font-size: 20px; font-weight: bold; margin: auto;">' + result + '</div>';
    };

    this.buildNewArrivals = function (request_data, id) {
        $.ajax({
            method: 'POST',
            url: '/api/admin/get_new_arrivals',
            headers: {
                'Content-Type': 'application/json'
            },
            data: JSON.stringify(request_data),
            dataType: 'json',
            success: (response) => {
                let result = response.data;
                let host = window.location.origin;
                let rssHtml = '';
                if (request_data.rss_status) {
                    rssHtml = '<a class="" href="javascript:void(0)">RSS<i class="fa fa-rss"></i></a>';
                }
                let innerHTML = '';
                for (let data in result) {
                    innerHTML += '<li><a class="a-new-arrivals arrival-scale" href="' + result[data].url + '">' + result[data].name + '</a></li>';
                }
                innerHTML = '<div class="no-li-style col-sm-9 no-padding-col">' + innerHTML + '</div><div class= "col-sm-3 rss">' + rssHtml + '</div>';
                $("#" + id).append(innerHTML);
            }
        });
    };

    this.widgetTemplate = function (node, index) {
        let labelColor = "";
        let frameBorderColor = "";
        let backgroundColor = "";
        let content = "";
        let multiLangSetting = node.multiLangSetting;
        let languageDescription = "";
        let leftStyle = "left: initial; ";
        let rightStyle = "";
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
            let initNumber = 0;
            if (node.access_counter &&
                !Number.isNaN(Number(node.access_counter))) {
                initNumber = Number(node.access_counter);
            }
            content = this.buildAccessCounter(initNumber);
            rightStyle = "right: unset; ";
            paddingHeading = "";
            overFlowBody = "overflow-y: hidden; ";
            setInterval(() => { this.setAccessCounterValue(); }, INTERVAL_TIME);
        } else if (node.type == NEW_ARRIVALS) {
            let innerID = 'new_arrivals' + '_' + index;
            id = 'id="' + innerID + '"';
            let date = new Date();

            let listDate = [this.parseDateFormat(date)];
            if (node.new_dates != "Today") {
                for (let i = 0; i < Number(node.new_dates); i++) {
                    date.setDate(date.getDate() - 1);
                    listDate.push(this.parseDateFormat(date));
                }

            }
            let data = {
                'list_dates': listDate,
                'number_result': node.display_result,
                'rss_status': node.rss_feed
            }
            this.buildNewArrivals(data, innerID);
        }

        let template =
            '<div class="grid-stack-item">' +
            ' <div class="grid-stack-item-content panel panel-default widget" style="' +
            backgroundColor + frameBorderColor + '">' +
            '     <div class="panel-heading widget-header widget-header-position" style="' + labelColor + leftStyle + rightStyle + '">' +
            '       <strong style="' + paddingHeading + '">' + multiLangSetting.label + '</strong>' +
            '     </div>' +
            '     <div class="panel-body ql-editor pad-top-30"' + id +' style="' + overFlowBody + '">' +
            content + '</div>' +
            '   </div>' +
            '</div>';

        return template;
    };

    this.parseDateFormat = function(d){
        let currentDate = "";
        currentDate = d.getFullYear();

        if (d.getMonth() < 9) {
            currentDate += "-0" + (d.getMonth() + 1);
        } else {
            currentDate += '-' + (d.getMonth() + 1);
        }

        if (d.getDate() < 10) {
            currentDate += "-0" + d.getDate();
        } else {
            currentDate += "-" + d.getDate();
        }
        return currentDate;
    };

    this.setAccessCounterValue = function(){
      let data = this.getAccessTopPageValue();
      let result = Number(data);
      $(".widget-access-counter").each(function(){
        let initNumber = $(this).data("initNumber");
        let accessCounter = result + initNumber;
        $(this).text(accessCounter);
      });
    };

    this.getAccessTopPageValue = function(){
        let data= 0;
        $.ajax({
                  url: '/api/stats/top_page_access/0/0',
                  method: 'GET',
                  async: false,
                  success: (response) => {
                      if (response.all && response.all.count) {
                          data = response.all.count;
                      }
                  }
              })
         return data;
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


