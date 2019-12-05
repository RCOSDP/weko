const import_label = document.getElementById("import").value;
const list = document.getElementById("list").value;
const import_file = document.getElementById("import_file").value;
const import_index = document.getElementById("import_index").value;
const work_flow = document.getElementById("work_flow").value;
const select_file = document.getElementById("select_file").value;
const select_index = document.getElementById("select_index").value;
const select_work_flow = document.getElementById("select_work_flow").value;
const selected_file_name = document.getElementById("selected_file_name").value;
const selected_index = document.getElementById("selected_index").value;
const selected_work_flow = document.getElementById("selected_work_flow").value;
const index_tree = document.getElementById("index_tree").value;
const designate_index = document.getElementById("designate_index").value;
const work_flow_2 = document.getElementById("work_flow_2").value;
const item_type = document.getElementById("item_type").value;
const flow = document.getElementById("flow").value;
const select = document.getElementById("select").value;
const cancel = document.getElementById("cancel").value;
const check = document.getElementById("check").value;
// label check
const summary = document.getElementById("summary").value;
const total_label = document.getElementById("total").value;
const new_item_label = document.getElementById("new_item").value;
const update_item_label = document.getElementById("update_item").value;
const check_error_label = document.getElementById("check_error").value;
const download = document.getElementById("download").value;
const no = document.getElementById("no").value;
const item_id = document.getElementById("item_id").value;
const title = document.getElementById("title").value;
const check_result = document.getElementById("check_result").value;
const error = document.getElementById("error").value;
const update = document.getElementById("update").value;
const not_match = document.getElementById("not_match").value;
const register = document.getElementById("register").value;


const workflows = JSON.parse($("#workflows").text() ? $("#workflows").text() : "");
const urlTree = window.location.origin+'/api/tree'
const urlCheck = window.location.origin+'/admin/items/import/check'
const urlDownload = window.location.origin+'/admin/items/import/download'
const urlImport = window.location.origin+'/admin/items/import/import'

class MainLayout extends React.Component {

  constructor(){
    super()
    this.state = {
      tab: 'import',
      tabs: [
        {
          tab_key: 'import',
          tab_name: import_label
        },
        {
          tab_key: 'check',
          tab_name: check,
        },
        {
          tab_key: 'list',
          tab_name: list
        }
      ],
      list_record: [],
      is_import: true
    }
    this.handleChangeTab = this.handleChangeTab.bind(this)
    this.handleCheck = this.handleCheck.bind(this)
    this.handleImport = this.handleImport.bind(this)
    this.getStatus = this.getStatus.bind(this)
  }

  handleChangeTab(tab) {
    this.setState({
      tab: tab
    })
  }

  componentDidMount() {
  }

  handleCheck(data){
    const that = this
    $.ajax({
      url: urlCheck,
      type: 'POST',
      data: JSON.stringify(data),
      contentType: "application/json; charset=utf-8",
      dataType: "json",
      success: function (response) {
        if (response.code) {
          that.setState(()=>{
            return {
              list_record: response.list_record,
              root_path: response.data_path,
              is_import: false
            }
          })
          that.handleChangeTab('check');
        } else {
          console.log(response.msg);
          alert(response.error || '')
        }
      },
      error: function (error) {
        console.log(error);
      }
    });
  }

  handleImport() {
    const{list_record, root_path,is_import} = this.state
    const that = this
    if (is_import){
      return
    }
    this.setState({
      is_import: true
    })
    $.ajax({
      url: urlImport,
      type: 'POST',
      data: JSON.stringify({
        list_record,
        root_path
      }),
      contentType: "application/json; charset=utf-8",
      dataType: "json",
      success: function (response) {
        console.log(response)
        console.log(root_path)

          that.handleChangeTab('list');
          const mess = 'Import success :'+response.success+'\n'+ "Import failure :"+ response.failure_list
          alert(mess)
//          that.getStatus(response.data.task_id)
      },
      error: function (error) {
        console.log(error);
      }
    });
  }

