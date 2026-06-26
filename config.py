"""共享配置常量"""
from pathlib import Path
from threading import Lock
from dotenv import load_dotenv
import os

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = str(BASE_DIR / "meetings.db")
EXPORT_DIR = BASE_DIR / "exports"
EXPORT_DIR.mkdir(exist_ok=True)
DB_LOCK = Lock()

# DeepSeek API Key（从 .env 读取）
API_KEY_FROM_ENV = os.getenv("DEEPSEEK_API_KEY")
