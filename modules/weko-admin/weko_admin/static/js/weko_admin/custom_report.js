class ComponentTableResult extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      rows: [],
      cols: [],
      componentClass: "hidden",
      paging: [],
      pagingClassLeft: "hidden",
      pagingClassRight: "hidden",
      selectedPage: 1
    };
    this.displayData = this.displayData.bind(this);
    this.initPageButton = this.initPageButton.bind(this);
    this.handleClickEvent = this.handleClickEvent.bind(this);
  }

  handleClickEvent(event) {
    let selection = event.target.dataset.numPage;
    let selectedPage = this.state.selectedPage;

    if (selection == "first") {
      selectedPage = 1;
    } else if (selection == "last") {
      selectedPage = this.props.numPage;
    } else if (selection == "next") {
      if (Number(selectedPage) + 1 <= this.props.numPage) {
        selectedPage = Number(selectedPage) + 1;
      }
    } else if (selection == "previous") {
      if (Number(selectedPage) - 1 != 0) {
        selectedPage = Number(selectedPage) - 1;
      }
    } else {
      selectedPage = selection;
    }
    this.initPageButton(selectedPage);
    this.setState({
      selectedPage: selectedPage
    });

    // Get data for new page
    let startDate = document.getElementById("start_date").value;
    let endDate = document.getElementById("end_date").value;
    let target = document.getElementById("target").value;
    let unit = document.getElementById("unit").value;
    let unitText = document.getElementById("unit").options[document.getElementById("unit").selectedIndex].text

    let requestParam = {
      start_date: startDate || '0',
      end_date: endDate || '0',
      unit: unit
    };
    let request_url = '/api/stats/' + target + '/' + requestParam['start_date'].replace(/\//g, '-') + '/' + requestParam['end_date'].replace(/\//g, '-') + '/' + unitText + '?p=' + selectedPage;
    fetch(request_url/*,
        TODO: Display to result table {
          method: "GET",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify(requestParam)
        }*/)
      .then(res => res.json())
      .then((result) => {
        this.displayData(result.data);
      });
  }

  initPageButton(selectedPage) {
    if (!selectedPage) {
      selectedPage = this.state.selectedPage
    }
    if (this.props.numPage != 1) {
      // Create inner html for buttons
      let frontPage = Number(selectedPage) - 1;
      let nextPage = Number(selectedPage) + 1;
      let innerHTML = [];
      let frontInnerHTML =
        <li>
          <a data-num-page={frontPage} onClick={this.handleClickEvent}>{frontPage}</a>
        </li>;
      let nextInnerHTML =
        <li>
          <a data-num-page={nextPage} onClick={this.handleClickEvent}>{nextPage}</a>
        </li>;
      let selectedInnerHTML =
        <li className="active">
          <a data-num-page={selectedPage} onClick={this.handleClickEvent}>{selectedPage}</a>
        </li>;
      if (frontPage > 0) {
        innerHTML.push(frontInnerHTML);
      }
      innerHTML.push(selectedInnerHTML);
      if (nextPage <= this.props.numPage) {
        innerHTML.push(nextInnerHTML);
      }

      // Script display << < > >> buttons
      let leftState = "disabled"
      let rightState = "disabled"
      if (selectedPage != 1 && selectedPage > 0) {
        leftState = "";
      }
      if (selectedPage != this.props.numPage && selectedPage < this.props.numPage) {
        rightState = "";
      }

      // Set state
      this.setState({
        paging: innerHTML,
        pagingClassLeft: leftState,
        pagingClassRight: rightState
      });
    } else {
      this.setState({
        pagingClassLeft: "hidden",
        pagingClassRight: "hidden",
      });
    }
  }

  displayData(resultData) {
    let rows = [];
    let cell = [];
    let data = resultData;
    let cols = [];
    let unit = document.getElementById("unit").value;
    const UNIT_HOST = 5;
    const UNIT_ITEM = 4;
    const UNIT_DAY = 1;
    if (unit == UNIT_HOST || unit == UNIT_ITEM) {
      if (unit == UNIT_HOST) {
        cols.push(<col className="col-md-5" />);
        cols.push(<col className="col-md-4" />);
        cols.push(<col className="col-md-3" />);
        cell.push(<th style={this.styleTable}>Host</th>);
        cell.push(<th style={this.styleTable}>IP Address</th>);
        cell.push(<th style={this.styleTable}>Counts</th>);
        rows.push(<tr>{cell}</tr>);
        for (var i = 0; i < data.length; i++) {
          cell = [];
          cell.push(<td style={this.styleTable}>{data[i].domain}</td>);
          cell.push(<td style={this.styleTable}>{data[i].ip}</td>);
          cell.push(<td style={this.styleTable}>{data[i].count}</td>);
          rows.push(<tr style={this.styleTable}>{cell}</tr>);
        }
      } else {
        cols.push(<col className="col-md-3" />);
        cols.push(<col className="col-md-6" />);
        cols.push(<col className="col-md-3" />);
        cell.push(<th style={this.styleTable}>Item ID</th>);
        cell.push(<th style={this.styleTable}>Item Name</th>);
        cell.push(<th style={this.styleTable}>Counts</th>);
        rows.push(<tr>{cell}</tr>);
        for (var i = 0; i < data.length; i++) {
          cell = [];
          cell.push(<td style={this.styleTable}>{data[i].col1}</td>);
          cell.push(<td style={this.styleTable}>{data[i].col2}</td>);
          cell.push(<td style={this.styleTable}>{data[i].col3}</td>);
          rows.push(<tr style={this.styleTable}>{cell}</tr>);
        }
      }
    }
    else {
      cols.push(<col className="col-md-8" />);
      cols.push(<col className="col-md-4" />);
      cell.push(<th style={this.styleTable}>Period</th>);
      cell.push(<th style={this.styleTable}>Counts</th>);
      rows.push(<tr>{cell}</tr>);
      for (var i = 0; i < data.length; i++) {
        cell = [];
        let year = '';
        if (data[i].year) {
          year = data[i].year;
        } else if (unit == UNIT_DAY) {
          year = data[i].start_date;
        } else {
          year = data[i].start_date + " - " + data[i].end_date;
        }
        cell.push(<td style={this.styleTable}>{year}</td>);
        cell.push(<td style={this.styleTable}>{data[i].count}</td>);
        rows.push(<tr >{cell}</tr>);
      }
    }
    this.setState({
      rows: rows,
      cols: cols,
      componentClass: "form-group row margin_0"
    });
  }

  componentWillReceiveProps(props) {
    const { hidden } = this.props;
    if (hidden != props.hidden) {
      if (props.hidden) {
        this.setState({
          componentClass: "hidden"
        });
      } else {
        this.displayData(props.data);
        this.setState({
          selectedPage: 1,
          paging: []
        });
        this.initPageButton(1);
      }
    }
  }

  render() {
    return (
      <div style={this.styleContainer} className={this.state.componentClass}>
        <label className="control-label col-xs-2 text-right" htmlFor={this.props.id_component} style={this.styleLabel}>{this.props.name}</label>
        <div class="controls col-xs-5">
          <br />
          <div id="no_data" className="hidden">There is no data.</div>
          <table className="table table-striped" style={this.styleTable}>
            <colgroup>
              {this.state.cols}
            </colgroup>
            <tbody>
              {this.state.rows}
            </tbody>
          </table>
          <ul className="pagination page" id="pagination">
            <li className={this.state.pagingClassLeft}>
              <a data-num-page="first" onClick={this.handleClickEvent}>&lt;&lt;</a>
            </li>
            <li className={this.state.pagingClassLeft}>
              <a data-num-page="previous" onClick={this.handleClickEvent}>&lt;</a>
            </li>
            {this.state.paging}
            <li className={this.state.pagingClassRight}>
              <a data-num-page="next" onClick={this.handleClickEvent}>&gt;</a>
            </li>
            <li className={this.state.pagingClassRight}>
              <a data-num-page="last" onClick={this.handleClickEvent}>&gt;&gt;</a>
            </li>
          </ul>
        </div>
      </div>
    )
  }
}

