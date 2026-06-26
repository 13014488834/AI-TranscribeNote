"""核心模块 — Pydantic 模型 + LLM 初始化 + 纪要生成"""
from typing import List

from pydantic import BaseModel, Field
from langchain_deepseek import ChatDeepSeek

from config import API_KEY_FROM_ENV
from db import save_meeting


# ==================== Pydantic 数据模型 ====================
class TodoItem(BaseModel):
    """待办事项"""
    task: str = Field(description="任务描述")
    person: str = Field(description="负责人")


class MeetingMinutes(BaseModel):
    """会议纪要结构化模型，LLM 强制按此 schema 返回 JSON"""
    争论焦点: str = Field(description="会议中意见不一致的核心问题")
    最终结论: str = Field(description="会议达成的最终决定")
    待办事项: List[TodoItem] = Field(description="待办事项列表，每项包含任务描述和负责人")


# ==================== LLM 懒加载 ====================
_llm_cache: dict = {}


def _get_structured_llm(override_key: str = ""):
    """懒加载 DeepSeek LLM（首次调用时初始化，支持 UI 临时 Key 或 .env Key）"""
    effective_key = (override_key or API_KEY_FROM_ENV or "").strip()

    if not effective_key:
        return None, (
            "⚠️ 未配置 DeepSeek API Key。\n"
            "两种方式任选：\n"
            "1) 在下方「API Key」输入框粘贴你的 Key\n"
            "2) 创建 .env 文件，写入 DEEPSEEK_API_KEY=你的Key\n"
            "获取地址：https://platform.deepseek.com"
        )

    if effective_key in _llm_cache:
        return _llm_cache[effective_key], None

    try:
        llm = ChatDeepSeek(model="deepseek-chat", temperature=0.1, api_key=effective_key)
        _llm_cache[effective_key] = llm.with_structured_output(MeetingMinutes)
        return _llm_cache[effective_key], None
    except Exception as e:
        return None, f"❌ LLM 初始化失败：{e}"


# ==================== 核心生成函数 ====================
def summarize_meeting(text: str, source_type: str = "text",
                      source_name: str = "手动输入",
                      api_key: str = "") -> dict:
    """处理会议文字记录，提取争论焦点、最终结论和待办事项"""
    if not text or not text.strip():
        return {
            "状态": "⚠️ 输入为空",
            "提示": "请粘贴会议内容或上传文件。",
            "争论焦点": "", "最终结论": "", "待办事项": [],
        }

    MAX_CHARS = 8000
    overflow_note = ""
    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS]
        overflow_note = "「注意：原文过长，已截取前8000字处理」"

    prompt = (
        "你是一位资深的会议纪要秘书。请仔细阅读以下会议文字记录，从中提取出：\n"
        "1. 争论焦点：会议中意见不一致、存在讨论或争议的核心问题是什么？\n"
        "2. 最终结论：会议针对上述争论最终达成了什么决定或共识？\n"
        "3. 待办事项：列出所有需要后续跟进的任务，每项需明确任务描述和负责人。\n\n"
        "重要规则：\n"
        "- 如果某项信息在会议记录中没有体现，请填写「（会议中未提及）」，不要凭空编造。\n"
        "- 待办事项如果会议中没提到任何人名，负责人请填写「待定」。\n"
        "- 尽可能精确提取，保持原文关键信息不丢失。\n\n"
        f"{overflow_note}\n=== 会议记录 ===\n{text}"
    )

    llm_instance, llm_error = _get_structured_llm(override_key=api_key)
    if llm_error:
        return {"状态": "⚠️ 未配置 API Key", "提示": llm_error,
                "争论焦点": "", "最终结论": "", "待办事项": []}
    if llm_instance is None:
        return {"状态": "❌ LLM 未初始化", "提示": "内部错误。",
                "争论焦点": "", "最终结论": "", "待办事项": []}

    try:
        result: MeetingMinutes = llm_instance.invoke(prompt)
        todo_list = [{"任务": item.task, "负责人": item.person} for item in result.待办事项]

        output = {
            "状态": "✅ 纪要生成成功",
            "争论焦点": result.争论焦点,
            "最终结论": result.最终结论,
            "待办事项": todo_list,
        }

        try:
            save_meeting(source_type=source_type, source_name=source_name,
                         original_text=text, debate_points=result.争论焦点,
                         final_conclusion=result.最终结论, todo_items=todo_list)
        except Exception:
            pass  # 数据库写入失败不影响主流程

        return output
    except Exception as e:
        return {"状态": "❌ API 调用失败", "错误信息": str(e),
                "争论焦点": "", "最终结论": "", "待办事项": []}
