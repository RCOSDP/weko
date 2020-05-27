const VERSION_CONTROLLER_LABEL = document.getElementById(
  "component-version-label"
).value;
const UPGRADE_RADIO_BUTTON_LABEL = document.getElementById(
  "upgrade-radiobutton-label"
).value;
const EDIT_RADIO_BUTTON_LABEL = document.getElementById(
  "edit-radiobutton-label"
).value;

class MainLayout extends React.Component {
  constructor(props) {
    super(props);
  }

  render() {
    return (
      <div className="row">
        <div class="form-group">
          <label class="control-label col-sm-3 text-right">
            {VERSION_CONTROLLER_LABEL}
          </label>
          <div class="col-sm-9">
            <label class="col-sm-3">
              <input type="radio" name="radioVersionSelect" value="update" />{" "}
              {UPGRADE_RADIO_BUTTON_LABEL}
            </label>
            <label class="col-sm-3">
              <input type="radio" name="radioVersionSelect" value="keep" />{" "}
              {EDIT_RADIO_BUTTON_LABEL}
            </label>
          </div>
        </div>
      </div>
    );
  }
}

$(function () {
  ReactDOM.render(
    <MainLayout />,
    document.getElementById("react-component-version")
  );
});
