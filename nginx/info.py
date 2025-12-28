#!/usr/bin/env python3
import os
import sys
import platform
import html

# HTTPヘッダーの出力
print("Content-Type: text/html; charset=utf-8")
print()

def generate_table(title, data_dict):
    """辞書データをHTMLのテーブルに変換する""" 
    rows = []
    # キーでソートして見やすくする
    for key in sorted(data_dict.keys()):
        value = data_dict[key]
        rows.append(f""" 
            <tr>
                <td class="e">{html.escape(str(key))}</td>
                <td class="v">{html.escape(str(value))}</td>
            </tr>
        """)

    return f""" 
        <h2>{title}</h2>
        <table>
            {''.join(rows)}
        </table>
    """ 

# HTMLの組み立て
style = """ 
<style>
    body {background-color: #ffffff; color: #000000; font-family: sans-serif;}
    table {border-collapse: collapse; border: 1px solid #000000; width: 934px; margin: 0 auto 20px;}
    .e {background-color: #ccccff; font-weight: bold; color: #000000; width: 300px; border: 1px solid #000000;}
    .v {background-color: #cccccc; color: #000000; border: 1px solid #000000; word-break: break-all;}
    h1 {text-align: center;}
    h2 {text-align: center;}
    td {padding: 4px 8px; font-size: 0.8em;}
</style>
""" 

print(f""" 
<!DOCTYPE html>
<html>
<head>
    <title>pythoninfo()</title>
    {style}
</head>
<body>
    <h1>Python Information</h1>
""")

# 1. Pythonの基本情報
core_info = {
    "Python Version": sys.version,
    "Python Executable": sys.executable,
    "Platform": platform.platform(),
    "Implementation": platform.python_implementation(),
    "Filesystem Encoding": sys.getfilesystemencoding(),
}
print(generate_table("Python Core", core_info))

# 2. CGI環境変数 (PHPの $_SERVER に相当)
print(generate_table("Environment Variables (CGI)", os.environ))

print(""" 
</body>
</html>
""")