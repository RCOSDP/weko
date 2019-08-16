const urlLoadLang = '/api/admin/load_lang';
const urlLoadSiteInfo = '/api/admin/get_site_info';

class MainLayout extends React.Component {

    constructor(props) {
        super(props);
        this.state = {
           list_lang_register: [],
           site_name: [],
           copy_right: "",
           keyword: "",
           description: "",
           errors: {}
        }
        this.get_list_lang_register = this.get_list_lang_register.bind(this)
        this.get_site_info = this.get_site_info.bind(this)
        this.handleChange = this.handleChange.bind(this)
        this.handleChangeSiteName = this.handleChangeSiteName.bind(this)
        this.handleAddSiteName = this.handleAddSiteName.bind(this)
        this.handleSave = this.handleSave.bind(this)
        this.handleRemoveSiteName = this.handleRemoveSiteName.bind(this)
        this.isEnableAddSiteName = this.isEnableAddSiteName.bind(this)
        this.handleValidation = this.handleValidation.bind(this)
    }

    componentDidMount() {
      this.get_list_lang_register()
      this.get_site_info()
    }

    get_list_lang_register() {
      const that = this
      $.ajax({
        url: urlLoadLang,
        type: 'GET',
        success: function (data) {
          const results = data.results;

          const list_lang_register = results.filter(item => item.is_registered)
          that.setState({
            list_lang_register: list_lang_register
          })
        },
        error: function (error) {
          console.log(error);
          alert('Error when get languages');
        }
      });
    }

    get_site_info() {
    const that = this

    $.ajax({
        url: urlLoadSiteInfo,
        type: 'GET',
        success: function (data) {
          const results = data;
          that.setState({
            ...results
          })
        },
        error: function (error) {
          console.log(error);
          alert('Error when get languages');
        }
      });
     }

    handleChange(name, value) {
      this.setState({
        [name]: value
      })
    }

    handleChangeSiteName(index, name, value) {
      let {site_name} = this.state
      site_name[index][name] = value
      this.setState({
        site_name: site_name
      })
    }

    handleAddSiteName() {
      const new_site_name = {
        name: "",
        language: ""
      }
      let {site_name} = this.state
      this.setState({
        site_name: [...site_name, {...new_site_name}]
      })
    }

    handleRemoveSiteName(index){
      const {site_name} = this.state
      this.setState({
        site_name: site_name.filter((value,key) => key!=index)
      })
    }

    handleSave(){
      console.log(this.state)
      const validate = this.handleValidation()
      console.log("validate",validate)
    }

    isEnableAddSiteName(){
    const {site_name, list_lang_register} = this.state
      return site_name.length < list_lang_register.length
    }

    handleValidation(){
      const {site_name, list_lang_register} = this.state
      const errors = {}
      const site_name_test = Array.from(site_name, (item, key) => ({...item, index: key}))
      const list_lang_code = Array.from(list_lang_register, item => item.lang_code)
      const errors_mess = []
      if(!site_name.length) {
        errors_mess.push('Must set at least 1 site name.')
      }
      site_name_test.map(item => {
        if(!item.name.trim()) {
          errors_mess.push("Site name is required")
          errors[`site_name_${item.index}`] = "Please input site information for empty field."
        }
        const check_dub = site_name_test.filter(sn => sn.language === item.language)
        if(check_dub.length>=2) {
          errors_mess.push("The same language is set for many site names.")
          check_dub.map(cd => {
            errors[`site_name_${cd.index}`] = 'The same language is set for many site names.'
          })
        }
        if(item.index>=list_lang_register.length) {
          errors[`site_name_${item.index}`] = 'language not match'
        }
        if(!list_lang_code.includes(item.language)){
           errors[`site_name_${item.index}`] = 'language not match'
        }
      })
      const list_error = Array.from(new Set(errors_mess))
      this.setState({
        errors: errors
      })
      alert(list_error.join('\r\n'))
      if(list_error.length){
        return false
      }
      else return true
    }

