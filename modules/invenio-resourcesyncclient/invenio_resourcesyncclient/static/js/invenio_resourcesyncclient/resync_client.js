const LABELS = {};
(function () {
  // Get all labels.
  let labels = document.getElementsByClassName('resync-client-label');
  for (let i = 0; i < labels.length; i++) {
    LABELS[labels[i].id] = labels[i].value;
  }
})();

const list_label = LABELS['lblResyncClientList'];
const create_label = LABELS['lblResyncClientCreate'];
const edit_label = LABELS['lblResyncClientEdit'];
const detail_label = LABELS['lblResyncClientDetail'];
const urlCreate = window.location.origin + "/admin/resync/create";
const urlUpdate = window.location.origin + "/admin/resync/update";
const urlDelete = window.location.origin + "/admin/resync/delete";
const urlGetList = window.location.origin + "/admin/resync/get_list";
const urlRunResync = window.location.origin + "/admin/resync/run_import";
const urlGetLogs = window.location.origin + "/admin/resync/get_logs";
const urlSync = window.location.origin + "/admin/resync/run_sync";
const urltoggleRunning = window.location.origin + "/admin/resync/toggle_auto";
const urlGetTreeList = window.location.origin + "/api/tree";
const urlGetRepositoryList = window.location.origin + "/admin/resync/get_repository";
const status = JSON.parse($("#status").text())
const resync_mode = JSON.parse($("#resync_mode").text())
const saving_format = JSON.parse($("#saving_format").text())
const default_state = {
  status: status.automatic,
  repository_name: "",
  index_id: "",
  base_url: "",
  from_date: null,
  to_date: null,
  interval_by_day: 1,
  resync_save_dir: "",
  resync_mode: resync_mode.baseline,
  saving_format: saving_format.jpcoar,
};

const default_label = {
  repository_name: "Repository Name",
  status: 'Status',
  index_id: "Index Id",
  index_name: "Index Name",
  base_url: "Base Url",
  resync_mode: "Mode",
  saving_format: "Saving Format",
  from_date: "From Date",
  to_date: "To Date",
  interval_by_day: "Interval by Day"
}

class MainLayout extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      current_step: 1,
      current_tab: "list",
      select_item: {},
      tabs: [
        {
          tab_key: "list",
          tab_name: list_label,
          step: 1
        },
        {
          tab_key: "create",
          tab_name: create_label,
          step: 1
        },
        {
          tab_key: "edit",
          tab_name: edit_label,
          step: 2
        },
        {
          tab_key: "detail",
          tab_name: detail_label,
          step: 2
        }
      ]
    };
    this.handleChangeTab = this.handleChangeTab.bind(this);
  }

  componentDidMount() { }

  handleChangeTab(select_tab, select_item = null) {
    const { tabs } = this.state;
    const a = tabs.filter(item => {
      return item.tab_key === select_tab;
    });
    if (a[0]) {
      const item = a[0];
      this.setState({
        current_tab: item.tab_key,
        current_step: item.step

      });
      if (select_item) {
        this.setState({
          select_item: select_item
        });
      }
    }
  }

  render() {
    const { tabs, current_step, current_tab, select_item } = this.state;
    return (
      <div className="resource row">
        <ul className="nav nav-tabs">
          {tabs.map((item, key) => {
            if (item.step <= current_step) {
              return (
                <li
                  role="presentation"
                  className={`${item.tab_key === current_tab ? "active" : ""}`}
                  onClick={() => this.handleChangeTab(item.tab_key)}
                >
                  <a href="#">{item.tab_name}</a>
                </li>
              );
            }
          })}
        </ul>
        {current_tab === tabs[0].tab_key ? (
          <div>
            <ListResyncComponent
              handleChangeTab={this.handleChangeTab}
            ></ListResyncComponent>
          </div>
        ) : (
          ""
        )}

        {current_tab === tabs[1].tab_key ? (
          <div>
            <CreateResyncComponent
              handleChangeTab={this.handleChangeTab}
              mode="create"
            ></CreateResyncComponent>
          </div>
        ) : (
          ""
        )}

        {current_tab === tabs[2].tab_key ? (
          <div>
            <CreateResyncComponent
              handleChangeTab={this.handleChangeTab}
              select_item={select_item}
              mode="edit"
            ></CreateResyncComponent>
            {/* </div> : ''} */}
          </div>
        ) : (
          ""
        )}

        {current_tab === tabs[3].tab_key ? (
          <div>
            <DetailResourceComponent
              handleChangeTab={this.handleChangeTab}
              select_item={select_item}
            ></DetailResourceComponent>
            {/* </div> : ''} */}
          </div>
        ) : (
          ""
        )}
      </div>
    );
  }
}

