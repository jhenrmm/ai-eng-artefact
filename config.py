import os

from dotenv import load_dotenv

load_dotenv()

PDF_PATH = os.getenv("PDF_PATH", "data/políticas_da_loja.pdf")
DATA_DIR = os.getenv("DATA_DIR", "data")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))

OLLAMA_URL = os.getenv("OLLAMA_URL")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")
OLLAMA_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "120"))

CHAT_MAX_MESSAGE_CHARS = int(os.getenv("CHAT_MAX_MESSAGE_CHARS", "1000"))

API_HOST = os.getenv("API_HOST")
API_PORT = int(os.getenv("API_PORT"))

ST_MODEL_NAME = os.getenv("ST_MODEL_NAME")