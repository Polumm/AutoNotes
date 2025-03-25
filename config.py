import os


class Config:
    # Allow override via environment variables
    OLLAMA_API = os.getenv("OLLAMA_API", "http://localhost:11434/api/chat")
    LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-r1:14b")
    WHISPER_MODEL_DIR = os.getenv("WHISPER_MODEL_DIR", "./models/whisper")
