const list_label = "List"
const create_label = "Create"
const edit_label = "Edit"
const detail_label = "Detail"


class MainLayout extends React.Component {

    constructor(props) {
        super(props);
        this.state = {
          current_step: 1,
          current_tab: 'list',
          tabs: [
            {
              tab_key: 'list',
              tab_name: list_label,
              step: 1
            },
            {
              tab_key: 'create',
              tab_name: create_label,
              step: 1

            },
            {
              tab_key: 'edit',
              tab_name: edit_label,
              step: 2,
            },
            {
              tab_key: 'detail',
              tab_name: detail_label,
              step: 2,
            }
          ],
        }
        this.handleChangeTab = this.handleChangeTab.bind(this)

    }

    componentDidMount() {
    }

    handleChangeTab(select_tab, select_item = {}) {
      const { tabs } = this.state
      const a = tabs.filter(item => {
        return item.tab_key === select_tab
      })
      if (a[0]) {
        const item = a[0]
        this.setState({
          current_tab: item.tab_key,
          current_step: item.step
        })
        if(select_item){
          this.setState({
            select_item: select_item,
          })
        }
      }
    }


    render() {
        const { tabs, current_step, current_tab } = this.state
        return (
            <div className="resource row">
              <ul className="nav nav-tabs">
                {
                  tabs.map((item, key) => {
                    if (item.step <= current_step){
                      return (
                        <li role="presentation" className={`${item.tab_key === current_tab ? 'active' : ''}`} onClick={() => this.handleChangeTab(item.tab_key)}><a href="#">{item.tab_name}</a></li>
                      )
                    }
                  })
                }
              </ul>

              {current_tab === tabs[0].tab_key ? <div>
                <ListResourceComponent
                  handleChangeTab={this.handleChangeTab}
                ></ListResourceComponent>
              </div> : ''}

              {current_tab === tabs[1].tab_key ? <div>
                <CreateResourceComponent
                  handleChangeTab={this.handleChangeTab}
                ></CreateResourceComponent>
              </div> : ''}

              {current_tab === tabs[2].tab_key ? <div>
                <EditResourceComponent
                  handleChangeTab={this.handleChangeTab}
                ></EditResourceComponent>
              </div> : ''}

              {current_tab === tabs[3].tab_key ? <div>
                <DetailResourceComponent
                  handleChangeTab={this.handleChangeTab}
                ></DetailResourceComponent>
              </div> : ''}

            </div>
        )
    }
}

class ListResourceComponent extends React.Component {
  constructor(props){
    super(props)
    this.state = {

    }
  }

  render(){
    return(
      <div>
        List ne
      </div>
    )
  }
}

const default_state = {
  status: false,
  repository: '',
  resource_dump_manifest: false,
  url_path: ''
}

class CreateResourceComponent extends React.Component {
  constructor(props){
    super(props)
    this.state = {
      ...default_state
    }
    this.handleChangeState = this.handleChangeState.bind(this)
    this.handleChangeURL = this.handleChangeURL.bind(this)
  }

  handleChangeState(name, value) {
    const {state} = this
    this.setState({
      current_state: {
        ...state,
        [name]: value
      }
    },() => {
      if (name === 'repository'){
        this.handleChangeURL()
      }
    })
  }

  handleChangeURL(){
    const {state} = this
    const {repository} = state
    url_path = window.location.origin + '/resource/'+ repository
    this.handleChangeState('url_path',url_path)
  }

  render(){
    const {state} = this
    return(
      <div className="create-resource">

        <div className="row form-group flex-baseline">
          <div className="col-md-4 text-right">
            <label>Status</label>
          </div>
          <div className="col-md-8">
            <input type="checkbox" onChange={(e) => {
              const value = e.target.checked
              this.handleChangeState('status', value)
            }}></input>
          </div>
        </div>

        <div className="row form-group flex-baseline">
          <div className="col-md-4 text-right">
            <label>Repository</label>
          </div>
          <div className="col-md-8">
            <select className="form-control"
              onChange={(e) => {
                const value = e.target.value
                this.handleChangeState('repository', value)
              }}
            >
              <option value="1">Large 1</option>
              <option value="2">Large 2</option>
              <option value="3">Large 3</option>
              <option value="4">Large 4</option>
            </select>
          </div>
        </div>

        <div className="row form-group flex-baseline">
          <div className="col-md-4 text-right">
            <label>Resource Dump Manifest</label>
          </div>
          <div className="col-md-8">
            <input
              type="checkbox"
              onChange={(e) => {
                const value = e.target.checked
                this.handleChangeState('resource_dump_manifest', value)
              }}
            ></input>
          </div>
        </div>

        <div className="row form-group flex-baseline">
          <div className="col-md-4 text-right">
            <label>Resource List uri</label>
          </div>
          <div className="col-md-8">
            <input type="text" className="form-control" disabled></input>
          </div>
        </div>

        <div className="row form-group flex-baseline">
          <div className="col-md-4 text-right">
            <label>Resource Dump uri</label>
          </div>
          <div className="col-md-8">
            <input type="text" className="form-control" disabled></input>
          </div>
        </div>

        <div className="row form-group flex-baseline">
          <div className="col-md-4 text-right">
            <label>Auto start after save</label>
          </div>
          <div className="col-md-8">
            <input type="checkbox"></input>
          </div>
        </div>

        <div className="row form-group flex-baseline">
          <div className="col-md-4">
          </div>
          <div className="col-md-8">
            <button
                  className="btn btn-primary"
                  onClick={() => { this.props.handleChangeTab('list') }}
                >
                  Save
             </button>
             <button
                  className="btn btn-default"
                  onClick={() => {  }}
                >
                  Save add Add Another
             </button>
             <button
                  className="btn btn-danger"
                  onClick={() => { this.props.handleChangeTab('edit') }}
                >
                  Cancel
             </button>
          </div>
        </div>
      </div>
    )
  }
}


class EditResourceComponent extends React.Component {
  constructor(props){
    super(props)
    this.state = {

    }
  }

  render(){
    return(
      <div>
        Edit ne
      </div>
    )
  }
}


class DetailResourceComponent extends React.Component {
  constructor(props){
    super(props)
    this.state = {

    }
  }

  render(){
    return(
      <div>
        Deatil ne
      </div>
    )
  }
}
$(function () {
    ReactDOM.render(
        <MainLayout />,
        document.getElementById('root')
    )
});
