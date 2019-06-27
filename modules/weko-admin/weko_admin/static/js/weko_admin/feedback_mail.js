class ComponentFeedbackMail extends React.Component {
    constructor(props) {
        super(props);
        this.style_component = {
            "margin-top": "15px",
            "font-size": "18px",
        }
        this.margin_left = {
            "margin-left": "10%",
        }
        this.style_radioBtn = {
            "width" : "18px",
            "height" : "18px",
        }
    }
    render() {
        return (
            <div className="form-group" style = {this.style_component}>
                <span className="control-label col-xs-2">ON/OFF</span>
                <div class="controls col-xs-10">
                    <div className="form-group">
                        <span><input style = {this.style_radioBtn} type="radio"  name="feedback_mail" value="send"/>Send</span>
                        <span  style = {this.margin_left}><input style = {this.style_radioBtn} type="radio" name="feedback_mail" value="not_send"/>Do not send</span>
                    </div>
                </div>
            </div>
        )
    }
}

class ComponentExclusionTarget extends React.Component {
    constructor(props) {
        super(props);
        this.style_component = {
            "margin-top": "15px",
            "font-size": "18px",
        }
        this.margin_left = {
            "margin-left": "10%",
        }
        this.style_radioBtn = {
            "width" : "18px",
            "height" : "18px",
        }
        this.style_button = {
            "box-shadow": "4px 4px 5px #7D7D7D",
            "background-color": "white",
            "border": "1px ridge black"
        }
        this.style_selected_box = {
            "margin-top": "15px",
            "width": "70%",
            "heiht": "50px",
            "border": "1px inset black",
            "display": "inline-block",
        }
        this.style_full_size = {
            "width": "100%",
        }
        this.style_deleteBtn = {
            "margin-left": "5px",
            "margin-bottom": "10px",
        }
        this.deleteCommand = this.deleteCommand.bind(this);
        this.searchCommand = this.searchCommand.bind(this);
    }
    deleteCommand(){

    }
    searchCommand(){

    }
    render() {
        return (
            <div className="form-group"  style = {this.style_component}>
                <span className="control-label col-xs-2">Send exclusion target persons</span>
                <div class="controls col-xs-10">
                    <div>
                        <button type="button" className="btn" style={this.style_button}><i className = "glyphicon glyphicon-search" onClick={this.searchCommand}></i>&nbsp;From author DB</button>
                    </div>
                    <div style = {this.style_full_size}>
                        <select multiple style = {this.style_selected_box}>
                            <option value="volvo">Volvo</option>
                            <option value="saab">Saab</option>
                            <option value="opel">Opel</option>
                            <option value="audi">Audi</option>
                        </select>
                        <button className="btn btn-danger delete-button style-my-button" onClick={this.deleteCommand} style = {this.style_deleteBtn}>
                            <span class="glyphicon glyphicon-trash" aria-hidden="true"></span>
                            &nbsp;Delete
                        </button>
                    </div>
                </div>
            </div>
        )
    }
}

class ComponentButtonLayout extends React.Component {
    constructor(props) {
        super(props);
        this.style_component = {
            "margin-top": "15px",
            "font-size": "18px",
        }
        this.style_button = {
            "width" : "100px",
            "border-radius" : "5%",
            "font-weight" : "600",
        }
        this.saveCommand = this.saveCommand.bind(this);
        this.sendCommand = this.sendCommand.bind(this);
    }

    saveCommand(event) {

    }

    sendCommand(event){

    }

    render() {
        return (
            <div className="form-group" style={this.style_component}>
                <div className="col-xs-5">
                    <button style={this.style_button} className="btn btn-primary" onClick={this.saveCommand}>
                        Save
                    </button>
                </div>
                <div className="col-xs-offset-10">
                    <button style = {this.style_button} className="btn btn-primary" onClick={this.sendCommand}>
                        Manual Send
                    </button>
                </div>
            </div>
        )

    }
}
class MainLayout extends React.Component {
    constructor(props) {
        super(props);
    }
    render() {
        return (
            <div>
                <div className="row">
                    <ComponentFeedbackMail/>
                </div>
                <div className="row">
                    <ComponentExclusionTarget/>
                </div>
                <div className="row">
                    <ComponentButtonLayout/>
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
