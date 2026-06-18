"""
Script d'indexation du BrandStore dans ChromaDB.

Usage :
    python scripts/index_brandstore.py
    python scripts/index_brandstore.py --force-refresh

Avec RAG_SOURCE=local, les documents sont lus depuis data/brandstore/.
Avec RAG_SOURCE=sharepoint, le script synchronise d'abord le cache SharePoint local.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.rag.store import SharePointSyncError, index_brandstore


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Indexe la base documentaire RAG.")
    parser.add_argument(
        "--force-refresh",
        action="store_true",
        help="Force la resynchronisation SharePoint avant reindexation.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    try:
        count = index_brandstore(verbose=True, force_refresh=args.force_refresh)
    except SharePointSyncError as exc:
        print(f"Echec de synchronisation SharePoint: {exc}")
        raise SystemExit(1) from exc

    if count == 0:
        print("Aucun document indexe. Verifiez la source RAG configuree.")
    else:
        print(f"{count} chunks indexes avec succes.")
