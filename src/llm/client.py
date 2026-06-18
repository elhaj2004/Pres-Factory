import os
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()

_OPENAI_COMPAT_HOST_HINTS = ("llmproxy.ai.orange",)


def _configure_optional_tracing() -> None:
    tracing_enabled = (
        os.getenv("LANGCHAIN_TRACING_V2")
        or os.getenv("LANGSMITH_TRACING")
        or ""
    ).strip().lower()
    api_key = (
        os.getenv("LANGCHAIN_API_KEY")
        or os.getenv("LANGSMITH_API_KEY")
        or ""
    ).strip()

    if tracing_enabled in {"1", "true", "yes", "on"} and not api_key:
        os.environ["LANGCHAIN_TRACING_V2"] = "false"
        os.environ["LANGSMITH_TRACING"] = "false"


def _should_prefix_openai_models(base_url: str | None) -> bool:
    if not base_url:
        return False
    return any(host_hint in base_url.lower() for host_hint in _OPENAI_COMPAT_HOST_HINTS)


def _normalize_openai_compatible_model_name(model_name: str, base_url: str | None) -> str:
    normalized = model_name.strip()
    if not normalized or "/" in normalized:
        return normalized
    if _should_prefix_openai_models(base_url):
        return f"openai/{normalized}"
    return normalized


_configure_optional_tracing()


def _openai_compatible_api_key() -> str:
    return (
        os.getenv("OPENAI_COMPAT_API_KEY")
        or os.getenv("DINOOTOO_API_KEY")
        or ""
    )


def _openai_compatible_base_url() -> str | None:
    return (
        os.getenv("OPENAI_COMPAT_BASE_URL")
        or os.getenv("DINOOTOO_BASE_URL")
        or None
    )


def _chat_model_name() -> str:
    configured_model = (
        os.getenv("OPENAI_COMPAT_MODEL")
        or os.getenv("DINOOTOO_MODEL")
        or "gpt-4o"
    )
    return _normalize_openai_compatible_model_name(
        configured_model,
        _openai_compatible_base_url(),
    )


def _embedding_model_name() -> str:
    configured_model = (
        os.getenv("OPENAI_COMPAT_EMBEDDING_MODEL")
        or os.getenv("DINOOTOO_EMBEDDING_MODEL")
        or "text-embedding-3-small"
    )
    return _normalize_openai_compatible_model_name(
        configured_model,
        _openai_compatible_base_url(),
    )


@lru_cache(maxsize=1)
def get_llm():
    provider = os.getenv("LLM_PROVIDER", "dinootoo").lower()

    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6"),
            api_key=os.getenv("ANTHROPIC_API_KEY", ""),
            temperature=0.1,
            max_tokens=4096,
        )

    # Dinootoo (défaut) — interface OpenAI-compatible
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(
        model=_chat_model_name(),
        api_key=_openai_compatible_api_key(),
        base_url=_openai_compatible_base_url(),
        temperature=0.1,
        max_tokens=4096,
    )


@lru_cache(maxsize=1)
def get_embeddings():
    if os.getenv("USE_LOCAL_EMBEDDINGS", "false").lower() == "true":
        from langchain_community.embeddings import HuggingFaceEmbeddings
        return HuggingFaceEmbeddings(
            model_name=os.getenv(
                "LOCAL_EMBEDDING_MODEL",
                "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            )
        )

    from langchain_openai import OpenAIEmbeddings
    return OpenAIEmbeddings(
        model=_embedding_model_name(),
        api_key=_openai_compatible_api_key(),
        base_url=_openai_compatible_base_url(),
    )
