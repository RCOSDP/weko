const currentTime = new Date().getTime();
const urlLoadLang = '/api/admin/load_lang' + '?time=' + currentTime;
const urlLoadSiteInfo = '/api/admin/get_site_info' + '?time=' + currentTime;
const default_favicon = '/static/favicon.ico'
const default_favicon_name = 'JAIRO Cloud icon'
const site_name_label = document.getElementById("site_name_label").value;
const favicon_label = document.getElementById("favicon_label").value;
const copyright_label = document.getElementById("copyright_label").value;
const description_label = document.getElementById("description_label").value;
const keyword_label = document.getElementById("keyword_label").value;
const notify_label = document.getElementById("notify_label").value;
const selected_icon_label = document.getElementById("selected_icon_label").value;
const selected_file_label = document.getElementById("selected_file_label").value;
const add_site_name_label = document.getElementById("add_site_name_label").value;
const add_notify_label = document.getElementById("add_notify_label").value;
const site_name_not_set_label = document.getElementById("site_name_not_set_label").value;
const language_label = document.getElementById("language_label").value;
const save_label = document.getElementById("save_label").value;
const must_set_at_least_1_site_name_label = document.getElementById("must_set_at_least_1_site_name_label").value;
const please_input_site_infomation_for_empty_field_label = document.getElementById("please_input_site_infomation_for_empty_field_label").value;
const the_same_language_is_set_for_many_site_names_label = document.getElementById("the_same_language_is_set_for_many_site_names_label").value;
const the_notify_limit_to_1000_characters = document.getElementById("the_notify_limit_to_1000_characters").value;
const the_same_language_is_set_for_many_notify_label = document.getElementById("the_same_language_is_set_for_many_notify_label").value;
const error_when_get_languages_label = document.getElementById("error_when_get_languages_label").value;
const error_when_get_site_infomation_label = document.getElementById("error_when_get_site_infomation_label").value;
const language_not_match_label = document.getElementById("language_not_match_label").value;
const delete_label = document.getElementById("delete_label").value;
const select_icon_file_label = document.getElementById("select_icon_file_label").value;
const select_file_name_label = document.getElementById("select_file_name_label").value;
const success_mess = document.getElementById("success_mess").value;
const google_tracking_id_user_label = document.getElementById("google_tracking_id_user_label").value;
const ogp_image_label = document.getElementById("ogp_image_label").value;
const lang_code_ja = 'ja'
class MainLayout extends React.Component {

    constructor(props) {
        super(props);
        this.state = {
           list_lang_register: [],
           site_name: [],
           copy_right: "",
           keyword: "",
           description: "",
           favicon_name: "",
           favicon: "",
           google_tracking_id_user: "",
           ogp_image: "",
           ogp_image_name: "",
           notify: [],
           errors: [],
           show_alert: false,
           success: true,
        }
        this.get_site_info = this.get_site_info.bind(this)
        this.handleChange = this.handleChange.bind(this)
        this.handleChangeSiteName = this.handleChangeSiteName.bind(this)
        this.handleChangeNotify = this.handleChangeNotify.bind(this);
        this.handleAddSiteName = this.handleAddSiteName.bind(this)
        this.handleAddNotify = this.handleAddNotify.bind(this);
        this.handleSave = this.handleSave.bind(this)
        this.handleRemoveSiteName = this.handleRemoveSiteName.bind(this)
        this.handleRemoveNotify = this.handleRemoveNotify.bind(this);
        this.isEnableAddSiteName = this.isEnableAddSiteName.bind(this)
        this.isEnableAddNotify = this.isEnableAddNotify.bind(this);
        this.handleValidation = this.handleValidation.bind(this)
        this.handleChangeFavicon = this.handleChangeFavicon.bind(this);
        this.handleChangeOGPImage = this.handleChangeOGPImage.bind(this);
        this.getLastString = this.getLastString.bind(this)
        this.handle_focus_error = this.handle_focus_error.bind(this)
        this.handleDimiss = this.handleDimiss.bind(this)
        const that = this
        $.ajax({
          url: urlLoadLang,
          type: 'GET',
          success: function (data) {
            const results = data.results;
            const list_lang_register = results.filter(item => item.is_registered)
            that.setState({
              list_lang_register: list_lang_register,
              default_lang_code: list_lang_register[0].lang_code
            })
            that.get_site_info()
          },
          error: function (error) {
            console.log(error);
            alert(error_when_get_languages_label);
          }
        });
    }

