import os
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()


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
    return (
        os.getenv("OPENAI_COMPAT_MODEL")
        or os.getenv("DINOOTOO_MODEL")
        or "gpt-4o"
    )


def _embedding_model_name() -> str:
    return (
        os.getenv("OPENAI_COMPAT_EMBEDDING_MODEL")
        or os.getenv("DINOOTOO_EMBEDDING_MODEL")
        or "text-embedding-3-small"
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