  getStatus(taskID) {
    const that = this
    $.ajax({
      url: urlImport+'/'+taskID,
      method: 'GET'
    })
    .done((res) => {
      console.log(res)
      const html = `
      <tr>
        <td>${res.data.task_id}</td>
        <td>${res.data.task_status}</td>
        <td>${res.data.task_result}</td>
      </tr>`
      $('#tasks').prepend(html);
      const taskStatus = res.data.task_status;
      if (taskStatus === 'finished' || taskStatus === 'failed') return false;
      setTimeout(function() {
        that.getStatus(res.data.task_id);
      }, 1000);
    })
    .fail((err) => {
      console.log(err);
    });
  }

  render() {
    const {tab, tabs, list_record,is_import} = this.state
    return(
      <div>
        <ul className="nav nav-tabs">
          {
            tabs.map((item,key)=>{
              return(
                <li role="presentation" className={`${item.tab_key===tab ? 'active' : ''}`} onClick={()=>this.handleChangeTab(item.tab_key)}><a href="#">{item.tab_name}</a></li>
              )
            })
          }
        </ul>
        <div className={`${tab === tabs[0].tab_key ? '': 'hide'}`}>
          <ImportComponent
            handleCheck={this.handleCheck}
           ></ImportComponent>
        </div>
        <div className={`${tab === tabs[1].tab_key ? '': 'hide'}`}>
          <CheckComponent
            list_record={list_record || []}
            handleImport={this.handleImport}
            is_import={is_import}
          ></CheckComponent>
        </div>
        <div className={`${tab === tabs[2].tab_key ? '': 'hide'}`}>
        </div>
      </div>
    )
  }
}

class ImportComponent extends React.Component {

    constructor(){
      super()
      this.state = {
        file: null,
        file_name: "",
        isShowModalWF: false,
        work_flow_data : null,
        wl_key: null,
        isShowModalIndex: false,
        list_index: [],
        term_select_index_list: [],
        select_index_list: [],
        isShowModalImport: false
      }
      this.handleChangefile = this.handleChangefile.bind(this)
      this.handleClickFile = this.handleClickFile.bind(this)
      this.getLastString = this.getLastString.bind(this)
      this.handleShowModalWorkFlow = this.handleShowModalWorkFlow.bind(this)
      this.handleChangeWF = this.handleChangeWF.bind(this)
      this.handleShowModalIndex = this.handleShowModalIndex.bind(this)
      this.handleSelectIndex = this.handleSelectIndex.bind(this)
      this.handleSubmit = this.handleSubmit.bind(this)

    }

    componentDidMount() {
      const that = this
      $.ajax({
        url: urlTree,
        type: 'GET',
        success: function (data) {
          that.setState({
            list_index: data
          })
        },
        error: function (error) {
          console.log(error);
          // alert();
        }
      });
    }

    handleChangefile (e) {
      const file = e.target.files[0],
            reader = new FileReader();
        const file_name = this.getLastString(e.target.value, "\\")
        if (this.getLastString(file_name,".") !== 'zip') {
          return false
        }

        this.setState({
          file_name:file_name,
         });

        reader.onload = (e) => {
            this.setState({
                file: reader.result,
            });
        }
        reader.readAsDataURL(file);
    }

    handleClickFile() {
      this.inputElement.click();
    }

    getLastString(path, code){
      const split_path = path.split(code)
      return split_path.pop()
    }

    handleShowModalWorkFlow(data) {
      const {isShowModalWF,work_flow_data} = this.state
      if(!isShowModalWF) {
        this.setState({
          isShowModalWF: !isShowModalWF,
          wl_key: work_flow_data ? workflows.findIndex((item) => {return work_flow_data && item.id === work_flow_data.id}) : null
        })
      } else {
        this.setState({
          isShowModalWF: !isShowModalWF,
          work_flow_data: data ? data : work_flow_data
        })
      }
    }

    handleChangeWF(e) {
      const value = e.target.value
      this.setState({
        wl_key: value
      })
    }

