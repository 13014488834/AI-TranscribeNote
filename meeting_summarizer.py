"""
AI 会议纪要结构化生成工具 — Gradio 版
======================================
Gradio Web 界面入口。核心逻辑已拆分到 core / db / parser / export 模块。

运行：python meeting_summarizer.py
"""
import subprocess
import sys
import importlib.util

# ==================== 自动安装依赖 ====================
DEP_MAP = {
    "gradio": "gradio",
    "langchain-deepseek": "langchain_deepseek",
    "python-dotenv": "dotenv",
    "pydantic": "pydantic",
    "python-docx": "docx",
    "fpdf2": "fpdf",
    "openai-whisper": "whisper",
}


def ensure_dependencies() -> None:
    """检查并自动安装缺失的 Python 包"""
    for pip_name, module_name in DEP_MAP.items():
        if importlib.util.find_spec(module_name) is None:
            tag = "（可选）" if pip_name == "openai-whisper" else ""
            print(f"[依赖检查] 缺少 {pip_name} {tag}，正在安装...")
            try:
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", pip_name],
                    stdout=sys.stdout, stderr=sys.stderr,
                )
            except Exception as e:
                if pip_name == "openai-whisper":
                    print(f"[依赖检查] openai-whisper 安装失败，音频功能不可用: {e}")
                else:
                    raise
        else:
            print(f"[依赖检查] {pip_name} 已安装，跳过。")


ensure_dependencies()

# ==================== 导入依赖 ====================
import os
from typing import List, Optional, Tuple

import gradio as gr

# 从拆分后的模块导入（所有模块已独立可测）
from config import API_KEY_FROM_ENV
from core import summarize_meeting
from db import init_db, get_history, get_meeting_by_id
from parser import parse_file
from export import export_markdown, export_docx, export_pdf, _build_export_content


# ==================== Gradio 事件处理 ====================
def _refresh_history_choices(search: str = "") -> list:
    """刷新历史记录 Radio 的可选项"""
    records = get_history(search)
    if not records:
        return []
    return [
        (f"{r[1]} | {r[3][:35]}{'...' if len(r[3]) > 35 else ''}", r[0])
        for r in records
    ]


def on_text_submit(text: str, api_key: str = "") -> Tuple[dict, dict, dict]:
    """文本输入 → 生成纪要 + 刷新历史 + 更新导出状态"""
    result = summarize_meeting(text, "text", "手动输入", api_key=api_key)
    choices = _refresh_history_choices()
    return result, gr.update(choices=choices, value=None), result


def on_file_submit(file, api_key: str = "") -> Tuple[dict, dict, dict]:
    """文件上传 → 解析 → 生成纪要 + 刷新历史 + 更新导出状态"""
    empty = {"状态": "⚠️ 未选择文件", "争论焦点": "", "最终结论": "", "待办事项": []}
    if file is None:
        return empty, gr.update(choices=_refresh_history_choices(), value=None), empty

    file_path = file if isinstance(file, str) else file.name
    file_name = os.path.basename(file_path)
    text, name, err = parse_file(file_path, file_name)
    if err:
        empty["状态"] = "❌ 文件解析失败"
        empty["错误信息"] = err
        return empty, gr.update(choices=_refresh_history_choices(), value=None), empty

    result = summarize_meeting(text, "file", name, api_key=api_key)
    choices = _refresh_history_choices()
    return result, gr.update(choices=choices, value=None), result


def on_history_select(selected_str: str) -> Tuple[dict, Optional[str], Optional[str], dict]:
    """用户点击历史记录 → 加载详情"""
    empty: dict = {}
    if not selected_str:
        return empty, None, None, empty
    record = get_meeting_by_id(selected_str)
    if record is None:
        return {"状态": "⚠️ 记录未找到", "争论焦点": "", "最终结论": "", "待办事项": []}, None, None, empty
    result = {
        "状态": f"📋 历史记录 #{record['id']} — {record['created_at']}",
        "来源": record["source_name"],
        "争论焦点": record["debate_points"],
        "最终结论": record["final_conclusion"],
        "待办事项": record["todo_items"],
    }
    return result, None, None, result