class ComponentCombobox extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      selections: [],
      displayButton: <button className="hidden"></button>,
      responseData: [],
      disabled: true
    };
    this.required = {
      color: 'red',
    };
    this.handleClickEvent = this.handleClickEvent.bind(this);
    this.handleChangeEvent = this.handleChangeEvent.bind(this);
    this.checkValidDate = this.checkValidDate.bind(this);
  }
  componentDidMount() {
    if (this.props.id_component == 'target') {
      let initURL = "/api/admin/get_init_selection/target";
      fetch(initURL)
        .then(res => res.json())
        .then(
          (result) => {
            let selectionData = result[this.props.id_component];
            let options = selectionData.map((option) => {
              return (
                <option key={option.id} value={option.id}>{option.data}</option>
              );
            });
            this.setState({
              selections: options,
              disabled: false
            });
          }
        );
    }
    let buttonHtml;
    if (this.props.id_component == 'unit') {
      buttonHtml = <button className="btn btn-primary action-button col-md-2" onClick={this.handleClickEvent}>Display</button>
    } else {
      <button className="hidden"></button>
    }
    this.setState({
      displayButton: buttonHtml
    });
  }

  componentWillReceiveProps(props) {
    const { disable } = this.props;
    const { target } = this.props;
    if (disable != props.disable || target != props.target) {
      if (this.props.id_component == 'unit') {
        if (props.disable) {
          let target = document.getElementById("target").value;
          let initURL = "/api/admin/get_init_selection/" + target;
          fetch(initURL)
            .then(res => res.json())
            .then(
              (result) => {
                let selectionData = result[this.props.id_component];
                let options = selectionData.map((option) => {
                  return (
                    <option key={option.id} value={option.id}>{option.data}</option>
                  );
                });
                this.setState({
                  selections: options,
                  disabled: !props.disable
                });
              }
            );
        } else {
          this.setState({
            disabled: !props.disable
          });
        }
      }
    }
  }

  handleChangeEvent(event) {
    this.props.getValueOfField(this.props.result, null);
    this.props.getTableHidden(true);
    if (this.props.id_component == 'target') {
      document.getElementById("unit").value = 0;
      if (event.target.value != 0) {
        this.props.getUnitStatus(true, event.target.value);
      } else {
        this.props.getUnitStatus(false, event.target.value);
      }
    }
  }

  checkValidDate(start_date, end_date) {
    const IS_NOT_VALID = -1;
    const START_DATE_IS_GREATER = 0;
    const VALID = 1;
    if (!start_date && !end_date) {
      return VALID;
    } else if (!start_date) {
      let endDate = Date.parse(end_date);
      if (isNaN(end_date) && !isNaN(endDate)) {
        return VALID;
      } else {
        return IS_NOT_VALID;
      }
    } else if (!end_date) {
      let startDate = Date.parse(start_date);
      if (isNaN(start_date) && !isNaN(startDate)) {
        return VALID;
      } else {
        return IS_NOT_VALID;
      }
    } else {
      let startDate = Date.parse(start_date);
      let endDate = Date.parse(end_date);
      if (isNaN(end_date) && !isNaN(endDate) && isNaN(start_date) && !isNaN(startDate)) {
        if (endDate >= startDate) {
          return VALID;
        } else {
          return START_DATE_IS_GREATER;
        }
      } else {
        return IS_NOT_VALID;
      }
    }
  }

  handleClickEvent(event) {
    let startDate = document.getElementById("start_date").value;
    let endDate = document.getElementById("end_date").value;
    let target = document.getElementById("target").value;
    let unit = document.getElementById("unit").value;
    let unitText = document.getElementById("unit").options[document.getElementById("unit").selectedIndex].text
    let repository = document.getElementById("repository_select").value;
    this.props.getTableHidden(true);
    if (target == 0) {
      var modalcontent = "Target Report is required!";
      $("#inputModal").html(modalcontent);
      $("#allModal").modal("show");
    } else if (unit == 0) {
      var modalcontent = "Unit is required!";
      $("#inputModal").html(modalcontent);
      $("#allModal").modal("show");
    } else if (this.checkValidDate(startDate, endDate) == -1) {
      var modalcontent = "Date is not valid!";
      $("#inputModal").html(modalcontent);
      $("#allModal").modal("show");
    } else if (this.checkValidDate(startDate, endDate) == 0) {
      var modalcontent = "Start date is greater than End date!";
      $("#inputModal").html(modalcontent);
      $("#allModal").modal("show");
    } else {
      let requestParam = {
        start_date: startDate || '0',
        end_date: endDate || '0',
        unit: unit
      };
      let request_url = '/api/stats/' + target + '/' + requestParam['start_date'].replace(/\//g, '-') + '/' + requestParam['end_date'].replace(/\//g, '-') + '/' + unitText + '?p=1&repo=' + repository;
      fetch(request_url)
        .then(res => res.json())
        .then((result) => {
          if (result.data.length == 0) {
            if (document.getElementById('no_data').classList.contains('hidden')) {
              document.getElementById('no_data').classList.remove('hidden')
            }
            if (!document.getElementById('pagination').classList.contains('hidden')) {
              document.getElementById('pagination').classList.add('hidden')
            }
          } else {
            if (!document.getElementById('no_data').classList.contains('hidden')) {
              document.getElementById('no_data').classList.add('hidden')
            }
            if (document.getElementById('pagination').classList.contains('hidden')) {
              document.getElementById('pagination').classList.remove('hidden')
            }
          }
          this.props.getValueOfField(this.props.key_binding, result.data);
          this.props.getNumPage(result.num_page);
          this.props.getTableHidden(false);
        });
    }
  }

  render() {
    return (
      <div className="form-group row margin_0">
        <label htmlFor={this.props.id_component} className="control-label col-xs-2 text-right">
          {this.props.name}
          <span style={this.required}>
            *
          </span>
        </label>
        <div class="controls col-xs-5">
          <select className="form-control" id={this.props.id_component} disabled={this.state.disabled} onChange={this.handleChangeEvent}>
            <option key="0" value="0">Please select the&nbsp; {this.props.id_component}</option>
            {this.state.selections}
          </select>
        </div>
        {this.state.displayButton}
      </div>
    )
  }
}