    handleShowModalIndex(data) {
      const {isShowModalIndex,select_index_list,term_select_index_list} = this.state
      if(!isShowModalIndex) {
        this.setState({
          isShowModalIndex: !isShowModalIndex,
          term_select_index_list: [...select_index_list]
        })
      } else {
        this.setState({
          isShowModalIndex: !isShowModalIndex,
          select_index_list: data ? [...term_select_index_list] : [...select_index_list]
        })
      }
    }

    handleSelectIndex(data) {
      const {term_select_index_list} = this.state
      const new_select_index = term_select_index_list.filter(item => {
        return data.id !== item.id
      })
      if(new_select_index.length !== term_select_index_list.length) {
        this.setState({
          term_select_index_list: new_select_index
        })
      } else {
        this.setState({
          term_select_index_list: [...term_select_index_list, {...data}]
        })
      }
    }

    handleSubmit() {
      const {isShowModalImport,file,file_name, work_flow_data, select_index_list} = this.state
      const {handleCheck} = this.props
      const data = {
        file,
        file_name,
        // work_flow: work_flow_data,
        // index: select_index_list
      }
      handleCheck(data)
    }

    render() {
      const {
        file_name,
        isShowModalWF,
        wl_key,
        work_flow_data,
        isShowModalIndex,
        list_index,
        term_select_index_list,
        select_index_list,
        isShowModalImport,
        file
      } = this.state
      return(
        <div className="import_component">
          <div className="row layout">
            <div className="col-md-12">
              <div className="row">
                <div className="col-md-2 col-cd">
                  <label>{import_file}</label>
                </div>
                <div className="col-md-8">
                  <div>
                    <button className="btn btn-primary" onClick={this.handleClickFile}>{select_file}</button>
                    <input
                      type="file"
                      className="input-file"
                      ref={input => this.inputElement = input}
                      accept=".zip"
                      onChange={this.handleChangefile}
                      />
                  </div>
                  <div className="block-placeholder">
                    {
                      file_name ? <p className="active">{file_name}</p> : <p>{selected_file_name}</p>
                    }
                  </div>
                </div>
              </div>
            </div>
{/*
            <div className="col-md-12">
              <div className="row">
                <div className="col-md-2 col-cd">
                  <label>{import_index}</label>
                </div>
                <div className="col-md-8 ">
                  <div>
                    <button className="btn btn-primary" onClick={()=>this.handleShowModalIndex(false)}>{select_index}</button>
                  </div>
                  <div className="block-placeholder">
                    {
                      select_index_list.length ? select_index_list.map((item,key) => {
                        return(
                          <div className="panel_bread" key={key}>
                            <ol className="breadcrumb breadcrumb-custorm">
                              {
                                item.name.map((item_name, key_item)=>{
                                  return(
                                    <li
                                      style={{listStylePosition: "inside",
                                      }}>{item_name}</li>
                                  )
                                })
                              }
                            </ol>
                          </div>
                        )
                      }) : <p>{selected_index}</p>
                    }
                  </div>
                </div>
              </div>
            </div>
            <div className="col-md-12">
              <div className="row">
                <div className="col-md-2 col-cd">
                  <label>{work_flow}</label>
                </div>
                <div className="col-md-8">
                  <div>
                    <button className="btn btn-primary" onClick={this.handleShowModalWorkFlow}>{select_work_flow}</button>
                  </div>
                  <div className="block-placeholder">
                    {
                      work_flow_data ? <p className="active">{work_flow_data.flows_name}</p> : <p>{selected_work_flow}</p>
                    }
                  </div>
                </div>
              </div>
            </div>
             */}
            <div className="col-md-12">
              <div className="row">
                <div className="col-md-2">
                  <button
                    className="btn btn-primary"
                    disabled={!file}

                    onClick={()=>{file && this.handleSubmit()}}
                  >
                    <span className="glyphicon glyphicon-download-alt icon"></span>{import_label}
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Work Flow */}
{/*
          <div className={`modal ${isShowModalWF ? "active" : ''}`}>
            <div className="modal-mark" onClick={()=>this.handleShowModalWorkFlow()}></div>
            <div className="modal-content">
              <div class="row">
                <div class="col-sm-12 header">
                  <h3>{work_flow}</h3>
                </div>
                <div class="col-sm-12 table-scroll-400">
                  <table class="table table-striped table-bordered">
                    <thead>
                      <tr>
                        <th></th>
                        <th>{work_flow}</th>
                        <th>{item_type}</th>
                        <th>{flow}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {
                        workflows.map((item, key) => {
                          return (
                            <tr key={key}>
                              <td style={{textAlign: 'center'}}>
                                <input
                                  type='radio'
                                  name='workflow'
                                  value={key}
                                  checked={wl_key == key}
                                  onChange={this.handleChangeWF}
                                  ></input>
                              </td>
                              <td>{item.flows_name}</td>
                              <td>{item.item_type_name}</td>
                              <td>{item.flow_name}</td>
                            </tr>
                          )
                        })
                      }
                    </tbody>
                  </table>
                </div>
                <div class="col-sm-12 footer text-align-right">
                  <button
                    className="btn btn-primary"
                    disabled={wl_key === null}
                    onClick={()=>{wl_key!== null && this.handleShowModalWorkFlow(workflows[wl_key])}}
                  >
                    <span className="glyphicon glyphicon-download-alt icon"></span>{select}
                  </button>
                  <button className="btn btn-danger m-l-15" onClick={()=>this.handleShowModalWorkFlow()}>{cancel}</button>
                </div>
              </div>
            </div>
          </div>
           */}
          {/* Index */}
{/*
          <div className={`modal ${isShowModalIndex ? "active" : ''}`}>
            <div className="modal-mark" onClick={()=>this.handleShowModalIndex(false)}></div>
            <div className="modal-index">
              <div class="row">
                <div class="col-sm-12 header">
                  <h3>{import_index}</h3>
                </div>
                <div class="col-sm-12">
                  <div className="row">
                    <div className="col-md-4">
                      <div className="panel panel-default">
                        <div className="panel-heading">
                          <h3 className="panel-title">{index_tree}</h3>
                        </div>
                        <div className="panel-body tree_list">
                          {
                            isShowModalIndex && <TreeList
                            children={list_index}
                            handleSelectIndex={this.handleSelectIndex}
                            tree_name={[]}
                            select_index_list={[...select_index_list]}
                            ></TreeList>
                          }

                        </div>
                      </div>
                    </div>
                    <div className="col-md-8">
                      <div className="panel panel-default">
                        <div className="panel-heading">
                          <h3 className="panel-title">{designate_index}</h3>
                        </div>
                        <div className="panel-body index_list">
                        <ul className="list-group">
                          {term_select_index_list.map((item,key)=>{
                            return (
                              <li className="list-group-item" key={key}>
                                {item.name[item.name.length-1]}
                              </li>
                            )
                          })}
                        </ul>

                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                <div class="col-sm-12 footer text-align-right">
                  <button
                    className="btn btn-primary"
                    disabled={!term_select_index_list.length}
                    onClick={()=>{term_select_index_list.length && this.handleShowModalIndex(true)}}
                  >
                    <span className="glyphicon glyphicon-download-alt icon"></span>{select}</button>
                  <button className="btn btn-danger m-l-15" onClick={()=>this.handleShowModalIndex(false)}>{cancel}</button>
                </div>
              </div>
            </div>
          </div>
           */}
          {/* import */}
{/*
          <div className={`modal ${isShowModalImport ? "active" : ''}`}>
            <div className="modal-mark" onClick={()=>this.handleSubmit(false)}></div>
            <div className="modal-index">
              <div class="row">
                <div class="col-sm-12 header">
                  <h3>Import Items</h3>
                </div>
                <div class="col-sm-12">
                  <table class="table table-striped table-bordered">
                    <thead>
                      <tr>
                        <th>No</th>
                        <th>Item ID</th>
                        <th>Title</th>
                      </tr>
                    </thead>
                    <tbody>
                      {
                        workflows.slice(0,5).map((item, key) => {
                          return (
                            <tr key={key}>
                              <td>
                               {key}
                              </td>
                              <td>{item.flows_name}</td>
                              <td>{item.item_type_name}</td>
                            </tr>
                          )
                        })
                      }
                    </tbody>
                  </table>
                </div>
                <div class="col-sm-12 footer footer-import text-center">
                  <button className="btn btn-primary" onClick={()=>{this.handleSubmit(true)}}><span className="glyphicon glyphicon-download-alt icon"></span>{import_label}</button>
                  <button className="btn btn-danger m-l-15" onClick={()=>this.handleSubmit(false)}>{cancel}</button>
                  <button className="btn btn-success m-l-15" onClick={()=>this.handleSubmit(false)}>Download</button>
                </div>
              </div>
            </div>
          </div> */}

        </div>
      )
    }
}