class ListResyncComponent extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      list_resource: []
    };
    this.handleGetList = this.handleGetList.bind(this);
    this.handleViewDetail = this.handleViewDetail.bind(this);
    this.handleEdit = this.handleEdit.bind(this);
    this.handleDelete = this.handleDelete.bind(this);
  }

  componentDidMount() {
    this.handleGetList();
  }

  handleGetList() {
    fetch(urlGetList, {
      method: "GET",
      headers: {
        "Content-Type": "application/json"
      }
    })
      .then(res => res.json())
      .then(res => {
        this.setState({
          list_resource: res.data
        });
      })
      .catch(() => console.log("Error in get list"));
  }

  handleViewDetail(item) {
    this.props.handleChangeTab("detail", item);
  }

  handleEdit(item) {
    this.props.handleChangeTab("edit", item);
  }

  handleDelete(item) {
    const a = confirm("Are you sure to delete it ?");
    if (a) {
      fetch(urlDelete + "/" + item.id, {
        method: "POST",
        body: JSON.stringify(item),
        headers: {
          "Content-Type": "application/json"
        }
      })
        .then(res => res.json())
        .then(res => {
          if (res.success) {
            this.handleGetList();
          } else {
            alert("Error in Delete");
          }
        })
        .catch(() => alert("Error in Delete"));
    }
  }

  render() {
    const { list_resource } = this.state;
    return (
      <div className="row list_resource">
        <div className="col-md-12 m-t-20">
          <table class="table table-striped table-bordered">
            <thead>
              <tr>
                <th></th>
                <th>
                  <p className="">Repository name</p>
                </th>
                <th>
                  <p className="">Target Index</p>
                </th>
                <th>
                  <p className="">Base url</p>
                </th>
                <th>
                  <p className="">Status</p>
                </th>
                <th>
                  <p className="">Resync mode</p>
                </th>
                <th>
                  <p className="">Saving format</p>
                </th>
              </tr>
            </thead>
            <tbody>
              {list_resource.map((item, key) => {
                return (
                  <tr key={key}>
                    <td
                      style={{
                        display: "flex",
                        justifyContent: "space-around"
                      }}
                    >
                      <a className="icon" title="View Detail Resync">
                        <span
                          className="fa fa-eye glyphicon glyphicon-eye-open"
                          onClick={() => this.handleViewDetail(item)}
                        ></span>
                      </a>
                      <a className="icon" title="Edit Resync">
                        <span
                          className="fa fa-pencil glyphicon glyphicon-pencil"
                          onClick={() => this.handleEdit(item)}
                        ></span>
                      </a>
                      <a className="icon" title="Delete Resync">
                        <span
                          className="fa fa-trash glyphicon glyphicon-trash"
                          onClick={() => this.handleDelete(item)}
                        ></span>
                      </a>
                    </td>
                    <td>
                      {item.repository_name}
                    </td>
                    <td>
                      {item.index_name + " <ID:" + item.index_id + ">"}
                    </td>
                    <td>
                      <a
                        href={item.base_url}
                        target="_blank"
                      >
                        {item.base_url}
                      </a>
                    </td>
                    <td>
                      {item.status}
                    </td>
                    <td>
                      {item.resync_mode}
                    </td>
                    <td>
                      {item.saving_format}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    );
  }
}

class CreateResyncComponent extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      ...default_state,
      ...props.select_item,
      tree_list: []
    };
    this.handleChangeState = this.handleChangeState.bind(this);
    this.handleChangeURL = this.handleChangeURL.bind(this);
    this.handleSubmit = this.handleSubmit.bind(this);
    this.getRepositoryList = this.getRepositoryList.bind(this);
  }

  handleChangeState(name, value) {
    const { state } = this;
    this.setState(
      {
        ...state,
        [name]: value
      },
      () => {
        if (name === "repository_id") {
          this.handleChangeURL();
        }
      }
    );
  }

  handleChangeURL() {
    const { state } = this;
    const { repository_id } = state;
    const url_path = window.location.origin + "/resync/" + repository_id;
    this.handleChangeState("url_path", url_path);
  }

  handleSubmit(add_another) {
    if ((this.state.from_date || this.state.resync_mode === 'Incremental') && !moment(this.state.from_date, 'YYYY/MM/DD', true).isValid()) {
      alert(LABELS['lblResyncClientFromDate FormatErrorMsg']);
      return;
    }
    if (this.state.to_date && !moment(this.state.to_date, 'YYYY/MM/DD', true).isValid()) {
      alert(LABELS['lblResyncClientUntilDate FormatErrorMsg']);
      return;
    }
    const new_data = { ...this.state };
    delete new_data.tree_list;
    const { mode } = this.props
    const url = mode === "edit" ? urlUpdate + "/" + new_data.id : urlCreate
    fetch(url, {
      method: "POST",
      body: JSON.stringify(new_data),
      headers: {
        "Content-Type": "application/json"
      }
    })
      .then(res => res.json())
      .then(res => {
        if (res.success) {
          if (add_another) {
            this.setState({
              ...default_state
            })
          } else {
            this.props.handleChangeTab("list");
          }
        } else {
          alert(res.errmsg.join("\n"));
        }
      })
      .catch(() => alert("Error in Create"));
  }

  getRepositoryList() {
    fetch(urlGetRepositoryList, {
      method: "GET",
      headers: {
        "Content-Type": "application/json"
      }
    })
      .then(res => res.json())
      .then(res => {
        const filteredList = res.filter(item => item.value !== "Root Index");
        this.setState({
          tree_list: filteredList
        });
      })
      .catch(() => alert("Error in get Repository list"));
  }

  componentDidMount() {
    this.getRepositoryList();
    const { mode } = this.props
    initDatepicker();
    this.state.from_date = this.state.from_date ? moment(this.state.from_date).format("YYYY/MM/DD") : "";
    this.state.to_date = this.state.to_date ? moment(this.state.to_date).format("YYYY/MM/DD") : "";
    $("#from_date").val(this.state.from_date);
    $("#to_date").val(this.state.to_date);
  }

  render() {
    const { state } = this;
    const { mode } = this.props
    return (
      <div className="create-resource">
//repository_name
        <div className="row form-group flex-baseline">
          <div className="col-md-2 text-right">
            <label>Repository name</label><span className="required">*</span>
          </div>
          <div className="col-md-10">
            <input
              type="text"
              className="form-control"
              value={state.repository_name}
              name="repository_name"
              onChange={e => {
                const value = e.target.value;
                this.handleChangeState("repository_name", value);
              }}
            ></input>
          </div>
        </div>
//base_url
        <div className="row form-group flex-baseline">
          <div className="col-md-2 text-right">
            <label>Base Url</label><span className="required">*</span>
          </div>
          <div className="col-md-10">
            <input
              type="text"
              className="form-control"
              value={state.base_url}
              name="base_url"
              onChange={e => {
                const value = e.target.value;
                this.handleChangeState("base_url", value);
              }}
            ></input>
          </div>
        </div>

//status
        <div className="row form-group ">
          <div className="col-md-2 text-right">
            <label>Status</label>
          </div>
          <div className="col-md-10">
            <div className="col-md-10">
              <div className="row">
                {
                  Object.keys(status).map((item, key) => {
                    return (
                      <div className="col-md-2 flex">
                        <input
                          checked={state.status === status[item]}
                          type="radio"
                          name="status"
                          value={status[item]}
                          onChange={e => {
                            const value = e.target.value;
                            this.handleChangeState("status", value);
                          }}
                        ></input>
                        <div className="p-l-10">{status[item]}</div>
                      </div>
                    )
                  })
                }
              </div>
            </div>
          </div>
        </div>
//interval_by_day
        {
          status.automatic === state.status && (

            <div className="row form-group flex-baseline">
              <div className="col-md-2 text-right">
                <label>Interval By Day</label>
              </div>
              <div className="col-md-10">
                <input
                  type="number"
                  className="form-control"
                  value={state.interval_by_day}
                  name="interval_by_day"
                  onChange={e => {
                    let value = e.target.value;
                    value = value >= 1 ? value : 1
                    this.handleChangeState("interval_by_day", parseInt(value));
                  }}
                ></input>
              </div>
            </div>
          )
        }
        <div>
//from_date
          <div className="row form-group flex-baseline">
            <div className="col-md-2 text-right">
              <label>From Date</label>
            </div>
            <div className="col-md-10">
              <ComponentDatePicker
                component_name='from_date'
                name="from_date"
                id_component="from_date"
                date_picker_id="from_date_picker"
                error_id="from_date_error"
                onChange={this.handleChangeState}
                value={state.from_date}
              />
            </div>
          </div>
//to_date
          <div className="row form-group flex-baseline">
            <div className="col-md-2 text-right">
              <label>Until Date</label>
            </div>
            <div className="col-md-10">
              <ComponentDatePicker
                component_name='to_date'
                name="to_date"
                id_component="to_date"
                date_picker_id="to_date_picker"
                error_id="to_date_error"
                onChange={this.handleChangeState}
                value={state.to_date}
              />
            </div>
          </div>
        </div>
//index_id
        <div className="row form-group flex-baseline">
          <div className="col-md-2 text-right">
            <label>Target Index</label><span className="required">*</span>
          </div>
          <div className="col-md-10">
            <select
              className="form-control"
              onChange={e => {
                const value = e.target.value;
                this.handleChangeState("index_id", value);
              }}
              value={state.index_id}
            >
              <option value="" disabled></option>
              {state.tree_list.map(item => {
                return <option value={item.id} dangerouslySetInnerHTML={{ __html: item.value }}></option>;
              })}
            </select>
          </div>
        </div>
//resync_mode
        <div className="row form-group flex-baseline">
          <div className="col-md-2 text-right">
            <label>Resync Mode</label>
          </div>
          <div className="col-md-10">
            <select
              className="form-control"
              name="resync_mode"
              onChange={e => {
                const value = e.target.value;
                this.handleChangeState("resync_mode", value);
              }}
              value={state.resync_mode}
            >
              {Object.keys(resync_mode).map(item => {
                return <option value={resync_mode[item]}>{resync_mode[item]}</option>;
              })}
            </select>
          </div>
        </div>
//saving_format
        <div className="row form-group flex-baseline">
          <div className="col-md-2 text-right">
            <label>Saving format</label>
          </div>
          <div className="col-md-10">
            <select
              className="form-control"
              name="saving_format"
              onChange={e => {
                const value = e.target.value;
                this.handleChangeState("saving_format", value);
              }}
              value={state.saving_format}
            >
              {Object.keys(saving_format).map(item => {
                return <option value={saving_format[item]}>{saving_format[item]}</option>;
              })}
            </select>
          </div>
        </div>

        <div className="row form-group flex-baseline">
          <div className="col-md-2"></div>
          <div className="col-md-10">
            {
              mode === 'create' ? <span>
                <button
                  className="btn btn-primary"
                  onClick={() => {
                    this.handleSubmit();
                  }}
                >
                  Create
                </button>
                <button className="btn btn-default" onClick={() => {
                  this.handleSubmit(true);

                }}>
                  Create add Add Another
                </button>
              </span> : <span>
                <button
                  className="btn btn-primary"
                  onClick={() => {
                    this.handleSubmit();
                  }}
                >
                  Edit
                </button>
              </span>
            }
            <button
              className="btn btn-danger"
              onClick={() => {
                this.props.handleChangeTab("list");
              }}
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    );
  }
}