    componentDidMount() {
    }

    get_site_info() {
      const that = this
      $.ajax({
          url: urlLoadSiteInfo,
          type: 'GET',
          success: function (data) {
            const result = data;
            that.setState({
              ...result,
              favicon: (result && result.favicon) ? result.favicon :  default_favicon,
              favicon_name: (result && result.favicon_name) ? result.favicon_name :  default_favicon_name
            });
            if(!result  || !result.site_name ||!result.site_name.length){
              that.handleAddSiteName()
            }
            if(!result  || !result.notify ||!result.notify.length){
              that.handleAddNotify()
            }
          },
          error: function (error) {
            console.log(error);
            alert(error_when_get_site_infomation_label);
          }
        });
     }

    handleChange(name, value) {
      this.setState({
        [name]: value
      })
    }

    handleChangeSiteName(index, name, value) {
      let {site_name} = this.state;
      site_name[index][name] = value;
      this.setState({
        site_name: site_name
      })
    }


    handleChangeNotify(index, name, value) {
      let {notify} = this.state;
      notify[index][name] = value;
      this.setState({
        notify: notify
      })
    }

    handleAddSiteName() {
      const {default_lang_code} = this.state
      const new_site_name = {
        name: "",
        language: default_lang_code
      }
      let {site_name} = this.state
      this.setState({
        site_name: [...site_name, {...new_site_name}]
      })
    }

    handleAddNotify() {
      const {default_lang_code} = this.state;
      const new_notify = {
        notify_name: "",
        language: default_lang_code
      };
      let {notify} = this.state;
      let notifyResult = [];
      if (notify != null){
        notifyResult = [...notify, {...new_notify}];
      } else {
        notifyResult = [{ notify_name: "", language: default_lang_code }];
      }
      this.setState({
        notify: notifyResult
      })
    }

    handleRemoveSiteName(index){
      const {site_name} = this.state
      this.setState({
        site_name: site_name.filter((value,key) => key!=index)
      })
    }


    handleRemoveNotify(index){
      const {notify} = this.state;
      this.setState({
        notify: notify.filter((value,key) => key!=index)
      })
    }

    handleSave() {
      const { site_name, copy_right, keyword, description, favicon_name, favicon, notify, google_tracking_id_user, ogp_image, ogp_image_name } = this.state
      const validate = this.handleValidation()
      console.log("validate", validate)
      if (validate.status) {
        let new_site_name = JSON.parse(JSON.stringify(site_name))
        for (let index = 0; index < new_site_name.length; index++) {
          new_site_name[index].index = index
        }
        let new_notify = JSON.parse(JSON.stringify(notify))
        for (let index = 0; index < new_notify.length; index++) {
          new_notify[index].index = index
        }
        const that = this
        $.ajax({
          url: "/api/admin/update_site_info",
          type: 'POST',
          dataType: "json",
          contentType: 'application/json',
          data: JSON.stringify({
            site_name: new_site_name,
            copy_right: copy_right,
            google_tracking_id_user: google_tracking_id_user,
            keyword: keyword,
            description: description,
            favicon_name: favicon_name,
            favicon: favicon,
            ogp_image_name: ogp_image_name,
            ogp_image: ogp_image,
            notify: new_notify
          }),
          success: function (result) {
            console.log(result)
            if (result.error) {
              that.setState({
                errors: result.data,
                success: false,
                list_error: error,
                show_alert: true
              }, () => {
                that.handle_focus_error()
              })
            } else {
              that.setState({
                success: true,
                show_alert: true
              })
              setTimeout(() => {
                window.location.reload();
              }, 500);
            }
          },
          error: function (error) {
            console.log(error);
          }
        });
      } else {
        this.setState({
          errors: validate.item,
          success: false,
          list_error: validate.message,
          show_alert: true
        }, () => {
          this.handle_focus_error()
        })
      }
    }

