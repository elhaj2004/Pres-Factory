# Plan d'import local BrandStore depuis OneDrive

## Objectif

Importer dans le BrandStore local de `Pres-Factory` les fichiers de reference situes dans :

`C:\Users\BJPS1817\Downloads\OneDrive_2026-06-17\Résilience numérique`

en ne prenant que les fichiers `.pptx` et `.docx`, puis reindexer la base RAG locale pour que l'agent puisse s'en servir comme contexte de reference.

## Constat actuel

- Le dossier source contient de nombreux fichiers `.pptx` et `.docx` exploitables.
- Le dossier cible `data/brandstore/` est vide hormis `.gitkeep`.
- Le projet sait indexer localement les fichiers `.docx`, `.pptx`, `.txt` et `.md`.
- Le mode SharePoint n'est pas encore utilisable sans credentials Graph, donc le mode `RAG_SOURCE=local` est la bonne solution transitoire.

## Hypothese de travail

- Importer tous les `.pptx` et `.docx` trouves sous le dossier source.
- Preserver l'arborescence relative sous `data/brandstore/` pour eviter les collisions de noms et garder le contexte metier des dossiers.
- Ne pas toucher aux autres extensions.

## Plan d'execution

1. Verifier que `RAG_SOURCE` est bien positionne a `local` dans la configuration active.
2. Enumerer les fichiers `.pptx` et `.docx` du dossier source.
3. Copier ces fichiers vers `data/brandstore/` en conservant leur arborescence relative.
4. Laisser les fichiers non supportes de cote.
5. Lancer `scripts/index_brandstore.py` avec l'environnement Python du projet.
6. Verifier que l'indexation detecte bien des documents et cree les artefacts Chroma locaux.
7. Confirmer que le RAG local est ensuite exploitable par le pipeline applicatif.

## Points d'attention

- Certains noms de fichiers ou dossiers contiennent des accents, espaces et caracteres speciaux ; il faut conserver des chemins compatibles Windows sans les modifier inutilement.
- Le volume de documents semble important ; la copie doit etre recursive et non destructive.
- Il faut eviter d'aplatir les fichiers dans un seul dossier, car plusieurs documents peuvent partager un meme nom dans des sous-dossiers differents.
- Si `data/brandstore/` contient plus tard des documents deja presents, il faudra copier de maniere prudente pour ne pas ecraser involontairement des references locales non liees a cet import.

## Validation attendue

- Les fichiers `.pptx` et `.docx` du chemin source sont presents sous `data/brandstore/`.
- L'indexation locale se termine sans erreur bloquante.
- Le script affiche un nombre de documents/chunks strictement positif.
- Le pipeline peut ensuite utiliser `similarity_search()` sur cette base locale.

## Commandes prevues lors de l'execution

```powershell
.\.venv\Scripts\python.exe scripts/index_brandstore.py
```

Si la configuration n'est pas encore en local :

```env
RAG_SOURCE=local
BRANDSTORE_DIR=data/brandstore
```

## Resultat attendu

Le projet disposera d'un BrandStore local alimente a partir du dossier OneDrive fourni, avec uniquement les documents `.pptx` et `.docx`, utilisables immediatement pour enrichir le mapping de styles via RAG en attendant l'integration SharePoint.
