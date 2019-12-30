class MainLayout extends React.Component {

    constructor(props) {
        super(props);
        this.state = {

        }

    }

    componentDidMount() {
    }


    render() {
        return (
            <div className="resource row">
              resource
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