    isEnableAddNotify(){
    const {notify, list_lang_register} = this.state;
      return notify ? notify.length < list_lang_register.length : true
    }


    isEnableAddSiteName(){
      const {site_name, list_lang_register} = this.state;
        return site_name.length < list_lang_register.length
      }

    handleValidation(){
      const {site_name, list_lang_register, notify} = this.state
      const errors = {}
      let site_name_test = JSON.parse(JSON.stringify(site_name))
      for (let index = 0; index < site_name_test.length; index++) {
        site_name_test[index].index = index
      }
      let list_lang_code = []
      for (let index = 0; index < list_lang_register.length; index++) {
        list_lang_code.push(list_lang_register[index].lang_code)
      }
      const errors_mess = []
      if(!site_name.length) {
        errors_mess.push(must_set_at_least_1_site_name_label)
        return {
          message : must_set_at_least_1_site_name_label,
          item: [],
          status: false
        }
      }
      if(site_name.filter(item => !item.name).length === site_name.length) {
         return {
          message : must_set_at_least_1_site_name_label,
          item: ["site_name_0"],
          status: false
        }
      }
      for (let index in site_name_test) {
        const item = site_name_test[index];
        if(!item.name.trim()) {
          return {
            message : please_input_site_infomation_for_empty_field_label,
            item: [`site_name_${item.index}`],
            status: false
          }
        }
        const check_dub = site_name_test.filter(sn => sn.language === item.language && sn.language)
        if(check_dub.length>=2) {
          return {
            message : the_same_language_is_set_for_many_site_names_label,
            item: [`site_name_${item.index}`],
            status: false
          }
        }
        if(list_lang_code.indexOf(item.language) == -1){
          return {
            message : language_not_match_label,
            item: [`site_name_${item.index}`],
            status: false
          }
        }
      }

      let notify_test = JSON.parse(JSON.stringify(notify))
      for (let index = 0; index < notify_test.length; index++) {
        notify_test[index].index = index
      }
      for (let index in notify_test) {
        const item = notify_test[index];
        const check_dub = notify_test.filter(nt => nt.language === item.language && nt.language);
        if(check_dub.length>=2) {
          return {
            message : the_same_language_is_set_for_many_notify_label,
            item: [`site_name_${item.index}`],
            status: false
          }
        }
        if(list_lang_code.indexOf(item.language) == -1){
          return {
            message : language_not_match_label,
            item: [`site_name_${item.index}`],
            status: false
          }
        }
        if(item.notify_name.length > 1000){
          return {
            message : the_notify_limit_to_1000_characters,
            item: [`site_name_${item.index}`],
            status: false
          }
        }
      }

      return {
        status: true
      }

    }

    handleChangeFavicon(e) {
        const file = e.target.files[0],
            pattern = /image-*/,
            reader = new FileReader();
        const favicon_name = this.getLastString(e.target.value, "\\")
        if (this.getLastString(favicon_name,".") !== 'ico') {

          return false
        }

        this.setState({
               favicon_name:favicon_name
         });

        reader.onload = (e) => {
            this.setState({
                favicon: reader.result,
            });
        }

        reader.readAsDataURL(file);
    }

  handleChangeOGPImage(e) {
      const list_validation = ['JPG', 'PNG', 'WEBP', 'GIF', 'jpg', 'png', 'webp', 'gif']
      const file = e.target.files[0],
        pattern = /image-*/,
        reader = new FileReader();
      const ogp_image_name = this.getLastString(e.target.value, "\\")
      if (list_validation.indexOf(this.getLastString(ogp_image_name,".")) < 0) {
        return false
      }

      this.setState({
        ogp_image_name:ogp_image_name
      });

      reader.onload = (e) => {
        this.setState({
          ogp_image: reader.result,
        });
      }

      reader.readAsDataURL(file);
    }

