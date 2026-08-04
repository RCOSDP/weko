# WEKO3

TODO: WEKO3の説明等をまとめる。

## ディレクトリ構造（整理中）

```
.
├── build                            : 環境構築用ファイル
│   ├── data                         : 環境構築用データ
│   ├── images                       : Dockerイメージ
│   ├── scripts                      : 環境構築スクリプト
│   └── README.md                    : 構築手順
├── dev                              : 開発用ファイル群（開発用イメージには含める）
│   └── README.md                    : 説明
├── modules                          : モジュール（イメージに含める）
│   ├── cookiecutter-weko-module
│   ├── invenio-accounts
│   ├── ~省略~
│   └── weko-workspace
├── tools                            : ツール（イメージに含める）
├── utils                            : その他のツール（イメージに含めない）
├── update                           : アップデート用
│   ├── x.x.x                        : 一つ前からのアップデート用ファイル群（イメージに含める）
│   └── old                          : 過去のアップデート用（イメージに含めない）
│       └── x.x.x                    : vx.x.xのアップデート用ファイル群（イメージに含めない）
├── CHANGELOG_ja.md
├── CHANGELOG.md
├── LICENSE
└── README.md　　　　　　　　　　　　　: このファイル
```