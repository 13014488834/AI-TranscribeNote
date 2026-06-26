"""
AI 会议纪要生成工具 — Hugging Face Spaces 入口
===============================================
在线版：浏览器打开即用，在页面输入 DeepSeek API Key 即可生成纪要。
本地版：运行 python meeting_summarizer.py 或双击 run.bat。

部署方式：将整个仓库上传到 Hugging Face Spaces（SDK: Gradio）。
"""
from meeting_summarizer import demo

if __name__ == "__main__":
    demo.launch()
