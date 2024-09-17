from flask import Flask, send_from_directory, jsonify

app = Flask(__name__)

# 静的ファイルの提供
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

@app.route('/weko/static/<path:filename>')
def weko_static_files(filename):
    return send_from_directory('weko_static', filename)

# Weko関連のルート
@app.route('/weko/')
def weko_index():
    return 'Weko Index'

@app.route('/weko/auto/login')
def weko_auto_login():
    return 'Weko Auto Login'

@app.route('/weko/confim/user', methods=['POST'])
def weko_confirm_user():
    return 'Weko Confirm User'

@app.route('/weko/shib/login', methods=['GET', 'POST'])
def weko_shib_login():
    return 'Weko Shib Login'

@app.route('/weko/shib/sp/login')
def weko_shib_sp_login():
    return 'Weko Shib SP Login'

@app.route('/weko/shib/logout')
def weko_shib_logout():
    return 'Weko Shib Logout'

# その他のルート
@app.route('/accounts/settings/groups/static/<filename>')
def groups_static_files(filename):
    return send_from_directory('groups_static', filename)

@app.route('/accounts/settings/groups/groupcount')
def group_count():
    return jsonify({'count': 10})

@app.route('/accounts/settings/groups/grouplist')
def group_list():
    return jsonify({'groups': ['group1', 'group2']})

# アプリケーションの起動
if __name__ == '__main__':
    with app.app_context():
        print(app.url_map)
    app.run(debug=True)
