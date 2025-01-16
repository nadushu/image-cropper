@echo off
setlocal enabledelayedexpansion

:: Pythonがインストールされているか確認
python --version > nul 2>&1
if errorlevel 1 (
    echo Python is not installed. Please install Python first.
    pause
    exit /b
)

:: 必要なパッケージをインストール
echo Installing required packages...
python -m pip install --upgrade pip
python -m pip install pillow tkinterdnd2

:: スクリプトのディレクトリに移動
cd /d "%~dp0"

:: メインスクリプトを実行
echo Starting Image Cropper...
python image_cropper.py

if errorlevel 1 (
    echo An error occurred while running the application.
    pause
)

exit /b