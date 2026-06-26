"""SQLite 数据库层 — 会议纪要的持久化存储"""
import sqlite3
import json
from datetime import datetime
from config import DB_PATH, DB_LOCK


def init_db() -> None:
    """创建数据库和表（首次运行自动执行）"""
    with DB_LOCK:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS meetings (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at  TEXT    NOT NULL,
                source_type TEXT    NOT NULL,
                source_name TEXT    NOT NULL,
                original_text TEXT  NOT NULL,
                debate_points   TEXT NOT NULL,
                final_conclusion TEXT NOT NULL,
                todo_items      TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()


def save_meeting(
    source_type: str,
    source_name: str,
    original_text: str,
    debate_points: str,
    final_conclusion: str,
    todo_items: list,
) -> int:
    """保存纪要，返回记录 ID"""
    with DB_LOCK:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.execute(
            """INSERT INTO meetings
               (created_at, source_type, source_name, original_text,
                debate_points, final_conclusion, todo_items)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                source_type,
                source_name,
                original_text,
                debate_points,
                final_conclusion,
                json.dumps(todo_items, ensure_ascii=False),
            ),
        )
        row_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return row_id


def get_history(search: str = "") -> list:
    """查询历史记录，返回 [(id, created_at, source_name, debate_points), ...]"""
    with DB_LOCK:
        conn = sqlite3.connect(DB_PATH)
        if search.strip():
            cursor = conn.execute(
                """SELECT id, created_at, source_name, debate_points
                   FROM meetings
                   WHERE original_text   LIKE ?
                      OR debate_points   LIKE ?
                      OR final_conclusion LIKE ?
                   ORDER BY id DESC LIMIT 50""",
                (f"%{search}%", f"%{search}%", f"%{search}%"),
            )
        else:
            cursor = conn.execute(
                """SELECT id, created_at, source_name, debate_points
                   FROM meetings ORDER BY id DESC LIMIT 50"""
            )
        rows = cursor.fetchall()
        conn.close()
        return rows


def get_meeting_by_id(meeting_id: int) -> dict | None:
    """根据 ID 获取完整纪要"""
    with DB_LOCK:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.execute("SELECT * FROM meetings WHERE id = ?", (meeting_id,))
        row = cursor.fetchone()
        conn.close()
    if row is None:
        return None
    return {
        "id": row[0],
        "created_at": row[1],
        "source_type": row[2],
        "source_name": row[3],
        "original_text": row[4],
        "debate_points": row[5],
        "final_conclusion": row[6],
        "todo_items": json.loads(row[7]),
    }
