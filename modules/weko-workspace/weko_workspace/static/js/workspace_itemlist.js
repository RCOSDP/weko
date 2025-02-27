class DynamicContent extends React.Component {
    state = {
        data: null,
        loading: true,
        error: null
    };

    // 组件挂载时获取数据
    componentDidMount() {
        this.fetchContent();
    }

    // 获取数据的函数
    fetchContent = async () => {
        try {
            // 假设你的 api.py 提供了一个 /api/content 端点
            const response = await fetch('/workspace/get_workspace_itemlist');
            console.log("response : ", response);
            console.log("js-----1111");
            const data = await response.json();
            // const data = await response.url;
            console.log("data : ", data);
            console.log("js-----22222");
            this.setState({
                data: data,
                loading: false
            });
        } catch (error) {
            this.setState({
                error: error.message,
                loading: false
            });
        }
    };

    render() {
        const { data, loading, error } = this.state;

        if (loading) {
            return React.createElement('div', null, 'Loading...');
        }

        if (error) {
            return React.createElement('div', null, `Error: ${error}`);
        }

        return React.createElement(
            'div',
            { className: 'dynamic-content' },
            data && React.createElement(
                'div',
                null,
                React.createElement('h2', null, data.title),
                React.createElement('p', null, data.body)
                // React.createElement('p', null, data)
            )
        );
    }
}

// 渲染 React 组件到 DOM
ReactDOM.render(
    React.createElement(DynamicContent),
    document.getElementById('root')
);