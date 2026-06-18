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

Le BrandStore supporte maintenant deux sources configurables via `RAG_SOURCE` :

| Mode | Variable `RAG_SOURCE` | Fonctionnement |
|---|---|---|
| **Local** | `local` | Lit les fichiers de référence depuis `data/brandstore/` |
| **SharePoint** | `sharepoint` | Synchronise incrémentalement un dossier SharePoint vers `data/sharepoint_cache/`, puis indexe localement dans Chroma |

Les types de fichiers indexables sont `.docx`, `.pptx`, `.txt` et `.md`. Les autres types sont ignores proprement.

Lors du mapping de styles, l'agent récupère les 3 exemples les plus similaires avec `similarity_search(query, k=3)` sans changer l'interface metier existante.

---

## Installation

### Prérequis

- Python 3.10+
- Un acces a l'API LLM Proxy Orange/OpenAI-compatible ou une cle Anthropic
- Pour le mode SharePoint: une application Microsoft Entra ID avec permissions Graph en client credentials

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

Editer `.env` :

```env
# --- Provider principal (LLM Proxy Orange, OpenAI-compatible) ---
LLM_PROVIDER=dinootoo
OPENAI_COMPAT_API_KEY=<votre_cle>
OPENAI_COMPAT_BASE_URL=https://llmproxy.ai.orange
OPENAI_COMPAT_MODEL=gpt-4o
OPENAI_COMPAT_EMBEDDING_MODEL=text-embedding-3-small

# --- Variables historiques conservees pour compatibilite ---
DINOOTOO_API_KEY=<votre_cle>
DINOOTOO_BASE_URL=https://llmproxy.ai.orange
DINOOTOO_MODEL=gpt-4o
DINOOTOO_EMBEDDING_MODEL=text-embedding-3-small

# --- OU Anthropic ---
# LLM_PROVIDER=anthropic
# ANTHROPIC_API_KEY=<votre_clé>
# ANTHROPIC_MODEL=claude-sonnet-4-6

# --- Embeddings locaux (si pas d'API embeddings) ---
# USE_LOCAL_EMBEDDINGS=true
# LOCAL_EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2

# --- RAG local ou SharePoint ---
RAG_SOURCE=local
BRANDSTORE_DIR=data/brandstore

# --- SharePoint / Microsoft Graph ---
# Le SharePoint OCD ci-dessous est preconfigure par defaut dans .env local.
SHAREPOINT_FOLDER_URL=https://orangecyberdefense.sharepoint.com/sites/directionExpertise/Documents%20partages/Forms/AllItems.aspx
SHAREPOINT_SITE_URL=https://orangecyberdefense.sharepoint.com/sites/directionExpertise
SHAREPOINT_DOCUMENT_LIBRARY=Documents partages
SHAREPOINT_FOLDER_PATH=
SHAREPOINT_TENANT_ID=<tenant_id>
SHAREPOINT_CLIENT_ID=<client_id>
SHAREPOINT_CLIENT_SECRET=<client_secret>

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

## Indexer le BrandStore

Le BrandStore est la base de documents OCD de reference utilisee par le RAG. Si elle est vide, l'agent fonctionne quand meme mais sans exemples de contexte.

### Mode local

1. Placer des fichiers `.docx`, `.pptx`, `.txt` ou `.md` de reference dans `data/brandstore/`
2. Lancer l'indexation :

```bash
source .venv/bin/activate
python scripts/index_brandstore.py
```

### Mode SharePoint

Configurer :

```env
RAG_SOURCE=sharepoint
SHAREPOINT_FOLDER_URL=https://orangecyberdefense.sharepoint.com/sites/directionExpertise/Documents%20partages/Forms/AllItems.aspx
SHAREPOINT_SITE_URL=https://orangecyberdefense.sharepoint.com/sites/directionExpertise
SHAREPOINT_DOCUMENT_LIBRARY=Documents partages
SHAREPOINT_FOLDER_PATH=
SHAREPOINT_TENANT_ID=<tenant_id>
SHAREPOINT_CLIENT_ID=<client_id>
SHAREPOINT_CLIENT_SECRET=<client_secret>
```

Puis lancer :

```bash
source .venv/bin/activate
python scripts/index_brandstore.py
```

Pour forcer une resynchronisation SharePoint complete avant reindexation :

```bash
python scripts/index_brandstore.py --force-refresh
```

Comportement du connecteur SharePoint :

1. Authentification Microsoft Graph en client credentials via `msal`
2. Resolution dynamique du site, de la bibliotheque et du dossier SharePoint
3. Synchronisation incrementale vers `data/sharepoint_cache/<source>/files/`
4. Suppression locale des fichiers retires du SharePoint
5. Conservation d'un `manifest.json` pour detecter les deltas
6. Indexation locale dans Chroma avec collection et dossier de persistance specifiques a la source
7. En cas d'echec Graph, reutilisation du cache local deja synchronise si present

L'index ChromaDB est persiste dans `data/chroma_db/<source>/`. Cela evite les collisions entre plusieurs sources RAG.

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
│   ├── brandstore/             # Documents OCD de reference (mode local)
│   ├── sharepoint_cache/       # Cache synchronise SharePoint + manifest
│   ├── uploads/                # Fichiers uploadés (généré automatiquement)
│   ├── chroma_db/              # Index vectoriel ChromaDB par source (genere automatiquement)
│   └── output/                 # Documents traités en sortie (généré automatiquement)
├── requirements.txt
├── .env.example
└── .gitignore
```

---

## Mise à jour de la charte OCD

La charte est définie dans `src/charter/ocd_charter.json`. Pour l'ajuster (nouvelles couleurs, polices, tailles), modifier ce fichier directement — aucun redémarrage n'est nécessaire, le fichier est relu à chaque traitement.

---

## Permissions Microsoft Graph attendues

Le mode SharePoint attend une application Entra ID avec des permissions applicatives adaptees, typiquement :

- `Sites.Read.All`
- `Files.Read.All`

Un consentement administrateur est generalement necessaire.

## Config locale predefinie

Le depot peut utiliser un `.env` local gitignore avec :

- la cle API utilisateur pour `https://llmproxy.ai.orange`
- le SharePoint OCD `https://orangecyberdefense.sharepoint.com/sites/directionExpertise/Documents%20partages/Forms/AllItems.aspx`

Les credentials Graph restent a renseigner pour activer la synchronisation SharePoint distante. Sans eux, le code echoue proprement et peut reutiliser un cache local deja synchronise.
