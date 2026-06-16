"""
Script d'indexation du BrandStore dans ChromaDB.
Usage : python scripts/index_brandstore.py

Placez vos documents OCD de référence (.docx) dans data/brandstore/
avant d'exécuter ce script.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.rag.store import index_brandstore

if __name__ == "__main__":
    count = index_brandstore(verbose=True)
    if count == 0:
        print("Aucun document indexé. Vérifiez data/brandstore/")
    else:
        print(f"✅ {count} chunks indexés avec succès.")