class TreeList extends React.Component {

  constructor(){
    super()

  }

  render(){
    const {children, tree_name,select_index_list} = this.props
    return(
      <div>
        <ul>
          {
            children.map((item,index)=> {
              return (
                  <li>
                    <TreeNode
                      data={item} key={index}
                      handleSelectIndex={this.props.handleSelectIndex}
                      tree_name={tree_name}
                      select_index_list={select_index_list}
                      ></TreeNode>
                  </li>
              )
            })
          }
        </ul>
      </div>
    )
  }

}

class TreeNode extends React.Component {

  constructor(){
    super()
    this.state={
      isCollabsed: true,
      defaultChecked: false
    }
    this.handleShow = this.handleShow.bind(this)
    this.handleClick = this.handleClick.bind(this)
    this.defaultChecked = this.defaultChecked.bind(this)
  }

  handleShow(){
    const {isCollabsed} = this.state
    this.setState({
      isCollabsed: !isCollabsed
    })
  }

  handleClick(e) {
    const checked = e.target.checked
    this.props.handleSelectIndex({
      id: this.props.data.id,
      name: [...this.props.tree_name, this.props.data.name]
    })
    this.setState({
      defaultChecked: checked
    })
  }

  defaultChecked() {
    const {data, select_index_list} = this.props
    const result = !!select_index_list.filter(item => item.id===data.id).length
    return result
  }

