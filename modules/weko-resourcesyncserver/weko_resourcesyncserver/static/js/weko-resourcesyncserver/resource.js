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
          current_step: item
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

              {tab === tabs[0].tab_key ? <div>
                <ListResourceComponent>
                  handleChangeTab={this.handleChangeTab}
                ></ListResourceComponent>
              </div> : ''}

              {tab === tabs[1].tab_key ? <div>
                <CreateResourceComponent>
                  handleChangeTab={this.handleChangeTab}
                ></CreateResourceComponent>
              </div> : ''}

              {tab === tabs[2].tab_key ? <div>
                <EditResourceComponent>
                  handleChangeTab={this.handleChangeTab}
                ></EditResourceComponent>
              </div> : ''}

              {tab === tabs[3].tab_key ? <div>
                <DetailResourceComponent>
                  handleChangeTab={this.handleChangeTab}
                ></DetailResourceComponent>
              </div> : ''}

            </div>
        )
    }
}

class ListResourceComponent extends React.Component {
  constructor(){
    super()
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


class CreateResourceComponent extends React.Component {
  constructor(){
    super()
    this.state = {

    }
  }

  render(){
    return(
      <div>
        Create ne
      </div>
    )
  }
}


class EditResourceComponent extends React.Component {
  constructor(){
    super()
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
  constructor(){
    super()
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
