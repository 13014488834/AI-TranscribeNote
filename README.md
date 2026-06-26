# 📋 AI 智能会议纪要生成工具

基于 **Gradio + DeepSeek + LangChain + Pydantic** 的智能会议纪要结构化提取工具。输入会议文字记录或上传文件，自动提取**争论焦点**、**最终结论**和**待办事项**，支持历史检索与多格式导出。

## ✨ 核心功能

| 功能 | 说明 |
|------|------|
| 🧠 **AI 结构化提取** | 基于 DeepSeek 大模型，强制按 Pydantic Schema 输出 JSON，提取争论焦点 / 最终结论 / 待办事项 |
| 📁 **多格式文件上传** | 支持 `.txt` / `.docx` 文本解析，以及 `.mp3` / `.wav` / `.m4a` 语音转文字（Whisper） |
| 📋 **历史记录管理** | SQLite 本地存储，左侧面板关键词检索，点击回看任意历史纪要 |
| 📥 **一键导出** | 支持 Markdown / Word(.docx) / PDF 三种格式导出 |

## 🏗️ 技术架构

```
┌──────────────────────────────────────────────────┐
│                  Gradio Web UI                    │
│   ┌──────────┐  ┌──────────────┐  ┌───────────┐  │
│   │ 文本输入  │  │  文件上传     │  │ 历史记录   │  │
│   └────┬─────┘  └──────┬───────┘  └─────┬─────┘  │
│        │               │               │         │
│   ┌────┴───────────────┴───────────────┴─────┐   │
│   │           核心处理层 (Pydantic Schema)      │   │
│   │   DeepSeek Chat API + Structured Output    │   │
│   └────────────────────┬──────────────────────┘   │
│                        │                          │
│   ┌────────────────────┼──────────────────────┐   │
│   │  SQLite 持久化  │  导出层 (MD/DOCX/PDF)    │   │
│   └────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────┘
```

### 技术栈

- **UI 框架**: Gradio 4.x（响应式 Web 界面）
- **大模型**: DeepSeek Chat API（`langchain-deepseek` 集成）
- **结构化输出**: LangChain `with_structured_output` + Pydantic v2 强制 Schema 校验
- **数据持久化**: SQLite3（线程安全，`threading.Lock` 并发控制）
- **文件解析**:
  - `.txt` → 原生解析（UTF-8 / GBK 自动检测编码）
  - `.docx` → `python-docx` 段落提取
  - `.mp3/.wav/.m4a` → OpenAI Whisper `tiny` 模型语音转文字（懒加载，首次使用 ~75MB）
- **文档导出**: `python-docx`（Word）、`fpdf2`（PDF，中文字体渲染）

## 🚀 快速开始

### 1. 环境要求

- Python 3.9+
- （可选）`ffmpeg` — 仅音频转文字功能需要

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置 API Key

```bash
cp .env.example .env
# 编辑 .env，填入你的 DeepSeek API Key
```

> 从 [platform.deepseek.com](https://platform.deepseek.com) 获取 API Key

### 4. 启动应用

```bash
python meeting_summarizer.py
```

浏览器将自动打开 `http://127.0.0.1:7860`

## 📖 使用指南

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
- 导出文件保存在 `exports/` 目录

## 📁 项目结构

```
AI会议纪要/
├── meeting_summarizer.py    # 主程序（Gradio UI + 业务逻辑）
├── requirements.txt         # Python 依赖
├── .env                     # 环境变量（API Key，不提交）
├── .env.example             # 环境变量模板
├── .gitignore
├── meetings.db              # SQLite 数据库（本地历史记录）
├── exports/                 # 导出文件目录
└── README.md
```

## 🔧 设计要点

- **自动依赖安装**: 启动时自动检测并安装缺失的 Python 包，降低使用门槛
- **懒加载 Whisper**: 仅在首次使用音频功能时才下载模型，避免不必要的资源消耗
- **编码兼容**: `.txt` 解析自动尝试 UTF-8 → GBK，兼容 Windows 中文环境
- **线程安全**: SQLite 操作使用 `threading.Lock` 保护，避免并发写入冲突
- **容错设计**: 数据库写入失败不影响主流程；可选依赖缺失时优雅降级
- **长文本截断**: 超过 8000 字自动截断并提示用户

## 📄 License

MIT
