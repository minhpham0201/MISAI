import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")

    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5-nano")

    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "")

    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
    GOOGLE_MODEL = os.getenv("GOOGLE_MODEL", "gemini-1.5-pro")

    TEMPERATURE = float(os.getenv("TEMPERATURE", 0))

    JSON_MODE = True


settings = Settings()