class ComponentDatePicker extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      defaultClass: "controls col-xs-5",
      errorMessageClass: "hidden"
    }
    this.styleContainer = {
    }
    this.styleLabel = {
      "display": "inline",
    }
    this.styleDatePicker = {
      "border-radius": "3%",
      "background-color": "#fff",
    }

    this.handleChangeEvent = this.handleChangeEvent.bind(this)
  }

  handleChangeEvent(event) {
    let dateData = document.getElementById(this.props.id_component).value;
    let date = Date.parse(dateData);
    let dateElement = dateData.split('/');
    if (!dateData) {
      this.setState({
        defaultClass: "controls col-xs-5",
        errorMessageClass: "hidden"
      });
    }
    else if (dateElement.length == 3 && dateElement[0] && dateElement[1] && dateElement[2]) {
      if (isNaN(dateData) && !isNaN(date)) {
        this.setState({
          defaultClass: "controls col-xs-5",
          errorMessageClass: "hidden"
        });
      } else {
        this.setState({
          defaultClass: "controls col-xs-5 has-error",
          errorMessageClass: ""
        });
      }
    } else {
      this.setState({
        defaultClass: "controls col-xs-5 has-error",
        errorMessageClass: ""
      });
    }
  }

  render() {
    return (
      <div style={this.styleContainer} className="form-group row margin_0">
        <label className="control-label col-xs-2 text-right" htmlFor={this.props.id_component} style={this.styleLabel}>{this.props.name}</label>
        <div class={this.state.defaultClass} id={this.props.date_picker_id}>
          <input className="form-control" onChange={this.handleChangeEvent} name={this.props.component_name} id={this.props.id_component} style={this.styleDatePicker} type="text" />
          <div id={this.props.error_id} style={{ color: 'red' }} className={this.state.errorMessageClass}>Format is incorrect!</div>
        </div>
      </div>
    )
  }
}