  componentDidMount(){
    this.setState({
      defaultChecked: this.defaultChecked()
    })
  }

  render(){
    const {data, tree_name,select_index_list,} = this.props
    const {isCollabsed,defaultChecked} = this.state

    return(
      <div className="tree-node">
        <div
          className={`folding ${ data.children.length ? isCollabsed ? 'node-collapsed': 'node-expanded' : 'weko-node-empty'}`}
          onClick={()=>{data.children.length && this.handleShow()}}
        >
        </div>
        <div className='node-value'>
          <input type="checkbox" onChange={this.handleClick} ref={re => this.input} checked={defaultChecked} style={{marginRight: '5px'}}></input>
          <span className="node-name">{data.name}</span>
        </div>
        <div className={`${isCollabsed ? 'hide' : ''}`}>
          <TreeList
            children={data.children}
            tree_name={[...tree_name, data.name]}
            handleSelectIndex={this.props.handleSelectIndex}
            select_index_list={select_index_list}
            ></TreeList>
        </div>
      </div>
    )
  }

}

class CheckComponent extends React.Component {

  constructor(){
    super()
    this.state = {
      total: 0,
      new_item: 0,
      update_item: 0,
      check_error: 0,
      list_record: []
    }
    this.handleGenerateData = this.handleGenerateData.bind(this)
    this.generateTitle = this.generateTitle.bind(this)
    this.handleDownload = this.handleDownload.bind(this)
  }

  componentWillReceiveProps(nextProps, prevProps){
    this.handleGenerateData(nextProps.list_record)
  }

  handleGenerateData(list_record = []){
    const check_error = list_record.filter((item) => {
      return item.errors
    }).length
    const new_item = list_record.filter((item) => {
      return item.status && item.status === 'new'
    }).length
    const update_item = list_record.filter((item) => {
      return item.status && item.status === 'update'
    }).length

    this.setState({
      total: list_record.length,
      check_error: check_error,
      new_item: new_item,
      update_item: update_item,
      list_record: list_record
    })
  }