class DetailResourceComponent extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      ...default_state,
      ...props.select_item,
      logs: []
    }
    this.state.from_date = this.state.from_date ? moment(this.state.from_date).format("YYYY/MM/DD") : "";
    this.state.to_date = this.state.to_date ? moment(this.state.to_date).format("YYYY/MM/DD") : "";
  }

  handleSync() {
    const { id } = this.props.select_item
    const url = urlSync + "/" + id
    fetch(url, {
      method: "GET",
      headers: {
        "Content-Type": "application/json"
      }
    })
      .then(res => res.json())
      .then(res => {
        if (res.success) {
          alert("Sync Success")
          this.handleGetLogs()
        }
      })
      .catch(() => alert("Error in Sync"));
  }

  handleImport() {
    const { id } = this.props.select_item
    const url = urlRunResync + "/" + id
    fetch(url, {
      method: "GET",
      headers: {
        "Content-Type": "application/json"
      }
    })
      .then(res => res.json())
      .then(res => {
        alert("Import Success")
        this.handleGetLogs()
      })
      .catch(() => alert("Error in Import"));
  }

  handleGetLogs() {
    const { id } = this.props.select_item
    const url = urlGetLogs + "/" + id
    fetch(url, {
      method: "GET",
      headers: {
        "Content-Type": "application/json"
      }
    })
      .then(res => res.json())
      .then(res => {
        if (res.success) {
          this.setState({
            logs: res.logs || []
          })
          const that = this
          if (res.logs.filter(item => !item.end_time).length) {
            setTimeout(function () {
              that.handleGetLogs()
            }, 3000);
          }
        }

      })
      .catch(() => alert("Error in get logs"));
  }

  toggleRunning() {
    const { id } = this.state;
    const { is_running } = this.state;
    const url = urltoggleRunning + "/" + id
    fetch(url, {
      method: "POST",
      body: JSON.stringify({ is_running: !is_running }),
      headers: {
        "Content-Type": "application/json"
      }
    })
      .then(res => res.json())
      .then(res => {
        if (res.success) {
          this.setState({
            ...res.data
          })
        } else {
          alert(res.errmsg.join("\n"));
        }
      })
      .catch(() => alert("Error in Create"));
  }

  componentDidMount() {
    this.handleGetLogs()
  }

  render() {
    return (
      <div className="content_div">
        <div className="content_table">
          <table className="table table-hover table-bordered searchable">
            <tbody>
              <tr >
                <td><b>Repository Name</b></td>
                <td>{this.state.repository_name}</td>
              </tr>
              <tr >
                <td><b>Base Url</b></td>
                <td>{this.state.base_url}</td>
              </tr>
              <tr >
                <td><b>Status</b></td>
                <td>{this.state.status}</td>
              </tr>
              <tr >
                <td><b>Interval by Day</b></td>
                <td>{this.state.interval_by_day}</td>
              </tr>
              <tr >
                <td><b>From Date</b></td>
                <td>{this.state.from_date}</td>
              </tr>

              <tr >
                <td><b>Until Date</b></td>
                <td>{this.state.to_date}</td>
              </tr>
              <tr >
                <td><b>Target Index</b></td>
                <td>{`${this.state.index_name} < ${this.state.index_id}>`}</td>
              </tr>
              <tr >
                <td><b>Mode</b></td>
                <td>{this.state.resync_mode}</td>
              </tr>
              <tr >
                <td><b>Saving Format</b></td>
                <td>{this.state.saving_format}</td>
              </tr>
              {
                this.state.status === 'Automatic' ? (
                  <tr>
                    <td><b>Running</b></td>
                    <td><button
                      className={`btn ${this.state.is_running ? "btn-success" : "btn-danger"}`}
                      onClick={() => { this.toggleRunning() }}
                    >{this.state.is_running === true ? "ON" : "OFF"}</button></td>
                  </tr>
                ) : (
                  <tr>
                    <td><b>Action</b></td>
                    <td>
                      <button
                        className="btn btn-primary"
                        onClick={() => this.handleSync()}
                      >Sync</button>
                      {
                        this.state.resync_mode !== resync_mode.audit && <button
                          className="btn btn-primary"
                          onClick={() => this.handleImport()}
                        >Import</button>
                      }

                    </td>
                  </tr>
                )
              }

            </tbody>
          </table>
          <h3>Running logs</h3>
          <div className="content_table">
            <table className="table table-hover table-bordered searchable">
              <thead>
                <tr>
                  <th>#</th>
                  <th>{LABELS['lblResyncClientStart Time']}</th>
                  <th>{LABELS['lblResyncClientEnd Time']}</th>
                  <th>{LABELS['lblResyncClientStatus']}</th>
                  <th>{LABELS['lblResyncClientLog Type']}</th>
                  <th>{LABELS['lblResyncClientProcessed Items']}</th>
                  <th>{LABELS['lblResyncClientCreated Items']}</th>
                  <th>{LABELS['lblResyncClientUpdated Items']}</th>
                  <th>{LABELS['lblResyncClientDeleted Items']}</th>
                  <th>{LABELS['lblResyncClientError Items']}</th>
                  <th>Error Message, Url</th>
                </tr>
              </thead>
              <tbody>
                {
                  this.state.logs.map((item, key) => {
                    return (
                      <tr key={key}>
                        <td>{key + 1}</td>
                        <td>{item.start_time}</td>
                        <td>{item.end_time}</td>
                        <td>{item.status}</td>
                        <td>{item.log_type}</td>
                        <td>{item.counter.processed_items}</td>
                        <td>{item.counter.created_items}</td>
                        <td>{item.counter.updated_items}</td>
                        <td>{item.counter.deleted_items}</td>
                        <td>{item.counter.error_items}</td>
                        <td>{item.errmsg}</td>
                      </tr>
                    )
                  })
                }
              </tbody>
            </table>
          </div>
        </div>
      </div>
    );
  }
}

