# 📋 AI Meeting Minutes Generator / AI 智能会议纪要生成工具

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![Gradio](https://img.shields.io/badge/Gradio-4.x-orange.svg)](https://www.gradio.app/)

An intelligent meeting minutes extraction tool powered by **DeepSeek + LangChain + Pydantic**. Paste meeting transcripts or upload files — it automatically extracts **debate points**, **final conclusions**, and **action items**. Supports history search and multi-format export.

基于 **Gradio + DeepSeek + LangChain + Pydantic** 的智能会议纪要结构化提取工具。输入会议文字记录或上传文件，自动提取**争论焦点**、**最终结论**和**待办事项**，支持历史检索与多格式导出。

> 🌐 **English** | [中文](#中文)

---

## ✨ Features / 核心功能

| Feature | Description |
|---------|-------------|
| 🧠 **AI Structured Extraction** | DeepSeek LLM with Pydantic Schema-enforced JSON output — debate points, conclusions, action items |
| 📁 **Multi-format Upload** | `.txt` / `.docx` parsing + `.mp3` / `.wav` / `.m4a` speech-to-text (Whisper) |
| 📋 **History Management** | SQLite local storage with keyword search and instant recall |
| 📥 **One-click Export** | Markdown / Word(.docx) / PDF export |

## 🚀 Quick Start

### 1. Requirements

- Python 3.9+
- (Optional) `ffmpeg` — only needed for audio transcription

### 2. Install

```bash
pip install -r requirements.txt
```

### 3. Configure API Key

```bash
cp .env.example .env
# Edit .env and add your DeepSeek API key
```

> Get your API key at [platform.deepseek.com](https://platform.deepseek.com)

### 4. Launch

```bash
# Windows
run.bat

# Mac / Linux
bash run.sh

# Or directly
python meeting_summarizer.py
```

Browser opens at `http://127.0.0.1:7860`

> 💡 **No API key?** The app still launches — you can explore the UI. Generation will show a friendly setup guide.

## 🏗️ Architecture / 技术架构

```
┌──────────────────────────────────────────────────┐
│                  Gradio Web UI                    │
│   ┌──────────┐  ┌──────────────┐  ┌───────────┐  │
│   │  Text     │  │  File Upload │  │  History   │  │
│   └────┬─────┘  └──────┬───────┘  └─────┬─────┘  │
│        │               │               │         │
│   ┌────┴───────────────┴───────────────┴─────┐   │
│   │        Core: Pydantic Schema + LLM         │   │
│   │   DeepSeek Chat API + Structured Output    │   │
│   └────────────────────┬──────────────────────┘   │
│                        │                          │
│   ┌────────────────────┼──────────────────────┐   │
│   │  SQLite Storage  │  Export (MD/DOCX/PDF)   │   │
│   └────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────┘
```

### Tech Stack / 技术栈

- **UI**: Gradio 4.x
- **LLM**: DeepSeek Chat via `langchain-deepseek`
- **Structured Output**: LangChain `with_structured_output` + Pydantic v2
- **Storage**: SQLite3 (thread-safe with `threading.Lock`)
- **File Parsing**:
  - `.txt` → auto-detect encoding (UTF-8 / GBK)
  - `.docx` → `python-docx`
  - Audio → OpenAI Whisper `tiny` (lazy-loaded, ~75MB)
- **Export**: `python-docx` (Word), `fpdf2` (PDF with CJK fonts)

## 📁 Project Structure / 项目结构

```
AI-TranscribeNote/
├── meeting_summarizer.py    # Main app
├── requirements.txt         # Python dependencies
├── run.bat                  # Windows launcher
├── run.sh                   # Linux/Mac launcher
├── .env.example             # API key template
├── .gitignore
├── LICENSE                  # MIT
└── README.md
```

## 🔧 Design Highlights / 设计要点

- **Lazy initialization**: LLM & Whisper models load on first use — fast startup
- **Auto dependency check**: missing packages installed automatically on launch
- **Encoding resilience**: auto-fallback UTF-8 → GBK for Chinese Windows
- **Thread safety**: SQLite operations protected by `threading.Lock`
- **Graceful degradation**: optional deps missing → feature disabled, not crashed
- **Friendly onboarding**: app launches without API key, shows setup guide in UI

---

<a name="中文"></a>

## 📖 中文使用指南

### 文本输入
1. 在「📝 文本输入」Tab 粘贴会议文字记录
2. 点击「🚀 生成纪要」
3. 右侧展示结构化 JSON 结果

### 文件上传
1. 切换到「📁 文件上传」Tab
2. 上传会议文件（支持 txt / docx / mp3 等）
3. 系统自动解析并生成纪要

### 历史回顾
- 左侧面板展示最近 50 条记录
- 支持关键词搜索（模糊匹配原文、争论焦点、结论）
- 点击任意记录即可回看详情

### 导出
- 生成纪要后，点击底部按钮导出为 Markdown / Word / PDF

---

## ⚠️ 注意事项

1. 音频转文字需要安装 `ffmpeg`：[下载地址](https://ffmpeg.org/download.html)
2. Whisper 模型首次使用时会自动下载（约 75MB），请耐心等待
3. 长文本（>8000字）会自动截断处理

## 📄 License

MIT — 自由使用、修改、分发。
