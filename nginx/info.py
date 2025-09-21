#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import cgi
import html
import os
import platform
import sys

def print_section(title, data):
    """指定されたタイトルとデータでHTMLのセクションを生成する"""
    print(f"<h2>{html.escape(title)}</h2>")
    if not data:
        print("<p>No data available.</p>")
        return
    
    print("<table>")
    print("<tr><th>Key</th><th>Value</th></tr>")
    # キーでソートして表示を安定させる
    for key in sorted(data.keys()):
        # 値をエスケープしてXSSを防ぐ
        value = html.escape(str(data[key]))
        print(f"<tr><td>{html.escape(key)}</td><td>{value}</td></tr>")
    print("</table>")

def main():
    """メイン処理"""
    # 1. CGIスクリプトとして必須のHTTPヘッダーを出力
    print("Content-Type: text/html; charset=utf-8")
    print()  # ヘッダーとボディの間の空行

    # 2. HTMLのヘッダーとスタイルの出力
    print("""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <title>Python CGI Environment Info</title>
        <style>
            body { font-family: sans-serif; margin: 2em; }
            h1, h2 { color: #333; }
            table { border-collapse: collapse; width: 100%; margin-bottom: 2em; }
            th, td { border: 1px solid #ccc; padding: 8px; text-align: left; vertical-align: top; word-break: break-all; }
            th { background-color: #f2f2f2; }
            tr:nth-child(even) { background-color: #fafafa; }
            th:first-child, td:first-child {
    width: 25%; /* キー列の幅を25%に設定（この値は調整可能です）*/
    white-space: nowrap; /* キーが長くなっても改行されないようにする */
    font-weight: bold; /* キーを太字にして見やすくする */
}
        </style>
    </head>
    <body>
        <h1>Python CGI Environment Information</h1>
    """)

    # --- Python環境情報の表示 ---
    python_info = {
        "Python Version": sys.version,
        "Python Executable": sys.executable,
        "Module Search Path": "<br>".join(sys.path)
    }
    print_section("🐍 Python Environment", python_info)

    # --- CGI環境変数の表示 ---
    # os.environにサーバー情報やリクエストヘッダーがすべて含まれる
    print_section("⚙️ CGI Environment Variables (os.environ)", os.environ)
    
    # --- GET/POSTデータの表示 ---
    form = cgi.FieldStorage()
    form_data = {}
    for key in form.keys():
        form_data[key] = form.getvalue(key)
    print_section("📋 Form Data (GET/POST)", form_data)
    
    # --- プラットフォーム情報の表示 ---
    platform_info = {
        "System": platform.system(),
        "Node Name": platform.node(),
        "Release": platform.release(),
        "Version": platform.version(),
        "Machine": platform.machine(),
        "Processor": platform.processor(),
    }
    print_section("🖥️ Platform Information", platform_info)

    # 5. HTMLのフッターを出力
    print("""
    </body>
    </html>
    """)

if __name__ == "__main__":
    main()