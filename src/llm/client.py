import os
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()


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
        model=os.getenv("DINOOTOO_MODEL", "gpt-4o"),
        api_key=os.getenv("DINOOTOO_API_KEY", ""),
        base_url=os.getenv("DINOOTOO_BASE_URL") or None,
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
        model=os.getenv("DINOOTOO_EMBEDDING_MODEL", "text-embedding-3-small"),
        api_key=os.getenv("DINOOTOO_API_KEY", ""),
        base_url=os.getenv("DINOOTOO_BASE_URL") or None,
    )
