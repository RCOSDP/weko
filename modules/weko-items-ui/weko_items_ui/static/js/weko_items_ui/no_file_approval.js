const ENABLE_NO_FILE_APPROVAL_CHECKBOX_LABEL =  document.getElementById('no_file_approval_checkbox_label').value
const NO_FILE_APPROVAL_LABEL = document.getElementById('no_file_approval_label').value
const TERMS_AND_CONDITIONS_LABEL = document.getElementById('terms_and_conditions_label').value

class NoneContentsApproval extends React.Component{
    constructor(props){
        super(props);
        this.state = {
            showNoneContentsApproval:false,
            showTextareaForTerms:false
        }
    }

    componentDidMount() {
        const activityID = $("#activity_id").text();
        let item_application = [];
        let display_item_application_button = false
        $.ajax({
            url: "/workflow/get_item_application/" + activityID,
            async: false,
            method: "GET",
            success: function (response) {
            if (response.code) {
                item_application = response.item_application || {};
                display_item_application_button = response.is_display_item_application_button || false
            }
            },
            error: function(jqXHR, status) {
                alert(jqXHR.responseJSON.msg);
            }
        })
        this.setState({showNoneContentsApproval:display_item_application_button})
    }


    getDataInit() {
        let dataInit = {'workflows': [], 'roles': []};
        $.ajax({
          url: '/workflow/get-data-init',
          method: 'GET',
          async: false,
          success: function (data, status) {
            dataInit = data;
          },
          error: function (data, status) {}
        })
        return dataInit
      }

    TextareaForTerms(){
        let term_id = $('#terms_without_contents').val();
        if(term_id == "term_free"){
            return true
        }
        return false
    }

    render() {
        const itemApplicationList = this.getDataInit()
        const workflowList = itemApplicationList['init_workflows']
        const termsList = itemApplicationList['init_terms']
        return (
        <div>
            <div className="row">
                <div className="col-sm-12 form-group style-component">
                    <label className="col-xs-3 text-right">
                        <ReactBootstrap.Checkbox id='display_item_application_checkbox'checked={this.state.showNoneContentsApproval}
                            onChange={() => {this.setState({showNoneContentsApproval: !this.state.showNoneContentsApproval})}}>
                            {ENABLE_NO_FILE_APPROVAL_CHECKBOX_LABEL}
                        </ReactBootstrap.Checkbox>
                    </label>
                </div>
            </div>
            <div className={`row ${this.state.showNoneContentsApproval ? 'show': 'hidden'}`}>
                <div className="col-sm-12 form-group style-component">
                    <label className="control-label col-xs-3 text-right">
                        {NO_FILE_APPROVAL_LABEL}
                    </label>
                    <div class="col-sm-9">
                        <select class="form-control" id="workflow_for_item_application">
                            <option value=""></option>
                            {workflowList.map((workflow,index) => (
                            <option value={workflow.id}>{workflow.flows_name}</option>
                            ))}
                        </select>
                    </div>
                </div>
            </div>
            <div className={`row ${this.state.showNoneContentsApproval ? 'show': 'hidden'}`}>
                <div className="col-sm-12 form-group style-component">
                    <label className="control-label col-xs-3 text-right">
                        {TERMS_AND_CONDITIONS_LABEL}
                    </label>
                    <div class="col-sm-9">
                        <select class="form-control" id="terms_without_contents" onChange={() => {this.setState({showTextareaForTerms : this.TextareaForTerms()})}} > 
                            <option value=""></option>
                            {termsList.map((Terms,index) => (
                            <option value={Terms.id}>{Terms.name}</option>
                            ))}
                        </select>
                    </div>
                <div className={`row ${this.state.showTextareaForTerms ? 'show': 'hidden'}`}>
                    <div className="col-sm-12 form-group schema-form-textarea">
                        <label className="control-label col-sm-3"></label>
                        <div class="col-sm-9">
                            <textarea class="form-control" id="termsDescription"></textarea>
                        </div>
                    </div>
                </div>
                </div>
            </div>
        </div>
        )
    }
}


ReactDOM.render(
    <NoneContentsApproval/>,
    document.getElementById('none-contents-approval')
)