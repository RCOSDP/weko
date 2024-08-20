# Welcome to invenio-previewer

## It can display several formats of files

- [markdown.md](http://127.0.0.1:5000/records/1/preview?filename=markdown.md)
- [csvfile.csv](http://127.0.0.1:5000/records/1/preview?filename=csvfile.csv)
- [zipfile.zip](http://127.0.0.1:5000/records/1/preview?filename=zipfile.zip)
- [jsonfile.json](http://127.0.0.1:5000/records/1/preview?filename=jsonfile.json)
- [xmlfile.xml](http://127.0.0.1:5000/records/1/preview?filename=xmlfile.xml)
- [notebook.ipynb](http://127.0.0.1:5000/records/1/preview?filename=notebook.ipynb)
- [jpgfile.jpg](http://127.0.0.1:5000/records/1/preview?filename=jpgfile.jpg)
- [pngfile.png](http://127.0.0.1:5000/records/1/preview?filename=pngfile.png)
- [pdffile.pdf](http://127.0.0.1:5000/records/1/preview?filename=pdffile.pdf)

# XSS tests

[XSS](data:text/html;base64,PHNjcmlwdD5hbGVydChkb2N1bWVudC5kb21haW4pPC9zY3JpcHQ+Cg==)
<script>alert(1)</script>
<svg/onload=alert(document.origin)>
<img src='x' onerror='alert(document.domain)' />
