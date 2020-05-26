class MainLayout extends React.Component {
    constructor(props) {
        super(props);

    }
    setVersion(event) {
        console.log(event.target.value);
    }

    render() {
        const label = $("#component-version-label").val();
        const keepOption = $("#radio-version-option-2").val();
        const updateOption = $("#radio-version-option-1").val();
        return (
            <div className="row">
                <div class="form-group">
                    <label class="control-label col-sm-3 text-right">{label}</label>
                    <div class="col-sm-9" onChange={this.setVersion.bind(this)}>
                        <label><input type="radio" name="version" value="update" />{updateOption}</label>
                        <label><input type="radio" name="version" value="keep" />{keepOption}</label>
                    </div>
                </div>
            </div>

        );
    }
}

$(function () {
    ReactDOM.render(
        <MainLayout />,
        document.getElementById('react-component-version')
    )
});
