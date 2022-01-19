const LABELS = {};

class MainLayout extends React.Component {

  constructor(props) {
    super(props);
    this.state = {
      is_enable: true,
      list_title: {},
      list_facet: {}
    }
    this.getTitle = this.getTitle.bind(this);
    this.get_facet_search_list = this.get_facet_search_list.bind(this);
    this.handleCheck = this.handleCheck.bind(this);
    this.convertData = this.convertData.bind(this);
    this.getUrlVars = this.getUrlVars.bind(this);
    //this.get_display_control = this.get_display_control.bind(this);
  }

/*   get_display_control() {
    let url = '/api/admin/search_control/display_control';
    //let weko_show_index_for_authenticated_user = document.getElementById("weko_show_index_for_authenticated_user").value
    $.ajax({
        context: this,
        url: url,
        type: 'GET',
        contentType: 'application/json; charset=UTF-8',
        success: function (res) {
            if (res) {
               const data = JSON.parse(res);
               if (data.display_facet_search) {
                  this.setState({is_enable: data.display_facet_search.status});
               }

               if (data.display_index_tree && !data.display_index_tree.status || weko_show_index_for_authenticated_user === "True") {
                  $("#body_index").hide()
                  $("#body_indexlink").hide()
                  $("#body_indexlist").hide()
               }
            }
        },
        error: function() {
          console.log("Error in get list");
        }
    });
  } */
  getTitle() {
    let listtitle = {};
    $.ajax({
      context: this,
      url: '/facet-search/get-title',
      type: 'POST',
      success: function (response) {
        if (response.status) {
          listtitle = response.data;
        }
        this.setState({list_title: listtitle});
      },
      error: function () {
        console.log("Error in get list")
      }
    });
  }

  get_facet_search_list() {
    let search = window.location.search;
    let url = '/api/records/';
    let params = this.getUrlVars();
    if (params.search_type && String(params.search_type) === "2") {
      url = '/api/index/';
    }
    $.ajax({
      context: this,
      url: url + search,
      type: 'GET',
      contentType: 'application/json; charset=UTF-8',
      success: function (res) {
        if (params.search_type && String(params.search_type) === "2") {
          // Index faceted search
          const data = res && res.aggregations && res.aggregations.path && res.aggregations.path.buckets && res.aggregations.path.buckets[0] ? res.aggregations.path.buckets[0] : {}
          this.convertData(data && data[0] ? data[0] : {})
        } else {
          // default faceted search
          this.convertData(res && res.aggregations ? res.aggregations : {})
        }
      },
      error: function () {
        console.log("Error in get list")
      }
    });
  }

  getUrlVars() {
    let vars = {};
    let pattern = /[?&]+([^=&]+)=([^&]*)/gi;
    window.location.href.replace(pattern, function (m, key, value) {
      vars[key] = value;
    });
    return vars;
  }

  convertData(data) {
    let list_facet = {};
    if (data) {
      Object.keys(data).map(function (name, k) {
        let val = data[name][name] ? data[name][name] : data[name];
        let hasBuckets = val['key'] && val['key'].hasOwnProperty('buckets');
        hasBuckets = val.hasOwnProperty('buckets') || hasBuckets;
        if (hasBuckets) {
          list_facet[name] = val[name] ? val[name] : val;
        }
      })
    }
    this.setState({list_facet: list_facet});
  }

  componentDidMount() {
    this.getTitle();
    this.get_facet_search_list();
  }

  handleCheck(params, value) {
    let search = window.location.search.replace(',', '%2C') || "?"
    let pattern = encodeURIComponent(params) + "=" + encodeURIComponent(value)
    if (search.indexOf(pattern) >= 0) {
      search = search.replace("&"+ pattern ,"")
      search = search.replace(pattern ,"")
    } else {
      search+= "&" + pattern
    }
    window.location.href = "/search"+ search;
  }

  render() {
    const { is_enable, list_title, list_facet } = this.state;
    const search = window.location.search.replace(',', '%2C');
    const that = this;
    return (
      <div>
        {is_enable && <div className="facet-search break-word">
          {
            Object.keys(list_facet).map(function (name, key) {
              const item = list_facet[name];
              return (
                <div className="panel panel-default" key={key}>
                  <div className="panel-heading clearfix">
                    <h3 className="panel-title">{list_title[name]}</h3>
                  </div>
                  <div className="panel-body index-body">
                    {
                      item.buckets && item.buckets.map(function (subitem, k) {
                        const pattern = encodeURIComponent(name) + "=" + encodeURIComponent(subitem.key);
                        const value = search.indexOf(pattern) >= 0 ? true : false;
                        return (
                          <label>
                            <input type="checkbox" defaultChecked={value}
                              onChange={function () {
                                that.handleCheck(name, subitem.key)
                              }}
                            ></input>
                            {LABELS[subitem.key] || subitem.key}({subitem.doc_count})
                          </label>
                        )
                      })
                    }
                  </div>
                </div>
              )
            })
          }
        </div>}
      </div>
    )
  }
}

$(function () {
  //Get all labels.
  let labels = document.getElementsByClassName('body-facet-search-label');
  for (let i = 0; i < labels.length; i++) {
    LABELS[labels[i].id] = labels[i].value;
  }
  ReactDOM.render(
    <MainLayout />,
    document.getElementById('app-facet-search')
  )
});
