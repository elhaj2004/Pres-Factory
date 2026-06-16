import os
from pathlib import Path
from typing import Optional
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import DirectoryLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from src.llm.client import get_embeddings

CHROMA_DIR = Path(__file__).parent.parent.parent / "data" / "chroma_db"
BRANDSTORE_DIR = Path(__file__).parent.parent.parent / "data" / "brandstore"

_store: Optional[Chroma] = None


def get_rag_store() -> Chroma:
    global _store
    if _store is not None:
        return _store

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    embeddings = get_embeddings()

    _store = Chroma(
        persist_directory=str(CHROMA_DIR),
        embedding_function=embeddings,
        collection_name="brandstore",
    )
    return _store


def index_brandstore(verbose: bool = True) -> int:
    """Indexe tous les .docx du dossier data/brandstore/ dans ChromaDB."""
    if not BRANDSTORE_DIR.exists() or not any(BRANDSTORE_DIR.glob("**/*.docx")):
        if verbose:
            print(f"[RAG] BrandStore vide — ajoutez des .docx dans {BRANDSTORE_DIR}")
        return 0

    loader = DirectoryLoader(
        str(BRANDSTORE_DIR),
        glob="**/*.docx",
        loader_cls=Docx2txtLoader,
        show_progress=verbose,
    )
    docs = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", ". ", " "],
    )
    chunks = splitter.split_documents(docs)

    embeddings = get_embeddings()
    store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(CHROMA_DIR),
        collection_name="brandstore",
    )

    if verbose:
        print(f"[RAG] Indexé {len(chunks)} chunks depuis {len(docs)} documents.")

    global _store
    _store = store
    return len(chunks)


def similarity_search(query: str, k: int = 3) -> list:
    store = get_rag_store()
    try:
        return store.similarity_search(query, k=k)
    except Exception:
        return []
