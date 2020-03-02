class MainLayout extends React.Component {

  constructor() {
    super()
    this.state = {
    }
  }

  render() {
    return (
      <div>
        facet search
      </div>
    )
  }
}

$(function () {
  ReactDOM.render(
    <MainLayout />,
    document.getElementById('app-facet-search')
  )
});
