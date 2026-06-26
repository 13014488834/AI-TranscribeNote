"""
AI 会议纪要生成工具 — Streamlit 版
==================================
本地运行：streamlit run web_app.py
云端部署：推送 GitHub 后连接 Streamlit Cloud

与 Gradio 版功能一致：文本/文件输入 → DeepSeek AI 提取 → 导出
"""
import os
import sys
import json
import io
import tempfile
from datetime import datetime
from pathlib import Path

# 将当前目录加入路径，以复用核心模块
sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st
from meeting_summarizer import (
    summarize_meeting,
    parse_file,
    get_history,
    get_meeting_by_id,
    init_db,
    _build_export_content,
    export_markdown,
    export_docx,
    export_pdf,
)

# ==================== 页面配置 ====================
st.set_page_config(
    page_title="AI 会议纪要生成器",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==================== 初始化数据库 ====================
init_db()

# ==================== Session State ====================
if "current_result" not in st.session_state:
    st.session_state.current_result = {}
if "history_search" not in st.session_state:
    st.session_state.history_search = ""


# ==================== 侧边栏：API Key + 历史记录 ====================
with st.sidebar:
    st.title("📋 会议纪要")

    # --- API Key ---
    st.subheader("🔑 DeepSeek API Key")
    env_key = os.getenv("DEEPSEEK_API_KEY", "")
    api_key = st.text_input(
        "API Key",
        value=env_key,
        type="password",
        placeholder="粘贴你的 Key（sk-...）或配置 .env",
        label_visibility="collapsed",
        help="你的 Key 仅在浏览器本地使用，不存储到服务器",
    )
    st.caption("[📎 获取 API Key](https://platform.deepseek.com)")

    st.divider()

    # --- 历史记录 ---
    st.subheader("📋 历史记录")
    search_query = st.text_input(
        "搜索",
        value=st.session_state.history_search,
        placeholder="关键词搜索……",
        label_visibility="collapsed",
        key="search_box",
    )

    records = get_history(search_query) if search_query else get_history()
    if records:
        # 显示最近记录列表
        record_options = {}
        for r in records:
            label = f"{r[1]} | {r[3][:30]}{'…' if len(r[3]) > 30 else ''}"
            record_options[label] = r[0]

        selected_label = st.selectbox(
            "最近记录",
            options=[""] + list(record_options.keys()),
            format_func=lambda x: "— 选择记录 —" if x == "" else x,
            label_visibility="collapsed",
        )

        if selected_label and selected_label in record_options:
            meeting_id = record_options[selected_label]
            record = get_meeting_by_id(meeting_id)
            if record:
                st.session_state.current_result = {
                    "状态": f"📋 历史 #{record['id']} — {record['created_at']}",
                    "争论焦点": record["debate_points"],
                    "最终结论": record["final_conclusion"],
                    "待办事项": record["todo_items"],
                }
                st.rerun()
    else:
        st.caption("暂无历史记录")


# ==================== 主区域 ====================
st.title("📋 AI 智能会议纪要生成工具")
st.caption("粘贴会议记录或上传文件，自动提取争论焦点、结论和待办事项")

# 输入区域
tab1, tab2 = st.tabs(["📝 文本输入", "📁 文件上传"])

with tab1:
    text_input = st.text_area(
        "会议文字记录",
        placeholder="请粘贴会议录音转文字……",
        height=280,
        label_visibility="collapsed",
    )
    col1, col2, col3 = st.columns([1, 1, 3])
    with col1:
        text_submit = st.button("🚀 生成纪要", type="primary", use_container_width=True)

with tab2:
    uploaded_file = st.file_uploader(
        "上传会议文件",
        type=["txt", "docx", "mp3", "wav", "m4a", "flac", "ogg"],
        label_visibility="collapsed",
    )
    col1b, col2b, col3b = st.columns([1, 1, 3])
    with col1b:
        file_submit = st.button("🚀 解析并生成纪要", type="primary", use_container_width=True)

# ==================== 处理逻辑 ====================
if text_submit and text_input.strip():
    with st.spinner("AI 正在分析会议内容……"):
        result = summarize_meeting(
            text_input, source_type="text", source_name="手动输入", api_key=api_key
        )
        st.session_state.current_result = result
    st.rerun()

if file_submit and uploaded_file is not None:
    with st.spinner("正在解析文件……"):
        # 保存上传文件到临时目录
        suffix = Path(uploaded_file.name).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded_file.getvalue())
            tmp_path = tmp.name

        text, name, err = parse_file(tmp_path, uploaded_file.name)
        os.unlink(tmp_path)  # 清理临时文件

        if err:
            st.session_state.current_result = {
                "状态": f"❌ 文件解析失败",
                "错误信息": err,
                "争论焦点": "",
                "最终结论": "",
                "待办事项": [],
            }
        else:
            with st.spinner("AI 正在分析会议内容……"):
                result = summarize_meeting(
                    text, source_type="file", source_name=name, api_key=api_key
                )
                st.session_state.current_result = result
    st.rerun()

