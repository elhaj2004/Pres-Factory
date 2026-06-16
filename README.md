# Pres Factory — Orange Cyberdefense

Agent LangGraph de mise en conformité charte graphique OCD pour fichiers `.docx` et `.pptx`.

## Architecture

```
INPUT (.docx / .pptx)
        │
        ▼
[detect_format] → [parse_document] → [anonymize]
                                           │
                                           ▼
                                    [map_styles]  ←──────────────┐
                                           │                      │ feedback
                                           ▼                      │
                                    [apply_charter]               │
                                           │                      │
                                           ▼                      │
                                    [check_quality]               │
                                           │                      │
                               score ≥ 70 ou max iter            │
                                           ▼                      │
                            ┌── [GARDE-FOU HUMAIN] ──┐           │
                         approuver               rejeter ─────────┘
                            │
                            ▼
                     OUTPUT (.docx / .pptx conforme OCD)
```

### Nœuds LangGraph

| Nœud | Rôle |
|------|------|
| `detect_format` | Détecte .docx ou .pptx automatiquement |
| `parse_document` | Extrait les éléments structurés (JSON indexé) |
| `anonymize` | Anonymisation RGPD (regex + LLM Dinootoo) |
| `map_styles` | Mapping styles OCD via LLM + RAG BrandStore |
| `apply_charter` | Application programmatique de la charte (python-docx / python-pptx) |
| `check_quality` | Score de conformité OCD 0-100 |
| `human_review` | Garde-fou humain obligatoire (interrupt_before) |

## Installation

```bash
pip install -r requirements.txt
cp .env.example .env
# Remplir .env avec vos clés Dinootoo
```

## Lancer l'interface

```bash
python ui/app.py
# → http://localhost:7860
```

## Indexer le BrandStore (RAG)

Déposez vos documents OCD de référence dans `data/brandstore/`, puis :

```bash
python scripts/index_brandstore.py
```

## Charte graphique

Les règles OCD sont dans `src/charter/ocd_charter.json`.
**À mettre à jour avec les spécifications exactes du département Communication OCD.**

## Évolution vers RAG SharePoint

Remplacer `src/rag/store.py` par un connecteur SharePoint/Microsoft Graph.
L'interface `get_rag_store()` et `similarity_search()` reste identique — aucune autre modification requise.
