import React from "react";
import RGL, { WidthProvider } from "react-grid-layout";

const ReactGridLayout = WidthProvider(RGL);

/**
 * WEKO layout
 */
class StaticElementsLayout extends React.PureComponent {
  constructor(props) {
    super(props);

    this.onLayoutChange = this.onLayoutChange.bind(this);
  }

  onLayoutChange(layout) {
    this.props.onLayoutChange(layout);
  }

  render() {
    return (
      <ReactGridLayout
        className="layout"
        onLayoutChange={this.onLayoutChange}
        rowHeight={30}
      >
        <div key="2" data-grid={{ x: 0, y: 0, w: 2, h: 3 }}>
          <span className="text">新着アイテム</span>
        </div>
        <div key="3" data-grid={{ x: 0, y: 3, w: 2, h: 9 }}>
          <span className="text">お知らせ</span>
        </div>
        <div
          key="1"
          data-grid={{
            x: 2,
            y: 0,
            w: 10,
            h: 12,
            draggableHandle: ".react-grid-dragHandleExample"
          }}
        >
          <iframe id="main" title="weko" width="100%" height="100%" src="/"></iframe>
        </div>
      </ReactGridLayout>
    );
  }
}

module.exports = StaticElementsLayout;

if (require.main === module) {
  require("../test-hook.jsx")(module.exports);
}
