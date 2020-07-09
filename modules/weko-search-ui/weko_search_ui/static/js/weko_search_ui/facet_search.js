const urlGetDataFacet = "/api/records/?size=0"

const label = {
  "accessRights": document.getElementById("accessRights").value,
  "open access": document.getElementById("open access").value,
  "restricted access": document.getElementById("restricted access").value,
  "metadata only access": document.getElementById("metadata only access").value,
  "embargoed access": document.getElementById("embargoed access").value,
  "language": document.getElementById("language").value,
  "distributor": document.getElementById("distributor").value,
  "dataType": document.getElementById("dataType").value,
  "zho": document.getElementById("zho").value,
  "cmn": document.getElementById("cmn").value,
  "eng": document.getElementById("eng").value,
  "fra": document.getElementById("fra").value,
  "deu": document.getElementById("deu").value,
  "jpn": document.getElementById("jpn").value,
  "kor": document.getElementById("kor").value,
  "rus": document.getElementById("rus").value,
  "Social Science Japan Data Archive (SSJDA)": document.getElementById("Social Science Japan Data Archive (SSJDA)").value,
  "Institute of Economic Research, Hitotsubashi University": document.getElementById("Institute of Economic Research, Hitotsubashi University").value,
  "Panel Data Research Center at Keio University": document.getElementById("Panel Data Research Center at Keio University").value,
  "JGSS Research Center": document.getElementById("JGSS Research Center").value,
  "Historiographical Institute The University of Tokyo": document.getElementById("Historiographical Institute The University of Tokyo").value,

}

class MainLayout extends React.Component {

  constructor() {
    super()
    this.state = {
      is_enable: true,
      list_facet: {}
    }
    this.get_facet_search_list = this.get_facet_search_list.bind(this)
    this.handleCheck = this.handleCheck.bind(this)
    this.convertData = this.convertData.bind(this)
    this.getUrlVars = this.getUrlVars.bind(this)
    this.get_display_control = this.get_display_control.bind(this)
  }

  get_display_control() {
    let url = '/api/admin/search_control/display_control'
    $.ajax({
        context: this,
        url: url,
        type: 'GET',
        contentType: 'application/json; charset=UTF-8',
        success: function (res) {
            if (res) {
               const data = JSON.parse(res)
               if (data.display_facet_search) {
                  this.setState({is_enable: data.display_facet_search.status})
               }
               if (data.display_index_tree && !data.display_index_tree.status) {
                  $("#body_index").hide()
               }
            }

        },
        error: function() {
          alert("Error in get list")
        }
    });
  }

  get_facet_search_list() {
    let search = window.location.search
    let url = '/api/records/'
    let params = this.getUrlVars()
    if (params.search_type && String(params.search_type) === "2") {
      url = '/api/index/'
    }
    $.ajax({
        context: this,
        url: url+ search,
        type: 'GET',
        contentType: 'application/json; charset=UTF-8',
        success: function (res) {
            if (params.search_type && String(params.search_type) === "2") {
    //          Index faceted search
              const data = res && res.aggregations && res.aggregations.path && res.aggregations.path.buckets && res.aggregations.path.buckets[0] ? res.aggregations.path.buckets[0] : {}
              this.convertData(data && data[0] ? data[0] : {})
            }
            else {
    //          default faceted search
              this.convertData(res && res.aggregations ? res.aggregations : {})
            }
        },
        error: function() {
          alert("Error in get list")
        }
    });
  }

  getUrlVars() {
    var vars = {};
    var parts = window.location.href.replace(/[?&]+([^=&]+)=([^&]*)/gi, function(m,key,value) {
        vars[key] = value;
    });
    return vars;
}

  convertData(data) {
    const list_name_facet = ["accessRights", "dataType", "distributor", "language"]
    let new_data = {
        accessRights : {},
        dataType : {},
        distributor : {},
        language : {}
      }
    if (data) {
      Object.keys(data).map(function (name, k)  {
        if (list_name_facet.indexOf(name)>=0) {
          let item = data[name]
          if (item[name]) {
            item = item[name]
          }
          new_data[name] = item
        }
      })
    }

    this.setState({
      list_facet: new_data
    })
  }

  componentDidMount() {
      this.get_display_control()
      this.get_facet_search_list()
  }

  handleCheck(params, value) {
    let search = window.location.search || "?"
    let pattern = encodeURIComponent(params) + "=" + encodeURIComponent(value)
    if (search.indexOf(pattern) >= 0) {
      search = search.replace("&"+ pattern ,"")
      search = search.replace(pattern ,"")
    } else {
      search+= "&" + pattern
    }
    window.location.href = "/search"+ search
  }

  render() {
    const { is_enable, list_facet } = this.state
    const search = window.location.search
    const that = this
    return (
      <div>
        {is_enable && <div className="facet-search break-word">
          {
            Object.keys(list_facet).map(function(name, key) {
              const item = list_facet[name]
              return (
                <div className="panel panel-default" key={key}>
                  <div className="panel-heading clearfix">
                    <h3 className="panel-title">{label[name]}</h3>
                  </div>
                  <div className="panel-body index-body">
                    {
                      item.buckets && item.buckets.map(function(subitem, k) {
                        const pattern = encodeURIComponent(name) + "=" + encodeURIComponent(subitem.key)
                        const value = search.indexOf(pattern) >=0 ? true : false
                        return (
                          <label>
                            <input
                              type="checkbox"
                              defaultChecked={value}
                              onChange={function() { that.handleCheck(name, subitem.key) }}
                            ></input>
                            {label[subitem.key] || subitem.key}({subitem.doc_count})
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
  ReactDOM.render(
    <MainLayout />,
    document.getElementById('app-facet-search')
  )
});
