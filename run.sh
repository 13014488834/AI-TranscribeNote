#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

echo "========================================"
echo "  AI 智能会议纪要生成工具"
echo "========================================"
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "[错误] 未找到 Python，请先安装 Python 3.9+"
    echo "下载地址: https://www.python.org/downloads/"
    exit 1
fi

PYTHON=$(command -v python3 || command -v python)

# 检查 .env 文件
if [ ! -f ".env" ]; then
    echo "[提示] 未找到 .env 文件，正在从模板创建..."
    cp .env.example .env
    echo "[提示] 请编辑 .env 文件，填入你的 DeepSeek API Key"
    echo "       获取地址: https://platform.deepseek.com"
    echo ""
fi

# 安装依赖
echo "[1/2] 检查依赖..."
$PYTHON -m pip install -r requirements.txt -q 2>&1

# 启动应用
echo "[2/2] 启动应用..."
echo ""
$PYTHON meeting_summarizer.py