    getLastString(path, code){
        const split_path = path.split(code)
        return split_path.pop()
    }

    handle_focus_error() {
      const list_element = document.getElementsByClassName('has-error')
      const first_element = list_element.length && list_element[0]
      if(first_element){
        const input = first_element.getElementsByTagName("input")
        if(input[0]){
          input[0].focus()
          input[0].scrollIntoView()
        }
      }
    }

    handleDimiss(){
      this.setState({
        show_alert: false
      })
    }
    render() {
        const {errors,site_name,list_lang_register,copy_right,description,keyword, favicon,favicon_name,success, show_alert, list_error, notify, google_tracking_id_user, ogp_image, ogp_image_name} = this.state
        return (
            <div className="site_info row">
            {
              show_alert && (
                <div className={`alert ${success ? 'alert-success' : 'alert-danger'}`} role="alert">
                <button type="button" class="close" onClick={this.handleDimiss}>×</button>
                {
                  success ? success_mess : list_error
                }
              </div>
              )
            }

              <div className="col-md-12 col-sm-12">
                <div className="row form-group">
                  <div className="col-md-2 col-md-offset-8">
                      <button
                       className="btn btn-success"
                       onClick={this.handleAddSiteName}
                       disabled={!this.isEnableAddSiteName()}
                       ><span className="glyphicon glyphicon-plus icon"></span>{add_site_name_label}</button>
                  </div>
                </div>

                {
                  site_name.map((site_name,key) => {
                    return(
                      <div className={`row form-group`} key={key}>
                        <div className="col-md-2 text-right">
                          <label>{site_name_label}</label>
                        </div>
                        <div className="col-md-6">
                          <input
                            type="text"
                            className="form-control"
                            id="name"
                            placeholder={site_name_not_set_label}
                            defaultValue={site_name.name}
                            onBlur={e => {
                              this.handleChangeSiteName(key, 'name', e.target.value)
                            }}
                          />
                        </div>
                        <div className="col-md-2 text-right">
                          <select
                          className="form-control"
                          value={site_name.language}
                          onChange={e => {
                            this.handleChangeSiteName(key, 'language', e.target.value)
                          }}
                          >
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
                             ><span className="glyphicon glyphicon-trash icon"></span>{delete_label}</button>
                          </div>
                        }

                      </div>
                    )
                  })
                }

                <div className={`row form-group ${errors[`favicon`] && "has-error"}`}>
                  <div className="col-md-2 text-right">
                    <label>{favicon_label}</label>
                  </div>
                  <div className="col-md-6" >
                    <div className="row"  style={{marginBottom: "10px"}}>
                      <div className="col-md-6" >
                       <input
                        ref="icon"
                        type="file"
                        className="input-favicon"
                        id="favicon"
                        accept=".ico"
                        onChange={this.handleChangeFavicon}
                        />
                       <button className="btn btn-primary"
                        onClick={()=> {
                          this.refs.icon.click()
                        }}
                       >{select_icon_file_label}</button>
                      </div>
                    </div>
                    <div className="row">
                      <div className="col-md-9"><p style={{ wordBreak: 'break-all'}}>{favicon_name ? favicon_name: favicon ? favicon : selected_icon_label}</p></div>
                      <div className="col-md-3">
                      {
                        favicon && <img src={favicon} alt="favicon" className="img-response" style={{ maxWidth: "50px", maxHeight: "50px"}}/>
                      }
                      </div>
                    </div>
                  </div>
                </div>

                <div className={`row form-group ${errors[`copy_right`] && "has-error"}`}>
                  <div className="col-md-2 text-right">
                    <label>{copyright_label}</label>
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
                  <div className="col-md-2 text-right">
                    <label>{description_label}</label>
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
                  <div className="col-md-2 text-right">
                    <label>{keyword_label}</label>
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
                <div className={`row form-group ${errors[`google_tracking_id_user`] && "has-error"}`}>
                  <div className="col-md-2 text-right">
                    <label>{google_tracking_id_user_label}</label>
                  </div>
                  <div className="col-md-6">
                    <input
                    type="text"
                    className="form-control"
                    id="google_tracking_id_user"
                    value={google_tracking_id_user}
                    onChange={(e)=> {
                          this.handleChange('google_tracking_id_user', e.target.value)
                        }}
                    />
                  </div>
                </div>


              <div className={`row form-group ${errors[`ogp_image`] && "has-error"}`}>
                  <div className="col-md-2 text-right">
                      <label>{ogp_image_label}</label>
                  </div>
                  <div className="col-md-6" >
                      <div className="row"  style={{marginBottom: "10px"}}>
                          <div className="col-md-6" >
                              <input
                                  ref="input"
                                  type="file"
                                  className="input-favicon"
                                  id="ogp_image"
                                  accept="image/png, image/gif, image/jpeg, image/webp"
                                  onChange={this.handleChangeOGPImage}
                              />
                              <button className="btn btn-primary"
                                      onClick={()=> {
                                          this.refs.input.click()
                                      }}
                              >{selected_file_label}</button>
                          </div>
                      </div>
                      <div className="row">
                          <div className="col-md-9"><p style={{ wordBreak: 'break-all'}}>{ogp_image_name ? ogp_image_name: ogp_image ? ogp_image : select_file_name_label}</p></div>
                          <div className="col-md-3">
                              {
                                ogp_image && <img src={ogp_image} alt="ogp_image" className="img-response" style={{ maxWidth: "50px", maxHeight: "50px"}}/>
                              }
                          </div>
                      </div>
                  </div>
              </div>

                {this.props.enable_notify ? (
                    <div className="row form-group">
                    <div className="col-md-2 col-md-offset-8">
                        <button
                          className="btn btn-success"
                          onClick={this.handleAddNotify}
                          disabled={!this.isEnableAddNotify()}
                          ><span className="glyphicon glyphicon-plus icon"></span>{add_notify_label}</button>
                    </div>
                  </div>
                  ) :null
                }

                {
                 notify && this.props.enable_notify ? notify.map((notifyInfo, key) => {
                    return(
                      <div className={`row form-group`} key={key}>
                        <div className="col-md-2 text-right">
                          <label>{notify_label}</label>
                        </div>
                        <div className="col-md-6">
                          <textarea
                            maxlength="1000"
                            rows="3"
                            className="form-control"
                            id="notify_name"
                            defaultValue={notifyInfo.notify_name}
                            onBlur={e => {
                              this.handleChangeNotify(key, 'notify_name', e.target.value)
                            }}
                          />
                        </div>
                        <div className="col-md-2 text-right">
                          <select
                          className="form-control"
                          value={notifyInfo.language}
                          onChange={e => {
                            this.handleChangeNotify(key, 'language', e.target.value)
                          }}
                          >
                            {
                              list_lang_register.map((item)=>{
                                return(
                                  <option value={item.lang_code} key={item.lang_code}>{item.lang_name}</option>
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
                             onClick={()=>{this.handleRemoveNotify(key)}}
                             ><span className="glyphicon glyphicon-trash icon"></span>{delete_label}</button>
                          </div>
                        }

                      </div>
                    )
                  }): null
                }


                <div className="row">
                  <div className="col-md-2 text-right"></div>
                  <div className="col-md-6">
                    <button className="btn btn-primary" style={{width: "100px"}} onClick={this.handleSave}><span className="glyphicon glyphicon-saved icon"></span>{save_label}</button>
                  </div>
                </div>
              </div>
            </div>
        )
    }
}

$(function () {
    let enable_notify = document.getElementById('enable_notify').value == 'True' ? true : false;
    ReactDOM.render(
        <MainLayout enable_notify={enable_notify} />,
        document.getElementById('root')
    )
});
