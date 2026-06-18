# Plan pour pousser le projet

## Contexte constaté

- Branche courante : `main`
- Remote push : `origin` -> `https://github.com/elhaj2004/Pres-Factory.git`
- Fichiers modifiés non commités :
  - `.env.example`
  - `.gitignore`
  - `README.md`
  - `requirements.txt`
  - `scripts/index_brandstore.py`
  - `src/llm/client.py`
  - `src/rag/store.py`
- `.env` est bien ignoré par Git et ne sera pas poussé.

## Objectif

Pousser sur `origin/main` les changements d’intégration SharePoint/RAG et de configuration LLM proxy, sans exposer de secret local.

## Plan d’exécution

1. Vérifier une dernière fois les changements destinés au commit.
   - Contrôler `git status`, `git diff`, et confirmer qu’aucun autre fichier inattendu n’est inclus.
   - Vérifier explicitement que `.env` reste ignoré et non tracké.

2. Valider le périmètre à pousser.
   - Inclure uniquement les 7 fichiers déjà modifiés dans le dépôt versionné.
   - Ne jamais ajouter `.env`, car il contient la clé API locale.

3. Exécuter une validation légère avant commit.
   - Lancer au minimum une compilation Python sur `src/rag/store.py`, `src/llm/client.py`, `scripts/index_brandstore.py`.
   - Si les dépendances sont disponibles, faire un dry-run simple du script d’indexation ou au minimum vérifier l’import des modules.

4. Créer un commit propre.
   - Stage uniquement :
     - `.env.example`
     - `.gitignore`
     - `README.md`
     - `requirements.txt`
     - `scripts/index_brandstore.py`
     - `src/llm/client.py`
     - `src/rag/store.py`
   - Utiliser un message de commit concis et cohérent avec l’historique, par exemple :
     - `Ajout du RAG SharePoint dynamique et config llmproxy`

5. Pousser vers le dépôt distant.
   - Exécuter `git push origin main`.
   - Vérifier le résultat et confirmer le hash du commit poussé.

## Points d’attention

- Le fichier `.env` local ne sera pas poussé ; la clé API restera uniquement sur la machine locale.
- Les credentials Graph SharePoint (`SHAREPOINT_TENANT_ID`, `SHAREPOINT_CLIENT_ID`, `SHAREPOINT_CLIENT_SECRET`) ne sont pas versionnés.
- Si le push échoue à cause d’un rejet distant, il faudra d’abord intégrer l’état distant (`git pull --rebase` ou stratégie équivalente), puis revalider avant de repousser.

## Résultat attendu

- Les changements applicatifs sont commités sur `main`.
- Le commit est poussé sur `origin/main`.
- Aucun secret local n’est publié.
