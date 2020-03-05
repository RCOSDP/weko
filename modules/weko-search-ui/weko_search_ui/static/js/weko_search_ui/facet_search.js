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
  "Center for Social Research and Data Archives, Institute of Social Science, University of Tokyo": document.getElementById("Center for Social Research and Data Archives, Institute of Social Science, University of Tokyo").value,
  "Institute of Economic Research, Hitotsubashi University": document.getElementById("Institute of Economic Research, Hitotsubashi University").value,
  "Panel Data Research Center at Keio University": document.getElementById("Panel Data Research Center at Keio University").value,
  "Japanese General Social Surveys, Osaka University of Commerce": document.getElementById("Japanese General Social Surveys, Osaka University of Commerce").value,
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
  }

  get_facet_search_list() {
    let url = new URL(window.location.href)
    url.pathname = '/api/records/'
    if (url.searchParams.has('search_type') && String(url.searchParams.get('search_type')) === "2") {
      url.pathname = '/api/index/'
    }
    fetch(url.href, {
      method: "GET",
      headers: {
        "Content-Type": "application/json"
      }
    })
      .then(res => res.json())
      .then(res => {
        if (url.searchParams.has('search_type') && String(url.searchParams.get('search_type')) === "2") {
//          Index faceted search
          this.convertData(res && res.aggregations && res.aggregations.path && res.aggregations.path.buckets && res.aggregations.path.buckets[0] ? res.aggregations.path.buckets[0] : {})
        }
        else {
//          default faceted search
          this.convertData(res && res.aggregations ? res.aggregations : {})
        }
      })
      .catch(() => alert("Error in get list"));
  }

  convertData(data) {
    const list_name_facet = ["accessRights", "dataType", "distributor", "language"]
    let new_data = {}
    Object.keys(data).map((name, k) => {
      if (list_name_facet.includes(name)) {
        let item = data[name]
        if (item[name]) {
          item = item[name]
        }
        new_data[name] = item
      }
    })
    this.setState({
      list_facet: new_data
    })
  }

  componentDidMount() {
    this.get_facet_search_list()
  }

  handleCheck(params, value) {
    let url = new URL(window.location.href)
    if (url.searchParams.has(params) && url.searchParams.getAll(params).includes(value)) {
      let new_value = url.searchParams.getAll(params).filter(i => i !== value)
      url.searchParams.delete(params)
      new_value.map(v => { url.searchParams.append(params, v) })
    } else {
      url.searchParams.append(params, value)
    }
    let new_url = new URL(window.location.origin + "/search")
    new_url.search = url.search;
    window.location.href = new_url.href
  }

  render() {
    const { is_enable, list_facet } = this.state
    const url = new URL(window.location.href)
    return (
      <div>
        {is_enable && <div className="facet-search">
          {
            Object.keys(list_facet).map((name, key) => {
              const item = list_facet[name]
              return (
                <div className="panel panel-default" key={key}>
                  <div className="panel-heading clearfix">
                    <h3 className="panel-title">{label[name]}</h3>
                  </div>
                  <div className="panel-body index-body">
                    {
                      item.buckets && item.buckets.map((subitem, k) => {
                        const value = url.searchParams.getAll(name).includes(subitem.key) ? true : false
                        return (
                          <label>
                            <input
                              type="checkbox"
                              defaultChecked={value}
                              onChange={() => { this.handleCheck(name, subitem.key) }}
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