def on_history_search(query: str) -> dict:
    """搜索历史记录"""
    choices = _refresh_history_choices(query)
    return gr.update(choices=choices, value=None)


def on_export_md(state: dict) -> Optional[str]:
    if not state or not state.get("争论焦点"):
        return None
    return export_markdown(state)


def on_export_docx(state: dict) -> Optional[str]:
    if not state or not state.get("争论焦点"):
        return None
    return export_docx(state)


def on_export_pdf(state: dict) -> Optional[str]:
    if not state or not state.get("争论焦点"):
        return None
    return export_pdf(state)


# ==================== Gradio Web 界面 ====================
init_db()

with gr.Blocks(title="AI智能会议纪要生成工具") as demo:
    current_result = gr.State({})

    gr.Markdown("""
    # 📋 AI智能会议纪要生成工具
    输入会议文字记录或上传文件，自动提取争论焦点、结论和待办事项
    """)

    gr.Markdown("### 🔑 DeepSeek API Key")
    with gr.Row():
        api_key_input = gr.Textbox(
            label="",
            placeholder="粘贴你的 DeepSeek API Key（sk-...），或留空使用 .env 配置",
            type="password",
            scale=3,
            value=API_KEY_FROM_ENV or "",
        )
        gr.Markdown("[📎 获取 API Key](https://platform.deepseek.com) ｜ 你的 Key 仅在浏览器本地使用，不存储到服务器", scale=2)

    with gr.Row():
        with gr.Column(scale=1, min_width=220):
            gr.Markdown("### 📋 历史记录")
            search_box = gr.Textbox(label="搜索", placeholder="输入关键词筛选……", scale=1)
            history_radio = gr.Radio(
                choices=_refresh_history_choices(), label="最近记录", interactive=True,
            )

        with gr.Column(scale=3, min_width=500):
            with gr.Tabs():
                with gr.Tab("📝 文本输入"):
                    text_input = gr.Textbox(
                        label="会议文字记录", placeholder="请粘贴会议录音转文字……", lines=12,
                    )
                    text_submit_btn = gr.Button("🚀 生成纪要", variant="primary", size="lg")
                with gr.Tab("📁 文件上传"):
                    file_input = gr.File(
                        label="上传会议文件",
                        file_types=[".txt", ".docx", ".mp3", ".wav", ".m4a", ".flac", ".ogg"],
                    )
                    file_submit_btn = gr.Button("🚀 解析并生成纪要", variant="primary", size="lg")

            output_json = gr.JSON(label="结构化会议纪要")

            with gr.Row():
                export_md_btn = gr.DownloadButton("📥 导出 Markdown")
                export_docx_btn = gr.DownloadButton("📥 导出 Word")
                export_pdf_btn = gr.DownloadButton("📥 导出 PDF")

    # ==================== 事件绑定 ====================
    text_submit_btn.click(
        fn=lambda txt, key: on_text_submit(txt, str(key or "")),
        inputs=[text_input, api_key_input],
        outputs=[output_json, history_radio, current_result],
    )
    file_submit_btn.click(
        fn=lambda f, key: on_file_submit(f, str(key or "")),
        inputs=[file_input, api_key_input],
        outputs=[output_json, history_radio, current_result],
    )
    search_box.change(fn=on_history_search, inputs=search_box, outputs=history_radio)
    history_radio.change(
        fn=on_history_select, inputs=history_radio,
        outputs=[output_json, export_md_btn, export_docx_btn, current_result],
    )
    export_md_btn.click(fn=on_export_md, inputs=current_result, outputs=export_md_btn)
    export_docx_btn.click(fn=on_export_docx, inputs=current_result, outputs=export_docx_btn)
    export_pdf_btn.click(fn=on_export_pdf, inputs=current_result, outputs=export_pdf_btn)


# ==================== 启动入口 ====================
if __name__ == "__main__":
    init_db()
    print(f"[初始化] 数据库路径：{__import__('config').DB_PATH}")
    print(f"[初始化] 导出目录：{__import__('config').EXPORT_DIR}")

    demo.launch(
        inbrowser=True,
        theme=gr.themes.Soft(),
        css="""
            * { font-family: "Microsoft YaHei", "微软雅黑", sans-serif; }
        """,
    )
