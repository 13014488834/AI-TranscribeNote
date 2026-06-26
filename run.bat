@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo   AI 智能会议纪要生成工具
echo ========================================
echo.

:: 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.9+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

:: 检查 .env 文件
if not exist ".env" (
    echo [提示] 未找到 .env 文件，正在从模板创建...
    copy .env.example .env >nul
    echo [提示] 请编辑 .env 文件，填入你的 DeepSeek API Key
    echo        获取地址: https://platform.deepseek.com
    echo.
)

:: 安装依赖
echo [1/2] 检查依赖...
pip install -r requirements.txt -q
if errorlevel 1 (
    echo [错误] 依赖安装失败
    pause
    exit /b 1
)

:: 启动应用
echo [2/2] 启动应用...
echo.
python meeting_summarizer.py
pause
