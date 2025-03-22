## 概要
このリポジトリは、Notion のデータベースに新規ページを追加し、既存ページを更新する Python スクリプトを提供します。重複を避けながらデータを管理し、必要に応じて新規作成と更新を自動的に行います。

## ファイル構成
- **main.py**  
  Notion ページを追加・更新するロジックをまとめたスクリプトです。  
- **(非公開)** config.ini  
  認証情報などが含まれるため、公開しないようにご注意ください。

## 環境構築
- **conda環境**
```bash
conda env create -f environment.yml
conda activate notion_env
```
- **pyenv, venv環境**
```bash
pip install -r requirements.txt
```

## 使い方
0. 入力したいjsonファイルを用意して下さい(属性はjson.exampleを参考にしてください)
1. `config.ini` などの必要な設定ファイルを作成し、Notion API のトークンなどを設定してください。  
3. 以下のコマンドを実行します。  
   ```bash
   python merge_json.py /path/to.json
   python main.py merged_output.py
   ```


## 注意事項
- **config.ini** や機密情報は絶対に公開しないようにしてください。
- Notion API を使用するため、事前に [Notion API の利用手順](https://developers.notion.com/) を確認してください。
```