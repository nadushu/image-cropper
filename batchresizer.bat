@echo off
echo Image Processor Launcher
echo ----------------------

:: Pythonが存在するか確認
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed or not in PATH
    echo Please install Python and try again
    pause
    exit /b
)

:: 必要なライブラリをチェック
python -c "import PIL" >nul 2>&1
if errorlevel 1 (
    echo Installing required library: Pillow
    pip install Pillow
)

:: スクリプトを実行
python "image_processor.py"
if errorlevel 1 (
    echo An error occurred while running the script
    pause
)
pause