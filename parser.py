"""文件解析层 — 支持 .txt / .docx / 音频文件"""
import os
from pathlib import Path

# 可选依赖
try:
    from docx import Document as DocxDocument
    DOCX_OK = True
except ImportError:
    DOCX_OK = False

try:
    import whisper
    WHISPER_OK = True
except ImportError:
    WHISPER_OK = False

# Whisper 模型懒加载
_whisper_model = None


def _get_whisper_model():
    """懒加载 Whisper 模型（tiny 模型约 75MB）"""
    global _whisper_model
    if _whisper_model is None and WHISPER_OK:
        print("[Whisper] 正在加载语音识别模型 (tiny)...")
        _whisper_model = whisper.load_model("tiny")
        print("[Whisper] 模型加载完成。")
    return _whisper_model


def parse_txt(file_path: str) -> tuple[str, str | None]:
    """读取纯文本文件，返回 (内容, 错误)"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        if not content.strip():
            return "", "文件内容为空。"
        return content, None
    except UnicodeDecodeError:
        try:
            with open(file_path, "r", encoding="gbk") as f:
                return f.read(), None
        except Exception as e:
            return "", f"文件编码错误：{e}"
    except Exception as e:
        return "", f"读取文件失败：{e}"


def parse_docx(file_path: str) -> tuple[str, str | None]:
    """读取 Word 文档，提取所有段落文本"""
    if not DOCX_OK:
        return "", "缺少 python-docx 依赖，无法解析 .docx 文件。"
    try:
        doc = DocxDocument(file_path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        if not paragraphs:
            return "", "Word 文档中未找到文本内容。"
        return "\n".join(paragraphs), None
    except Exception as e:
        return "", f"解析 Word 文档失败：{e}"


def transcribe_audio(file_path: str) -> tuple[str, str | None]:
    """使用 Whisper 将音频转为文字"""
    if not WHISPER_OK:
        return "", "语音转文字需要 openai-whisper 依赖，安装失败或已跳过。"
    try:
        model = _get_whisper_model()
        if model is None:
            return "", "Whisper 模型加载失败。"
        result = model.transcribe(file_path, fp16=False, language="zh")
        text = result["text"].strip()
        if not text:
            return "", "音频中未检测到语音内容。"
        return text, None
    except Exception as e:
        msg = str(e)
        if "ffmpeg" in msg.lower():
            return "", "需要安装 ffmpeg 才能转写音频。请从 https://ffmpeg.org/download.html 下载并添加到 PATH。"
        return "", f"语音转写失败：{e}"


def parse_file(file_path: str, file_name: str) -> tuple[str, str, str | None]:
    """根据文件扩展名自动选择解析器，返回 (文本内容, 源名称, 错误)"""
    ext = Path(file_name).suffix.lower()
    if ext == ".txt":
        text, err = parse_txt(file_path)
    elif ext == ".docx":
        text, err = parse_docx(file_path)
    elif ext in (".mp3", ".wav", ".m4a", ".flac", ".ogg"):
        text, err = transcribe_audio(file_path)
    else:
        return "", file_name, f"不支持的文件格式「{ext}」。支持的格式：.txt / .docx / .mp3 / .wav / .m4a"
    return text, file_name, err