    render() {
        const {errors,site_name,list_lang_register,copy_right,description,keyword, favicon} = this.state
        return (
            <div className="site_info row">
              <div className="col-md-8 col-sm-12">
                <div className="row form-group">
                  <div className="col-md-2 col-md-offset-8">
                      <button
                       className="btn btn-default"
                       onClick={this.handleAddSiteName}
                       disabled={!this.isEnableAddSiteName()}
                       ><span className="glyphicon glyphicon-plus"></span>Add site name</button>
                  </div>
                </div>

                {
                  site_name.map((site_name,key) => {
                    return(
                      <div className={`row form-group ${errors[`site_name_${key}`] && "has-error"}`} key={key}>
                        <div className="col-md-2">
                          <label>Site name</label>
                        </div>
                        <div className="col-md-6">
                          <input
                            type="text"
                            className="form-control"
                            id="name"
                            placeholder="site name not set"
                            defaultValue={site_name.name}
                            onBlur={e => {
                              this.handleChangeSiteName(key, 'name', e.target.value)
                            }}
                          />
                        </div>
                        <div className="col-md-2">
                          <select
                          className="form-control"
                          value={site_name.language}
                          onChange={e => {
                            this.handleChangeSiteName(key, 'language', e.target.value)
                          }}
                          >
                            <option disabled value="">Language</option>
                            {
                              list_lang_register.map((item,index)=>{
                                return(
                                  <option value={item.lang_code} key={index}>{item.lang_name}</option>
                                )
                              })
                            }
                          </select>
                        </div>
                        {
                          key > 0 &&
                          <div className="col-md-2">
                            <button
                             className="btn btn-danger"
                             onClick={()=>{this.handleRemoveSiteName(key)}}
                             ><span className="glyphicon glyphicon-trash"></span>Delete</button>
                          </div>
                        }

                      </div>
                    )
                  })
                }

                <div className={`row form-group ${errors[`favicon`] && "has-error"}`}>
                  <div className="col-md-2">
                    <label>Favicon</label>
                  </div>
                  <div className="col-md-6" >
                    <div className="row"  style={{marginBottom: "10px"}}>
                      <div className="col-md-6" >
                       <input
                        type="file"
                        className="input-favicon"
                        id="favicon"
                        onChange={(e)=> {
                          this.handleChange('favicon', e.target.value)
                        }}
                        />
                       <button className="btn btn-default btn-block">Select Icon File</button>
                      </div>
                    </div>
                    <div className="row">
                      <div className="col-md-6"><span>{favicon ? favicon : "Selected icon"}</span></div>
                      <div className="col-md-6">
                        <img src="https://community.repo.nii.ac.jp/images/common/favicon.ico" alt="Smiley face" />
                      </div>
                    </div>
                  </div>
                </div>

                <div className={`row form-group ${errors[`copy_right`] && "has-error"}`}>
                  <div className="col-md-2">
                    <label>CopyRight</label>
                  </div>
                  <div className="col-md-6">
                    <input
                    type="text"
                    className="form-control"
                    id="copy_right"
                    value={copy_right}
                    onChange={(e)=> {
                          this.handleChange('copy_right', e.target.value)
                        }}
                    />
                  </div>
                </div>

                <div className={`row form-group ${errors[`description`] && "has-error"}`}>
                  <div className="col-md-2">
                    <label>Description</label>
                  </div>
                  <div className="col-md-6">
                    <textarea
                       rows="3"
                       className="form-control"
                       id="description"
                       value={description}
                       onChange={(e)=> {
                          this.handleChange('description', e.target.value)
                       }}
                     />
                  </div>
                </div>

                <div className={`row form-group ${errors[`keyword`] && "has-error"}`}>
                  <div className="col-md-2">
                    <label>Keyword</label>
                  </div>
                  <div className="col-md-6">
                    <textarea
                     rows="3"
                     className="form-control"
                     id="keyword"
                     value={keyword}
                     onChange={(e)=> {
                          this.handleChange('keyword', e.target.value)
                       }}
                     />
                  </div>
                </div>
                <div className="text-center"><button className="btn btn-primary" style={{width: "100px"}} onClick={this.handleSave}><span className="glyphicon glyphicon-saved"></span>Save</button></div>
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
