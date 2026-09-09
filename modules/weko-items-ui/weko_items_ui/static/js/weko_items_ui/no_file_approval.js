const ENABLE_NO_FILE_APPROVAL_CHECKBOX_LABEL =  document.getElementById('no_file_approval_checkbox_label').value
const NO_FILE_APPROVAL_LABEL = document.getElementById('no_file_approval_label').value
const TERMS_AND_CONDITIONS_LABEL = document.getElementById('terms_and_conditions_label').value

class NoneContentsApproval extends React.Component{
    constructor(props){
        super(props);
        this.state = {
            workflows: [],
            terms: [],
            termsDescription: null,
            showNoneContentsApproval:false,
            selected_workflow: null,
            selected_term: null,
        }
    }

    componentDidMount() {
        fetch('/workflow/get-data-init')
            .then(response => response.json())
            .then(data => {
                const workflows = data.init_workflows || [];
                const terms = data.init_terms || [];
                this.setState({
                    workflows: workflows,
                    terms: terms
                })})
            .catch(error => alert(error));

        fetch('/workflow/get_item_application/' + $("#activity_id").text())
            .then(response => response.json())
            .then(data => {
                if (data.code) {
                    const item_application = data.item_application || {};
                    const display_item_application_button = data.is_display_item_application_button || false
                    this.setState({
                        showNoneContentsApproval: display_item_application_button,
                        selected_workflow: item_application.workflow,
                        selected_term: item_application.terms,
                        termsDescription: item_application.termsDescription
                    })
                }})
            .catch(error => alert(error));
    }

    render() {
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
                            {this.state.workflows.map((workflow, index) => {
                                const selected = (workflow.id == this.state.selected_workflow) ? 'selected' : '';
                                return <option value={workflow.id} selected={selected}>{workflow.flows_name}</option>;
                            })}
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
                        <select class="form-control" id="terms_without_contents" onChange={(e) => {this.setState({selected_term : e.target.value})}} >
                            <option value=""></option>
                            {this.state.terms.map((Terms, index) => {
                                const selected = (Terms.id === this.state.selected_term) ? 'selected' : '';
                                return <option value={Terms.id} selected={selected}>{Terms.name}</option>;
                            })}
                        </select>
                    </div>
                <div className={`row ${this.state.selected_term === "term_free" ? 'show': 'hidden'}`}>
                    <div className="col-sm-12 form-group schema-form-textarea">
                        <label className="control-label col-sm-3"></label>
                        <div class="col-sm-9">
                            <textarea class="form-control" id="termsDescription" onChange={() => {this.setState({termsDescription: this.value})}} value={this.state.termsDescription} />
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