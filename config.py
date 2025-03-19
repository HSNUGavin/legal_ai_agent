import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_NAME = "gpt-4o-mini"
HISTORY_FILE = "conversation_history.txt"
FILES_DIR = "files"
