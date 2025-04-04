const list_label = "List";
const create_label = "Create";
const edit_label = "Edit";
const urlCreate = window.location.origin + "/admin/resource_list/create";
const urlUpdate = window.location.origin + "/admin/resource_list/update";
const urlDelete = window.location.origin + "/admin/resource_list/delete";
const urlGetList = window.location.origin + "/admin/resource_list/get_list";
const urlGetTreeList = window.location.origin + "/api/tree";
const urlGetRepositoryList = window.location.origin + "/admin/resync/get_repository";
const default_state = {
  status: null,
  repository_id: "",
  resource_dump_manifest: false,
  url_path: ""
};

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
        }
      ]
    };
    this.handleChangeTab = this.handleChangeTab.bind(this);
  }

  componentDidMount() { }

  handleChangeTab(select_tab, select_item = {}) {
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
            <ListResourceComponent
              handleChangeTab={this.handleChangeTab}
            ></ListResourceComponent>
          </div>
        ) : (
          ""
        )}

        {current_tab === tabs[1].tab_key ? (
          <div>
            <CreateResourceComponent
              handleChangeTab={this.handleChangeTab}
            ></CreateResourceComponent>
          </div>
        ) : (
          ""
        )}

        {current_tab === tabs[2].tab_key ? (
          <div>
            <EditResourceComponent
              handleChangeTab={this.handleChangeTab}
              select_item={select_item}
            ></EditResourceComponent>
            {/* </div> : ''} */}
          </div>
        ) : (
          ""
        )}
      </div>
    );
  }
}