# ==================== 结果展示 ====================
result = st.session_state.current_result

if result and result.get("争论焦点"):
    st.divider()
    st.subheader("📊 结构化会议纪要")

    status = result.get("状态", "")
    if "✅" in status:
        st.success(status)
    elif "⚠️" in status or "❌" in status:
        st.warning(status) if "⚠️" in status else st.error(status)
        if result.get("提示"):
            st.info(result["提示"])
        if result.get("错误信息"):
            st.error(result["错误信息"])
    else:
        st.info(status)

    # 争论焦点
    with st.expander("💬 争论焦点", expanded=True):
        st.write(result.get("争论焦点", "（无）"))

    # 最终结论
    with st.expander("✅ 最终结论", expanded=True):
        st.write(result.get("最终结论", "（无）"))

    # 待办事项
    with st.expander("📝 待办事项", expanded=True):
        todos = result.get("待办事项", [])
        if todos:
            for i, item in enumerate(todos, 1):
                task = item.get("任务", item.get("task", ""))
                person = item.get("负责人", item.get("person", ""))
                st.markdown(f"{i}. **{task}**  — *{person}*")
        else:
            st.write("（无）")

    # ==================== 导出按钮 ====================
    st.divider()
    st.subheader("📥 导出")
    c1, c2, c3, c4 = st.columns(4)

    # Markdown 导出
    md_content = _build_export_content(result)
    with c1:
        st.download_button(
            "📥 导出 Markdown",
            data=md_content,
            file_name=f"会议纪要_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown",
            use_container_width=True,
        )

    # Word 导出
    with c2:
        try:
            docx_path = export_docx(result)
            if docx_path and os.path.exists(docx_path):
                with open(docx_path, "rb") as f:
                    docx_bytes = f.read()
                st.download_button(
                    "📥 导出 Word",
                    data=docx_bytes,
                    file_name=f"会议纪要_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True,
                )
        except Exception:
            st.button("📥 导出 Word", disabled=True, use_container_width=True,
                      help="python-docx 未安装")

    # PDF 导出
    with c3:
        try:
            pdf_path = export_pdf(result)
            if pdf_path and os.path.exists(pdf_path):
                with open(pdf_path, "rb") as f:
                    pdf_bytes = f.read()
                st.download_button(
                    "📥 导出 PDF",
                    data=pdf_bytes,
                    file_name=f"会议纪要_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
        except Exception:
            st.button("📥 导出 PDF", disabled=True, use_container_width=True,
                      help="fpdf2 未安装")

elif result and not result.get("争论焦点"):
    # 有错误或提示信息
    st.divider()
    status = result.get("状态", "")
    if status:
        st.warning(status)
    hint = result.get("提示", result.get("错误信息", ""))
    if hint:
        st.info(hint)

# ==================== 页脚 ====================
st.divider()
st.caption(
    "Built with Streamlit + DeepSeek + LangChain | "
    "[GitHub](https://github.com/13014488834/AI-TranscribeNote) | "
    "API Key 仅在浏览器本地使用"
)
