import logfire
from portkey_ai import Portkey, createHeaders, PORTKEY_GATEWAY_URL
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from groq import Groq

from app.config import settings


# Production gateway config:
#   - Fallback: primary @rag/llama-3.3-70b-versatile → @brag/llama-3.1-8b-instant on failure
#   - Cache: semantic mode (requires Portkey Enterprise — silently falls back to simple on free/starter)
#   - Retry: 2 attempts on rate limit / server error before triggering the fallback target
GATEWAY_CONFIG = {
    "strategy": {"mode": "fallback"},
    "cache": {"mode": "simple"},
    "retry": {
        "attempts": 2,
        "on_status_codes": [429, 503]
    },
    "targets": [
        {"override_params": {"model": f"@{settings.GROQ_SLUG}/{settings.GROQ_MODEL}"}},
        {"override_params": {"model": f"@{settings.GROQ_SLUG_2}/openai/gpt-oss-20b"}},
    ]
}


if settings.PORTKEY_API_KEY:
    portkey_client = Portkey(
        api_key=settings.PORTKEY_API_KEY,
        config=GATEWAY_CONFIG
    )
else:
    # Graceful fallback to direct Groq client when Portkey is not configured
    class DirectGroqWrapper:
        def __init__(self, groq_client, default_model: str):
            self._client = groq_client
            self._default_model = default_model

        class _Completions:
            def __init__(self, client, default_model):
                self._client = client
                self._default_model = default_model

            def create(self, **kwargs):
                if "model" not in kwargs or kwargs["model"].startswith("@"):
                    kwargs["model"] = self._default_model
                try:
                    return self._client.chat.completions.create(**kwargs)
                except Exception as e:
                    # If requested model is not available or has 404 access restrictions, fall back to qwen/qwen3.8-27b or openai/gpt-oss-20b
                    if "model_not_found" in str(e).lower() and kwargs.get("model") != "qwen/qwen3.8-27b":
                        logfire.warning(f"Model {kwargs.get('model')} not accessible on Groq key, falling back to qwen/qwen3.8-27b.")
                        kwargs["model"] = "qwen/qwen3.8-27b"
                        return self._client.chat.completions.create(**kwargs)
                    raise e

        @property
        def chat(self):
            class _Chat:
                def __init__(s, client, default_model):
                    s.completions = DirectGroqWrapper._Completions(client, default_model)
            return _Chat(self._client, self._default_model)

    portkey_client = DirectGroqWrapper(Groq(api_key=settings.GROQ_API_KEY), settings.GROQ_MODEL)


def get_langchain_llm(feature: str = "rag"):
    """
    Returns a Portkey-backed ChatOpenAI — a drop-in for ChatGroq in LangChain nodes.
    Falls back directly to ChatGroq if PORTKEY_API_KEY is not set.
    """
    if settings.PORTKEY_API_KEY:
        return ChatOpenAI(
            api_key=settings.PORTKEY_API_KEY,
            base_url=PORTKEY_GATEWAY_URL,
            model=f"@{settings.GROQ_SLUG}/{settings.GROQ_MODEL}",
            temperature=0,
            default_headers=createHeaders(
                api_key=settings.PORTKEY_API_KEY,
                config=GATEWAY_CONFIG,
                metadata={
                    "feature": feature,
                    "_user": "rag-system",
                    "environment": "production"
                }
            )
        )
    return ChatGroq(
        api_key=settings.GROQ_API_KEY,
        model=settings.GROQ_MODEL,
        temperature=0
    )


def extract_cache_status(response) -> str:
    """
    Pull x-portkey-cache-status from the Portkey native client response headers.
    Tries multiple attribute paths defensively — returns 'MISS' if not found.
    """
    for attr in ("_raw_response", "_response", "_http_response"):
        raw = getattr(response, attr, None)
        if raw is not None:
            status = getattr(raw, "headers", {}).get("x-portkey-cache-status", "")
            if status:
                return status.upper()
    return "MISS"