$(function () {
  ReactDOM.render(<MainLayout />, document.getElementById("root"));
});

class ComponentDatePicker extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      defaultClass: "controls",
      errorMessageClass: "hidden"
    }
    this.styleContainer = {
    }
    this.styleLabel = {
      "display": "inline",
    }
    this.styleDatePicker = {
      "background-color": "#fff",
    }
  }

  componentDidMount() {
    const that = this
    const { props } = this
    $("#" + this.props.id_component).change(
      function (event) {
        const value = event.target.value;
        that.props.onChange(that.props.name, value)
      }
    )
  }

  componentWillUnmount() {
    const { props } = this
    $("#" + props.id_component).off('change');
  }

  render() {
    const { props } = this
    return (
      <div style={this.styleContainer}>
        <div class={this.state.defaultClass}>
          <input
            className="form-control"
            name={props.component_name}
            id={props.id_component}
            type="text"
          />
          <div
            id={props.error_id}
            style={{ color: 'red' }}
            className={this.state.errorMessageClass}
          >Format is incorrect!</div>
        </div>
      </div>
    )
  }
}

function initDatepicker() {
  $("#from_date").datepicker({
    format: "yyyy/mm/dd",
    autoclose: true,
    forceParse: false
  })
    .on("changeDate", function (e) {
    });
  $("#to_date").datepicker({
    format: "yyyy/mm/dd",
    autoclose: true,
    forceParse: false
  })
    .on("changeDate", function (e) {
    });
}