class ListResourceComponent extends React.Component {
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
          list_resource: res
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
                  <p className="">Repository</p>
                </th>
                <th>
                  <p className="">Resource List Url</p>
                </th>
                <th>
                  <p className="">Resource Dump Url</p>
                </th>
                <th>
                  <p className="">Status</p>
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
                      <a className="icon" title="Edit Resource">
                        <span
                          className="fa fa-pencil glyphicon glyphicon-pencil"
                          onClick={() => this.handleEdit(item)}
                        ></span>
                      </a>
                      <a className="icon" title="Delete Resource">
                        <span
                          className="fa fa-trash glyphicon glyphicon-trash"
                          onClick={() => this.handleDelete(item)}
                        ></span>
                      </a>
                    </td>
                    <td>
                      {item.repository_name + " <ID:" + item.repository_id + ">"}
                    </td>
                    <td>
                      <a
                        href={item.url_path + "/resourcelist.xml"}
                        target="_blank"
                      >
                        {item.url_path + "/resourcelist.xml"}
                      </a>
                    </td>
                    <td>
                      <a
                        href={item.url_path + "/resourcedump.xml"}
                        target="_blank"
                      >
                        {item.url_path + "/resourcedump.xml"}
                      </a>
                    </td>
                    <td>{item.status ? "Publish" : "Private"}</td>
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

class CreateResourceComponent extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      ...default_state,
      tree_list: []
    };
    this.handleChangeState = this.handleChangeState.bind(this);
    this.handleChangeURL = this.handleChangeURL.bind(this);
    this.handleSubmit = this.handleSubmit.bind(this);
    this.getReositoryList = this.getRepositoryList.bind(this);
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
    const new_data = { ...this.state };
    delete new_data.tree_list;
    fetch(urlCreate, {
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
          alert(res.message);
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
        this.setState({
          tree_list: res
        });
      })
      .catch(() => alert("Error in get Repository list"));
  }

  componentDidMount() {
    this.getRepositoryList();
  }

  render() {
    const { state } = this;
    return (
      <div className="create-resource">
        <div className="row form-group ">
          <div className="col-md-2 text-right">
            <label>Status</label>
          </div>
          <div className="col-md-10">
            <div className="col-md-10">
              <div className="row">
                <div className="col-md-2 flex">
                  <input
                    checked={state.status === true}
                    type="radio"
                    name="status"
                    value="Publish"
                    onChange={e => {
                      const value = e.target.value;
                      this.handleChangeState("status", value === "Publish");
                    }}
                  ></input>
                  <div className="p-l-10">Publish</div>
                </div>
                <div className="col-md-2 flex">
                  <input
                    checked={state.status === false}
                    type="radio"
                    name="status"
                    value="Private"
                    onChange={e => {
                      const value = e.target.value;
                      this.handleChangeState("status", value === "Publish");
                    }}
                  ></input>
                  <div className="p-l-10">Private</div>
                </div>


              </div>
            </div>
          </div>
        </div>

        <div className="row form-group flex-baseline">
          <div className="col-md-2 text-right">
            <label>Repository</label>
          </div>
          <div className="col-md-10">
            <select
              className="form-control"
              onChange={e => {
                const value = e.target.value;
                this.handleChangeState("repository_id", value);
              }}
              value={state.repository_id}
            >
              <option value="" disabled></option>

              {state.tree_list.map(item => {
                return <option value={item.id} dangerouslySetInnerHTML={{ __html: item.value }}></option>;
              })}
            </select>
          </div>
        </div>

        <div className="row form-group flex-baseline">
          <div className="col-md-2 text-right">
            <label>Resource Dump Manifest</label>
          </div>
          <div className="col-md-10">
            <input
              type="checkbox"
              checked={state.resource_dump_manifest}
              onChange={e => {
                const value = e.target.checked;
                this.handleChangeState("resource_dump_manifest", value);
              }}
            ></input>
          </div>
        </div>

        <div className="row form-group flex-baseline">
          <div className="col-md-2 text-right">
            <label>Resource List uri</label>
          </div>
          <div className="col-md-10">
            <input
              type="text"
              className="form-control"
              disabled
              value={state.url_path && state.url_path + "/resourcelist.xml"}
            ></input>
          </div>
        </div>

        <div className="row form-group flex-baseline">
          <div className="col-md-2 text-right">
            <label>Resource Dump uri</label>
          </div>
          <div className="col-md-10">
            <input
              type="text"
              className="form-control"
              disabled
              value={state.url_path && state.url_path + "/resourcedump.xml"}
            ></input>
          </div>
        </div>

        <div className="row form-group flex-baseline">
          <div className="col-md-2"></div>
          <div className="col-md-10">
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

class EditResourceComponent extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      ...props.select_item,
      tree_list: [],
    };
    this.handleChangeState = this.handleChangeState.bind(this);
    this.handleChangeURL = this.handleChangeURL.bind(this);
    this.handleSubmit = this.handleSubmit.bind(this);
    this.getReositoryList = this.getRepositoryList.bind(this);
  }

  handleChangeState(name, value) {
    const { state } = this;
    this.setState(
      {
        ...state,
        [name]: value
      }, () => {
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

  handleSubmit() {
    const new_data = { ...this.state };
    delete new_data.tree_list;
    delete new_data.id;
    fetch(urlUpdate + "/" + this.state.id, {
      method: "POST",
      body: JSON.stringify(new_data),
      headers: {
        "Content-Type": "application/json"
      }
    })
      .then(res => res.json())
      .then(res => {
        if (res.success) {
          this.props.handleChangeTab("list");
        } else {
          alert(res.message);
        }
      })
      .catch(() => alert("Error in Edit"));
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
        this.setState({
          tree_list: res
        });
      })
      .catch(() => alert("Error in get Repository list"));
  }

  componentDidMount() {
    this.getRepositoryList();
    const { select_item } = this.props;
    this.setState({
      ...select_item,
    });
  }

  render() {
    const { state } = this;
    return (
      <div className="create-resource">
        <div className="row form-group">
          <div className="col-md-2 text-right">
            <label>Status</label>
          </div>
          <div className="col-md-10">
            <div className="row">
              <div className="col-md-2 flex">
                <input
                  checked={state.status}
                  type="radio"
                  name="status"
                  value="Publish"
                  onChange={e => {
                    const value = e.target.value;
                    this.handleChangeState("status", value === "Publish");
                  }}
                ></input>
                <div className="p-l-10">Publish</div>
              </div>
              <div className="col-md-2 flex">
                <input
                  checked={!state.status}
                  type="radio"
                  name="status"
                  value="Private"
                  onChange={e => {
                    const value = e.target.value;
                    this.handleChangeState("status", value === "Publish");
                  }}
                ></input>
                <div className="p-l-10">Private</div>
              </div>


            </div>
          </div>
        </div>

        <div className="row form-group flex-baseline">
          <div className="col-md-2 text-right">
            <label>Repository</label>
          </div>
          <div className="col-md-10">
            <select
              className="form-control"
              onChange={e => {
                const value = e.target.value;
                this.handleChangeState("repository_id", value);
              }}
              value={state.repository_id}
            >
              {state.tree_list.map(item => {
                return <option value={item.id} dangerouslySetInnerHTML={{ __html: item.value }}></option>;
              })}
            </select>
          </div>
        </div>

        <div className="row form-group flex-baseline">
          <div className="col-md-2 text-right">
            <label>Resource Dump Manifest</label>
          </div>
          <div className="col-md-10">
            <input
              type="checkbox"
              onChange={e => {
                const value = e.target.checked;
                this.handleChangeState("resource_dump_manifest", value);
              }}
              checked={state.resource_dump_manifest}
            ></input>
          </div>
        </div>

        <div className="row form-group flex-baseline">
          <div className="col-md-2 text-right">
            <label>Resource List uri</label>
          </div>
          <div className="col-md-10">
            <input
              type="text"
              className="form-control"
              disabled
              value={state.url_path && state.url_path + "/resourcelist.xml"}
            ></input>
          </div>
        </div>

        <div className="row form-group flex-baseline">
          <div className="col-md-2 text-right">
            <label>Resource Dump uri</label>
          </div>
          <div className="col-md-10">
            <input
              type="text"
              className="form-control"
              disabled
              value={state.url_path && state.url_path + "/resourcedump.xml"}
            ></input>
          </div>
        </div>

        <div className="row form-group flex-baseline">
          <div className="col-md-2"></div>
          <div className="col-md-10">
            <button
              className="btn btn-primary"
              onClick={() => {
                this.handleSubmit();
              }}
            >
              Save
            </button>
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
    this.state = {};
  }

  render() {
    return <div>Deatil ne</div>;
  }
}
$(function () {
  ReactDOM.render(<MainLayout />, document.getElementById("root"));
});
