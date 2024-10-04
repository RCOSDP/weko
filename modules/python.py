from flask import Flask, render_template, request, jsonify
import requests
import re
import base64

app = Flask(__name__)

GITHUB_REPO = "Shintetsu-qz/weko"
GITHUB_PATH = "weko/modules"
GITHUB_BRANCH = "1001_hb2u"

def similarity(s1, s2):
    return sum(a == b for a, b in zip(s1, s2)) / max(len(s1), len(s2))

def get_file_content(file_url):
    response = requests.get(file_url)
    if response.status_code == 200:
        content = response.json()['content']
        return base64.b64decode(content).decode('utf-8')
    else:
        raise Exception(f"Failed to fetch file content: {response.status_code}")

def search_github(folder_name, method_name):
    api_url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_PATH}"
    response = requests.get(api_url, params={"ref": GITHUB_BRANCH})
    if response.status_code != 200:
        raise Exception(f"Failed to access GitHub repository: {response.status_code}")

    contents = response.json()
    for item in contents:
        if item['type'] == 'dir' and folder_name in item['name']:
            test_dir_url = f"{api_url}/{item['name']}/tests"
            test_response = requests.get(test_dir_url, params={"ref": GITHUB_BRANCH})
            if test_response.status_code == 200:
                test_contents = test_response.json()
                for test_file in test_contents:
                    if test_file['name'].endswith('.py') and 'tasks' in test_file['name']:
                        file_content = get_file_content(test_file['url'])
                        methods = re.findall(r'def\s+(\w+)', file_content)
                        for method in methods:
                            if similarity(method, method_name) > 0.7:
                                return f".tox/c1/bin/pytest --cov=weko-deposit tests/{test_file['name']}::test_{method} -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/invenio-stats/.tox/c1/tmp --full-trace"
    return None

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        input_text = request.form['input']
        parts = input_text.split('/')
        if len(parts) < 2:
            return jsonify({"error": "Invalid input format."})
        
        folder_name, file_name = parts[-2], parts[-1]
        method_name = file_name.replace('.py', '')
        
        try:
            result = search_github(folder_name, method_name)
            if result:
                return jsonify({"result": result})
            else:
                return jsonify({"error": "No matching file or method found in the GitHub repository."})
        except Exception as e:
            return jsonify({"error": str(e)})
    
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)