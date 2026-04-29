from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import settings


def get_llm(json_mode: bool = None):
    provider = settings.LLM_PROVIDER
    use_json = settings.JSON_MODE if json_mode is None else json_mode

    kwargs = {
        "temperature": settings.TEMPERATURE,
    }

    # JSON mode chỉ áp dụng cho OpenAI/OpenRouter
    if use_json and provider in ["openai"]:
        kwargs["response_format"] = {"type": "json_object"}

    # ========= OPENAI =========
    if provider == "openai":
        return ChatOpenAI(
            model=settings.OPENAI_MODEL,
            api_key=settings.OPENAI_API_KEY,
            **kwargs
        )

    # ========= OPENROUTER (DeepSeek / Qwen / GPT / Gemini) =========
    if provider == "openrouter":
        return ChatOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=settings.OPENROUTER_API_KEY,
            model=settings.OPENROUTER_MODEL,
            default_headers={
                "HTTP-Referer": "http://localhost",
                "X-Title": "langgraph-test"
            },
            **kwargs
        )

    # ========= GOOGLE (direct Gemini API) =========
    if provider == "google":
        return ChatGoogleGenerativeAI(
            model=settings.GOOGLE_MODEL,
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=settings.TEMPERATURE
        )

    raise ValueError(f"Unsupported provider: {provider}")