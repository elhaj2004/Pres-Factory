import os
from functools import lru_cache
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

load_dotenv()


@lru_cache(maxsize=1)
def get_llm() -> ChatOpenAI:
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

    return OpenAIEmbeddings(
        model=os.getenv("DINOOTOO_EMBEDDING_MODEL", "text-embedding-3-small"),
        api_key=os.getenv("DINOOTOO_API_KEY", ""),
        base_url=os.getenv("DINOOTOO_BASE_URL") or None,
    )
