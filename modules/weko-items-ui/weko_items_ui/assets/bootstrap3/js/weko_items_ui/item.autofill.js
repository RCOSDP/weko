class ModalHeader extends React.Component {
    render() {
        return (
            <div className="text-left">
                <h3>{this.props.headerName}</h3>
            </div>
        )
    }
}
class SearchMetaForm extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            idType: '',
            itemId: '',
            selectOptions: []
        };

        this.handleChange = this.handleChange.bind(this);
        this.handleSubmit = this.handleSubmit.bind(this);
    }

    componentDidMount() {
        axios.get('/api/autofill/select_options')
            .then(res => res.data)
            .then((result) => {
                let options = result.options.map((option) => {
                    return (
                        <option key={option.value} value={option.value}>{option.text}</option>
                    )
                });
                this.setState({
                    selectOptions: options
                });
            }
            )
            .catch((error) => {
                alert(error);
            });
    }

    handleChange(event) {
        const target = event.target;
        const value = target.value;
        const name = target.name;
        this.setState({ [name]: value });
    }

    handleSubmit(event) {
        this.clickItemMetadata();
        event.preventDefault();
    }

    clickItemMetadata() {
        setTimeout(function () {
            angular.element('#btn_setItemMetadata').triggerHandler('click');
        }, 0);
    };

    render() {
        return (
            <div>
                <ModalHeader headerName={this.props.headerName} />
                <br></br>
                <form onSubmit={this.handleSubmit}>
                    <div className="form-inline">
                        <label className="input-group-text" for="autofill_id_type">
                            {this.props.selectMeta}
                        </label>
                        &nbsp;&nbsp;
                  <select name="idType" id="autofill_id_type" value={this.state.idType.value}
                            onChange={this.handleChange} className="form-control">
                            {this.state.selectOptions}
                        </select>
                        &nbsp;&nbsp;
                  <input name="itemId" type="text" id="autofill_item_id"
                            value={this.state.itemId.value} onChange={this.handleChange}
                            className="form-control ng-untouched ng-pristine ng-valid" />
                        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                  <input type="submit" id="autofill_item_button" value={this.props.getValue} className="btn btn-info" />
                    </div>
                    <br />
                    <div id="auto-fill-error-div">
                        <span id="autofill-error-message"></span>
                    </div>
                </form>
            </div>
        );
    }
}

$(function () {
    let meta_search_body = document.querySelector('#meta-search-body');
    let headerName = $("#autofill_header_name").val();
    let selectMeta = $("#autofill_select_meta").val();
    let getValue = $("#autofill_get_value").val();
    ReactDOM.render(
        <SearchMetaForm headerName={headerName}
            selectMeta={selectMeta}
            getValue={getValue} />,
        meta_search_body
    )
});
