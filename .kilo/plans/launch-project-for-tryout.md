# Plan de lancement local pour essai utilisateur

## Objectif

Lancer `Pres-Factory` localement pour permettre un essai manuel dans l'interface web.

## Contexte connu

- Le projet se lance via `ui/app.py`.
- L'environnement virtuel local attendu est `.venv`.
- Le point d'acces local attendu est `http://127.0.0.1:7860`.
- Le projet a deja fonctionne localement dans cette machine avec PowerShell.

## Commandes de lancement recommandees

### Option la plus simple

Depuis `C:\Users\BJPS1817\Pres-Factory` :

```powershell
.\.venv\Scripts\python.exe ui\app.py
```

### Option avec activation du venv

```powershell
.\.venv\Scripts\Activate.ps1
python ui\app.py
```

## Si PowerShell bloque l'activation

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python ui\app.py
```

## Verification attendue

1. Le terminal doit afficher le demarrage de Gradio.
2. L'URL locale doit etre accessible :

```text
http://127.0.0.1:7860
```

3. L'utilisateur peut ensuite charger un `.pptx` ou `.docx` dans l'UI.

## Points d'attention

- Si `.venv` n'existe plus, il faudra le recreer puis reinstaller les dependances :

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

- Si le projet doit utiliser le mode local plutot que SharePoint, verifier dans `.env` que la config active correspond bien au mode de test souhaite.

## Resultat attendu

L'application tourne localement, reste ouverte tant que le terminal tourne, et l'utilisateur peut tester le pipeline depuis le navigateur.