class MainLayout extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      result: [],
      unitStatus: false,
      tableHidden: true,
      target: 0,
      numPage: 0
    };
    this.getValueOfField = this.getValueOfField.bind(this);
    this.getUnitStatus = this.getUnitStatus.bind(this);
    this.getTableHidden = this.getTableHidden.bind(this);
    this.getNumPage = this.getNumPage.bind(this);
  }

  getTableHidden(value) {
    this.setState({
      tableHidden: value
    });
  }

  getNumPage(value) {
    this.setState({
      numPage: value
    });
  }

  getUnitStatus(value, target) {
    this.setState({
      unitStatus: value,
      target: target
    });
  }

  getValueOfField(key, value) {
    switch (key) {
      case 'result':
        this.setState({
          result: value
        });
        break;
    }
  }

  render() {
    return (
      <div>
        <div class="row content-font">
          <div className="col-md-1">
          </div>
          <div className="col-md-11 pull-left">
            <h4>Custom Report</h4>
            <ComponentDatePicker component_name='start_date' name="Start Date" id_component="start_date" date_picker_id="start_date_picker"
              error_id="start_error" getTableHidden={this.getTableHidden} />
            <ComponentDatePicker component_name='end_date' name="End Date" id_component="end_date" date_picker_id="end_date_picker"
              error_id="end_error" getTableHidden={this.getTableHidden} />
            <ComponentCombobox name="Target Report" getValueOfField={this.getValueOfField} getTableHidden={this.getTableHidden}
              id_component="target" getUnitStatus={this.getUnitStatus} />
            <ComponentCombobox name="Unit" getValueOfField={this.getValueOfField} key_binding="result" id_component="unit"
              disable={this.state.unitStatus} getTableHidden={this.getTableHidden} target={this.state.target} getNumPage={this.getNumPage} />
            <ComponentTableResult name="Result" data={this.state.result} hidden={this.state.tableHidden} numPage={this.state.numPage} />
          </div>
        </div>
      </div>
    )
  }
}

$(function () {
  ReactDOM.render(
    <MainLayout />,
    document.getElementById('root')
  );
  initDatepicker();
});

function initDatepicker() {
  $("#start_date").datepicker({
    format: "yyyy/mm/dd",
    todayBtn: "linked",
    autoclose: true,
    forceParse: false
  })
    .on("changeDate", function (e) {
      if (document.getElementById("start_date_picker").classList.contains('has-error')) {
        document.getElementById("start_date_picker").classList.remove('has-error');
      }
      if (!document.getElementById("start_error").classList.contains('hidden')) {
        document.getElementById("start_error").classList.add('hidden');
      }
    });
  $("#end_date").datepicker({
    format: "yyyy/mm/dd",
    todayBtn: "linked",
    autoclose: true,
    forceParse: false
  })
    .on("changeDate", function (e) {
      if (document.getElementById("end_date_picker").classList.contains('has-error')) {
        document.getElementById("end_date_picker").classList.remove('has-error');
      }
      if (!document.getElementById("end_error").classList.contains('hidden')) {
        document.getElementById("end_error").classList.add('hidden');
      }
    });
}
