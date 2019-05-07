class ComponentTableResult extends React.Component
    {
      constructor(props)
      {
        super(props);
        this.state ={
          rows: [],
          cols: [],
          componentClass: "hidden"
        }
      }
      componentWillReceiveProps(props)
      {
        const { hidden } = this.props;
        if (hidden != props.hidden) {
          if (props.hidden) {
            this.setState({
              componentClass: "hidden"
            });
          }else {
            let rows = [];
            let cell = [];
            let data = props.data;
            let cols = [];
            let unit = document.getElementById("unit").value;
            const UNIT_HOST = 5;
            const UNIT_ITEM = 4;
            console.log(unit);
            if(unit == UNIT_HOST || unit == UNIT_ITEM)
            {
              if (unit == UNIT_HOST) {
                cols. push(<col className="col-md-5" />);
                cols. push(<col className="col-md-4" />);
                cols. push(<col className="col-md-3" />);
                cell.push(<th style={this.styleTable}>Host</th>);
                cell.push(<th style={this.styleTable}>IP Address</th>);
                cell.push(<th style={this.styleTable}>Counts</th>);
              }else {
                cols. push(<col className="col-md-3" />);
                cols. push(<col className="col-md-6" />);
                cols. push(<col className="col-md-3" />);
                cell.push(<th style={this.styleTable}>Item ID</th>);
                cell.push(<th style={this.styleTable}>Item Name</th>);
                cell.push(<th style={this.styleTable}>Counts</th>);
              }
              rows.push(<tr>{cell}</tr>);
              for( var i=0; i< data.length;i++)
              {
                cell = [];
                cell.push(<td style={this.styleTable}>{data[i].col1}</td>);
                cell.push(<td style={this.styleTable}>{data[i].col2}</td>);
                cell.push(<td style={this.styleTable}>{data[i].col3}</td>);
                rows.push(<tr style={this.styleTable}>{cell}</tr>);
              }
            }
            else
            {
              cols. push(<col className="col-md-8" />);
              cols. push(<col className="col-md-4" />);
              cell.push(<th style={this.styleTable}>Period</th>);
              cell.push(<th style={this.styleTable}>Counts</th>);
              rows.push(<tr>{cell}</tr>);
              for( var i=0; i< data.length;i++)
              {
                cell = [];
                cell.push(<td style={this.styleTable}>{data[i].col1}</td>);
                cell.push(<td style={this.styleTable}>{data[i].col2}</td>);
                rows.push(<tr >{cell}</tr>);
              }
            }
            this.setState({
              rows: rows,
              cols: cols,
              componentClass: "form-group row"
            });
          }
        }
      }

      render(){
        return(
          <div style={this.styleContainer} className={this.state.componentClass}>
            <label className="control-label col-xs-2 text-right" htmlFor={this.props.id_component} style={this.styleLabel}>{this.props.name}</label>
            <div class="controls col-xs-5">
              <br/>
              <table className ="table table-striped" style={this.styleTable}>
                <colgroup>
                  {this.state.cols}
                </colgroup>
                <tbody>
                  {this.state.rows}
                </tbody>
              </table>
            </div>
          </div>
        )
      }
    }

    class ComponentCombobox extends React.Component
    {
      constructor(props)
      {
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
      }
      componentDidMount() 
      {
        if (this.props.id_component == 'target') {
          let initURL = "/api/admin/get_init_selection/target";
          fetch(initURL)
          .then(res => res.json())
          .then(
            (result) => 
            {
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
          buttonHtml = <button className="btn btn-primary col-xs-1" onClick={this.handleClickEvent}>Display</button>
        }else {
          <button className="hidden"></button>
        }
        this.setState({
          displayButton: buttonHtml
        });
      }

      componentWillReceiveProps(props) {
        const { disable } = this.props;
        const { target } = this.props;
        if (disable != props.disable || target != props.target){
          if (this.props.id_component == 'unit') {
            this.setState({
              disabled: !props.disable
            });
            if (props.disable) {
              let target = document.getElementById("target").value;
              let initURL = "/api/admin/get_init_selection/"+target;
              fetch(initURL)
              .then(res => res.json())
              .then(
                (result) => 
                {
                  let selectionData = result[this.props.id_component];
                  let options = selectionData.map((option) => {
                    return (
                      <option key={option.id} value={option.id}>{option.data}</option>
                    );
                  });
                  this.setState({
                    selections: options
                  });
                }
              );
            }
          }
        }
      }

      handleChangeEvent(event) {
        if (this.props.id_component == 'target') {
          document.getElementById("unit").value = 0;
          if (event.target.value != 0) {
            this.props.getUnitStatus(true, event.target.value);
          } else {
            this.props.getUnitStatus(false, event.target.value);
          }
        }
      }

      handleClickEvent(event) {
        let startDate = document.getElementById("start_date").value;
        let endDate = document.getElementById("end_date").value;
        let target = document.getElementById("target").value;
        let unit = document.getElementById("unit").value;
        this.props.getTableHidden(true);
        if (target == 0) {
          alert("Target Report is required!");
        } else if (unit == 0) {
          alert("Unit is required!");
        }else {
          const ITEM_REG_ID = 1;
          const DETAIL_VIEW_ID = 2;
          if (target == ITEM_REG_ID) {
            let requestParam = {
              start_date: startDate,
              end_date: endDate,
              unit: unit
            };
            let request_url='/api/admin/get_statistic_item_regis/'+unit;
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
              this.props.getValueOfField(this.props.key_binding, result);
              this.props.getTableHidden(false);
            });
          }else if (target == DETAIL_VIEW_ID) {
            let requestParam = {
              start_date: startDate,
              end_date: endDate,
              unit: unit
            };
            let request_url='/api/admin/get_statistic_detail_view/'+unit;
            fetch(request_url/*, {
              TODO: Display to result table
              method: "GET",
              headers: {
                "Content-Type": "application/json"
              },
              body: JSON.stringify(requestParam)
            }*/)
            .then(res => res.json())
            .then((result) => {
              this.props.getValueOfField(this.props.key_binding, result);
              this.props.getTableHidden(false);
            });
          }
        }
      }
      
      render() {
        return (
          <div className="form-group row">
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

    class ComponentDatePicker extends React.Component
    {
      constructor(props)
      {
        super(props);
        this.styleContainer={
        }
        this.styleLabel = {
          "display" : "inline",
        }
        this.styleDatePicker={
          "border-radius": "3%",
          "background-color":"#fff",
        }
      }

      render(){
        return(
          <div style={this.styleContainer} className="form-group row">
            <label className="control-label col-xs-2 text-right" htmlFor={this.props.id_component} style={this.styleLabel}>{this.props.name}</label>
            <div class="controls col-xs-5">
              <input className="form-control" id={this.props.id_component} style={this.styleDatePicker} readonly="true" type="text"/>
            </div>
          </div>
        )
      }
    }

    class MainLayout extends React.Component 
    {
      constructor(props)
      {
        super(props);
        this.state = {
          result: [],
          unitStatus: false,
          tableHidden: true,
          target: 0
        };
        this.styleContainer = {
          "margin-left": "-14px",
        };
        this.getValueOfField = this.getValueOfField.bind(this);
        this.getUnitStatus = this.getUnitStatus.bind(this);
        this.getTableHidden = this.getTableHidden.bind(this);
      }

      getTableHidden(value) {
        this.setState({
          tableHidden: value
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
          <div class="row content-font">
            <div className="col-md-1">
            </div>
            <div style = {this.styleContainer} className="col-md-11 pull-left">
              <h4 style={this.styleTitle}>Custom Report</h4>
              <ComponentDatePicker name = "Start Date" id_component="start_date"/>
              <ComponentDatePicker name = "End Date" id_component="end_date"/>
              <ComponentCombobox name="Target Report" id_component="target" getUnitStatus={this.getUnitStatus}/>
              <ComponentCombobox name="Unit" getValueOfField={this.getValueOfField} key_binding="result" id_component="unit" disable={this.state.unitStatus} getTableHidden={this.getTableHidden} target={this.state.target}/>
              <ComponentTableResult name="Result" data={this.state.result} hidden={this.state.tableHidden}/>
            </div> 
          </div>
        )
        }
    }

    $(function ()
    {
      ReactDOM.render(
      <MainLayout/>,
      document.getElementById('root')
      );
      initDatepicker();
    });

    function initDatepicker(){
      $("#start_date").datepicker({
          format: "yyyy/mm/dd",
          todayBtn: "linked",
          autoclose: true
      });
      $("#end_date").datepicker({
          format: "yyyy/mm/dd",
          todayBtn: "linked",
          autoclose: true
      });
    }