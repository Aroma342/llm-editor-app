@echo off
cd /d %~dp0

:: 仮想環境のパスを変数に設定
set VENV_PATH=%~dp0venv

:: 仮想環境が存在しない場合のみ作成
if not exist "%VENV_PATH%" (
    echo 仮想環境が見つかりません。初回セットアップを開始します...
    python -m venv venv
    
    echo 仮想環境を一時的に有効化してインストールを実行します...
    call "%VENV_PATH%\Scripts\activate"
    
    echo ライブラリをインストール中（これには数分かかります）...
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    python -m spacy download ja_ginza
)

:: 起動処理（更新チェックなしの最短ルート）
echo 仮想環境を有効化しています...
call "%VENV_PATH%\Scripts\activate"

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] 仮想環境の有効化に失敗しました。venvフォルダを削除してやり直してください。
    pause
    exit /b
)

echo アプリを起動します...
streamlit run app.py
pause