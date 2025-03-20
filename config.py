import os
from dotenv import load_dotenv

load_dotenv()

# OpenAI 配置
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_NAME = "gpt-4-0125-preview"

# 文件目錄配置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILES_DIR = os.path.join(BASE_DIR, "files")
HISTORY_DIR = os.path.join(BASE_DIR, "history")
HISTORY_FILE = os.path.join(HISTORY_DIR, "chat_history.jsonl")

# 數據庫配置
DB_PATH = os.path.join(FILES_DIR, "legal.db")

# 確保必要的目錄存在
os.makedirs(FILES_DIR, exist_ok=True)
os.makedirs(HISTORY_DIR, exist_ok=True)
