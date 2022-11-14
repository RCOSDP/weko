//poファイル定義の文言をhiddenから取得
const reindex_item_index = document.getElementById("reindex_item_index").value;
const reindex_item = document.getElementById("reindex_item").value;
const execute = document.getElementById("execute").value;
const waiting = document.getElementById("waiting").value;
const haserror = document.getElementById("haserror").value;
const executing = document.getElementById("executing").value;
const run_label = document.getElementById("run").value;
const cancel_label = document.getElementById("cancel").value;

// TODO: poファイルへ
const validationMsg1 = "どちらかチェックしてください。";
const confirmMessage = "本処理の実行にはかなりの時間がかかることが予想されます。インデックスの再作成処理を実行してよいですか？";

/** close ErrorMessage area */
function closeError() {
    $('#errors').empty();
}

/** show ErrorMessage */
function showErrorMsg(msg) {
    $('#errors').append(
        '<div class="alert alert-danger alert-dismissable">' +
        '<button type="button" class="close" data-dismiss="alert" aria-hidden="true">' +
        '&times;</button>' + msg + '</div>');
}

class MainLayout extends React.Component {
    constructor() {
        super();
        const err = JSON.parse(document.getElementById("isError").value.toLowerCase())
        const exe = JSON.parse(document.getElementById("isExecuting").value.toLowerCase())
        this.state = {
            isError: err
            ,isExecuting: exe
            ,disabled_Btn: err || exe
            ,showModal:false
            ,riiChecked : false
            ,riChecked : false
        }
        this.handleClickExecute = this.handleClickExecute.bind(this);
        this.handleCheckedChange = this.handleCheckedChange.bind(this);
        this.handleClose = this.handleClose.bind(this);
        this.handleExecute = this.handleExecute.bind(this);

    }

    /** 画面実行ボタン押下 */
    handleClickExecute(event){
        const riiChecked = document.getElementById("reindex_item_index").checked;
        const riChecked  = document.getElementById("reindex_item").checked;
        //validation
        if(!(riiChecked || riChecked)){
            return showErrorMsg(validationMsg1);
        }

        this.setState({
            showModal: true
        });
    }

    /** チェックボックス変更 */
    handleCheckedChange(event){
        if (event.target.id === 'reindex_item_index'){
            this.setState({
                riiChecked: event.target.checked
            });
        }

        if (event.target.id === "reindex_item"){
            this.setState({
                riChecked: event.target.checked
            });
        }
    }

    /** モーダル閉じる */
    handleClose() {
        this.setState({
            showModal: false
            // ,is_agree_doi: false
        });
    }

    /** モーダル実行ボタン押下 */
    handleExecute(){

        //モーダル閉じる
        closeError();
        const riiChecked = document.getElementById("reindex_item_index").checked;
        const riChecked  = document.getElementById("reindex_item").checked;
        this.setState({
            disabled_Btn: true
            ,isExecuting: true
            ,showModal: false
        });
        return this.execRii(riiChecked)
        .then((res) => {
            console.log(res);
            return this.execRi(riChecked);
        })
        .then((res) => {
            showErrorMsg(res);
            const execBtn = document.getElementById("execute");
            execBtn.setAttribute("disabled",false);
            this.setState({
                disabled_Btn: false
                ,isError: false
                ,isExecuting: false
            });
            // this.render();
        })
        .catch((e) => {
            showErrorMsg(e);
            this.setState({
                disabled_Btn: true
                ,isError: true
            });
        });

    }

    render() {
        const html = (
            <div>
                <div class="panel">
                    <div class="panel-body">
                        <div>
                            <input type="checkbox" id="reindex_item_index" checked={this.state.riiChecked} onChange={this.handleCheckedChange} />
                            <label for="reindex_item_index">
                                {reindex_item_index}
                            </label>
                        </div>
                        <div>
                            <input type="checkbox" id="reindex_item" checked={this.state.riChecked} onChange={this.handleCheckedChange}/>
                            <label for="reindex_item">
                                {reindex_item}
                            </label>
                        </div>
                        <div class="row">
                            <div class="form-actions">
                                <button type="submit" id="execute" name="execute" value="save_ranking_settings" class="btn btn-primary" 
                                onClick={this.handleClickExecute} disabled={this.state.disabled_Btn}>{execute}
                                </button>
                                <span>
                                    {this.state.isError? haserror :this.state.isExecuting? executing : waiting}
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
                <div className="export_component">
                    <ReactBootstrap.Modal show={this.state.showModal} onHide={this.handleClose} dialogClassName="w-725">
                        <ReactBootstrap.Modal.Header closeButton></ReactBootstrap.Modal.Header>
                        <ReactBootstrap.Modal.Body>
                            <div className="col-12">
                                <div className="row text-center">
                                    {confirmMessage}
                                </div>
                            </div>
                        </ReactBootstrap.Modal.Body>
                        <ReactBootstrap.Modal.Footer>
                            <div className="col-12">
                                <div className="row text-center">
                                    <button variant="primary" type="button" className="btn btn-default" onClick={this.handleExecute}>{run_label}</button>
                                    <button variant="secondary" type="button" className="btn btn-default cancel" onClick={this.handleClose}>{cancel_label}</button>
                                </div>
                            </div>
                        </ReactBootstrap.Modal.Footer>
                    </ReactBootstrap.Modal>
                </div>
            </div>
        );
        
        return html;
    }

    
    /** 機能の実行 */
    async execRii(riiChecked) {

        const url = window.location.href;
        if(riiChecked){
            // TODO: うまく動作していない。
            return $.ajax({
                url: url + 'reindex_items',
                type: 'GET',
                dataType: "json",
                async: false,
                success: (response) => {
                    return response.Body === 200 ? resolve(response) : reject(response)
                },
                error: (error) => {return reject(error)}
            });
        }
        return this;
    }
    async execRi(riChecked) {

        const url = window.location.href;
        if(riChecked){
            // TODO: うまく動作していない。
            return $.ajax({
                url: url + 'reindex_itemindexes',
                type: 'GET',
                dataType: "json",
                async: false,
                success: (response) => {
                    return response.Body === 200 ? resolve(response) : reject(response)
                },
                error: (error) => {return reject(error)}
            });
        }
        return this;
    }

}

$(function () {
    ReactDOM.render(
        <MainLayout />,
        document.getElementById('root')
    )
});
