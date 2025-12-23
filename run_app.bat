@echo off
cd /d %~dp0

:: 仮想環境が存在しない場合のみ作成とインストールを実行
if not exist venv (
    echo 仮想環境が見つかりません。初回セットアップを開始します...
    python -m venv venv
    call venv\Scripts\activate
    echo ライブラリをインストールしています...
    pip install -r requirements.txt
    python -m spacy download ja_ginza
) else (
    echo 仮想環境を有効化しています...
    call venv\Scripts\activate
)

echo アプリを起動します...
streamlit run app.py
pause