  generateTitle(title, len) {
    if (title.length <= len) {
      return title
    } else {
      return title.substring(0, len+1) +'...'
    }
  }

  handleDownload() {
    const {list_record} = this.state
    const result = Array.from(list_record, (item, key) => {
      return {
        'No': key,
        'Item type': item.item_type_name,
        'Item id': item.id,
        'Title' : (item['Title'] && item['Title'][0] && item['Title'][0]['Title']) ? item['Title'][0]['Title'] : item['Title'] && item['Title']['Title'] ? item['Title']['Title'] : '',
        'Check result': item['errors'] ? 'ERRORS' + (item['errors'][0] ? ': '+item['errors'][0] : '' ) : item.status === 'new' ? 'Register' : item.status === 'update' ? 'Update' : ''
      }
    })
    const data = {
      list_result: result
    }
    fetch(urlDownload, {
      method: 'POST',
      body: JSON.stringify(data),
      headers: {
        'Content-Type': 'application/json'
      },
     })
    .then(resp => resp.blob())
    .then(blob => {
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      // the filename you want
      const today = new Date();
      const date = today.getFullYear()+'-'+(today.getMonth()+1)+'-'+today.getDate();
      a.download = 'check_'+ date+'.tsv';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
    })
    .catch(() => alert('oh no!'));

  }

  render(){
    const {total, list_record, update_item, new_item, check_error} = this.state
    const {is_import} = this.props
    return(
      <div className="check-component">
        <div className="row">
          <div className="col-md-12 text-center">
            <button
              className="btn btn-primary"
              onClick={this.props.handleImport}
              disabled={is_import}
            >
              <span className="glyphicon glyphicon-download-alt icon"></span>{import_label}
             </button>
          </div>
          <div className="col-md-12 text-center">
            <div className="row block-summary">
              <div className="col-lg-2 col-md-3 col-sm-3">
                <h3><b>{summary}</b></h3>
                <div className="flex-box">
                  <div>{total_label}:</div>
                  <div>{total}</div>
                </div>
                <div className="flex-box">
                  <div>{new_item_label}:</div>
                  <div>{new_item}</div>
                </div>
                <div className="flex-box">
                  <div>{update_item_label}:</div>
                  <div>{update_item}</div>
                </div>
                <div className="flex-box">
                  <div>{check_error_label}:</div>
                  <div>{check_error}</div>
                </div>
              </div>
              <div className="col-lg-10 col-md-9 text-align-right">
                <button
                  className="btn btn-primary"
                  onClick={this.handleDownload}
                 ><span className="glyphicon glyphicon-cloud-download"></span>{download}</button>
              </div>
            </div>
          </div>
          <div className="col-md-12 m-t-20">
            <table class="table table-striped table-bordered">
              <thead>
                <tr>
                  <th>{no}</th>
                  <th>{item_type}</th>
                  <th>{item_id}</th>
                  <th>{title}</th>
                  <th>{check_result}</th>
                </tr>
              </thead>
              <tbody>
                {
                  list_record.map((item, key) => {
                    return (
                      <tr key={key}>
                        <td>
                          {key}
                        </td>
                        <td>{item.item_type_name || not_match}</td>
                        <td>
                          {item.status === 'new' && item.id ? (new_item_label+'('+ item.id+')') : item.id ? item.id :''}
                        </td>
                        <td>
                        <p className="title_item">
                          {(item['Title'] && item['Title'][0] && item['Title'][0]['Title'])
                           ? item['Title'][0]['Title']: item['Title'] && item['Title']['Title']
                           ? item['Title']['Title'] : '' }
                        </p>

                         </td>
                        <td>{item['errors'] ? item['errors'][0] && (error+ ': '+ item['errors'][0]) || error : item.status === 'new'?
                          <span className="badge badge-success">{register}</span> :
                           item.status === 'update' ?
                            <span className="badge badge-primary">{update}</span> :''}</td>
                      </tr>
                    )
                  })
                }
              </tbody>
            </table>
          </div>
        </div>
      </div>
    )
  }
}

$(function () {
    ReactDOM.render(
        <MainLayout/>,
        document.getElementById('root')
    )
});
