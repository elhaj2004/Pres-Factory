# Pres Factory — Agent de mise en conformité charte OCD

Agent LangGraph qui applique automatiquement la charte graphique **Orange Cyberdefense** sur des documents `.docx` et `.pptx`. Il anonymise les données sensibles, remet en forme le document selon les standards OCD, évalue la conformité, puis demande une validation humaine avant de livrer le fichier final.

---

## Fonctionnement

### Pipeline LangGraph

```
[Fichier DOCX/PPTX]
        │
        ▼
  detect_format          Identifie l'extension (.docx / .pptx)
        │
        ▼
  parse_document         Extrait tous les éléments textuels (paragraphes,
        │                titres, bullets, tableaux, slides…)
        ▼
    anonymize            Passe regex (emails, tél, montants) + LLM pour
        │                remplacer noms clients, personnes, dates, refs projet
        ▼
   map_styles            LLM + RAG (BrandStore ChromaDB) → génère un style_map
        │                JSON qui assigne le style OCD à chaque élément
        ▼
  apply_charter          Réécrit le fichier avec python-docx / python-pptx
        │                en appliquant polices, couleurs, espacements OCD
        ▼
  check_quality          LLM évalue la conformité (score 0–100) sur 4 axes :
        │                typographie, couleurs, espacements, cohérence
        ▼
  human_review  ◄────── INTERRUPT — l'UI attend la validation humaine
        │
   ┌────┴────┐
   │         │
Approuvé   Rejeté + feedback
   │         │
  END    map_styles (itération suivante, max 3)
```

### Providers LLM supportés

| Provider | Variable `LLM_PROVIDER` | Usage |
|---|---|---|
| **Dinootoo** (défaut) | `dinootoo` | API IA interne OCD, compatible OpenAI |
| **Anthropic** | `anthropic` | Claude Sonnet via API Anthropic |

### RAG — BrandStore

Les documents de référence `.docx` placés dans `data/brandstore/` sont indexés dans **ChromaDB** (local). Lors du mapping de styles, l'agent récupère les 3 exemples les plus similaires pour guider le LLM.

---

## Installation

### Prérequis

- Python 3.10+
- Un accès à l'API Dinootoo **ou** une clé Anthropic

### 1. Cloner et entrer dans le projet

```bash
git clone <url-du-repo>
cd Pres-Factory
```

### 2. Créer et activer l'environnement virtuel

```bash
python -m venv .venv
source .venv/bin/activate      # Linux / macOS
# .venv\Scripts\activate       # Windows
```

> Si le `.venv` existe déjà dans le repo, passer directement à l'activation.

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

Pour utiliser Anthropic en provider :

```bash
pip install langchain-anthropic
```

Pour les embeddings locaux (si Dinootoo ne supporte pas les embeddings) :

```bash
pip install sentence-transformers
```

### 4. Configurer les variables d'environnement

```bash
cp .env.example .env
```

Éditer `.env` :

```env
# --- Provider principal (Dinootoo, API interne OCD) ---
DINOOTOO_API_KEY=<votre_clé>
DINOOTOO_BASE_URL=https://<endpoint-dinootoo>/v1
DINOOTOO_MODEL=gpt-4o
DINOOTOO_EMBEDDING_MODEL=text-embedding-3-small

# --- OU Anthropic ---
# LLM_PROVIDER=anthropic
# ANTHROPIC_API_KEY=<votre_clé>
# ANTHROPIC_MODEL=claude-sonnet-4-6

# --- Embeddings locaux (si pas d'API embeddings) ---
# USE_LOCAL_EMBEDDINGS=true
# LOCAL_EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2

# --- Qualité ---
QUALITY_THRESHOLD=70    # score minimum avant human review (sinon retry auto)
MAX_ITERATIONS=3        # nb max d'itérations automatiques

# --- LangSmith (optionnel, pour tracer les runs) ---
# LANGCHAIN_TRACING_V2=true
# LANGCHAIN_API_KEY=<votre_clé_langsmith>
# LANGCHAIN_PROJECT=pres-factory
```

---

## Lancer le projet

### Commande unique (à chaque fois)

```bash
source .venv/bin/activate
python ui/app.py
```

L'interface est disponible sur **http://localhost:7860**

---

## (Optionnel) Indexer le BrandStore

Le BrandStore est la base de documents OCD de référence utilisée par le RAG. Si elle est vide, l'agent fonctionne quand même mais sans exemples de contexte.

1. Placer des fichiers `.docx` de référence (documents OCD validés) dans `data/brandstore/`
2. Lancer l'indexation :

```bash
source .venv/bin/activate
python scripts/index_brandstore.py
```

L'index ChromaDB est persisté dans `data/chroma_db/` — l'indexation n'est à refaire que si de nouveaux documents sont ajoutés.

---

## Utilisation de l'interface

1. **Importer** un fichier `.docx` ou `.pptx` via le bouton de dépôt
2. Cliquer sur **"Appliquer la charte OCD"** — le pipeline tourne automatiquement
3. Consulter le **rapport de conformité** (score + détail + problèmes détectés)
4. **Valider ou rejeter** le résultat :
   - **Approuver** → le document est finalisé et disponible au téléchargement
   - **Rejeter** → saisir un feedback (obligatoire), l'agent relance une nouvelle itération en tenant compte du retour
5. **Télécharger** le document conforme

---

## Structure du projet

```
Pres-Factory/
├── ui/
│   └── app.py                  # Interface Gradio (point d'entrée)
├── src/
│   ├── graph.py                # Définition du graphe LangGraph
│   ├── state.py                # TypedDict de l'état partagé entre les nœuds
│   ├── charter/
│   │   └── ocd_charter.json    # Spécifications de la charte OCD (polices, couleurs…)
│   ├── llm/
│   │   └── client.py           # Factory LLM (Dinootoo / Anthropic)
│   ├── nodes/
│   │   ├── detector.py         # Détection du format fichier
│   │   ├── parser.py           # Extraction des éléments textuels
│   │   ├── anonymizer.py       # Anonymisation RGPD (regex + LLM)
│   │   ├── style_mapper.py     # Mapping styles OCD via LLM + RAG
│   │   ├── charter_applier.py  # Application physique sur le fichier
│   │   ├── quality_checker.py  # Évaluation LLM de la conformité
│   │   └── human_review.py     # Nœud garde-fou (pass-through, interrupt géré par le graphe)
│   └── rag/
│       └── store.py            # Gestion ChromaDB (indexation + recherche)
├── scripts/
│   └── index_brandstore.py     # Script d'indexation du BrandStore
├── data/
│   ├── brandstore/             # Documents OCD de référence à placer ici
│   ├── uploads/                # Fichiers uploadés (généré automatiquement)
│   ├── chroma_db/              # Index vectoriel ChromaDB (généré automatiquement)
│   └── output/                 # Documents traités en sortie (généré automatiquement)
├── requirements.txt
├── .env.example
└── .gitignore
```

---

## Mise à jour de la charte OCD

La charte est définie dans `src/charter/ocd_charter.json`. Pour l'ajuster (nouvelles couleurs, polices, tailles), modifier ce fichier directement — aucun redémarrage n'est nécessaire, le fichier est relu à chaque traitement.

---

## Évolution vers RAG SharePoint

Remplacer `src/rag/store.py` par un connecteur SharePoint/Microsoft Graph. L'interface `get_rag_store()` et `similarity_search()` reste identique — aucune autre modification requise.
