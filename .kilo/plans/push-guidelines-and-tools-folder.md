# Plan pour repousser `GuidelinesFR.pdf` et `Tools and templates PPT - FR/`

## Constat

- Le dépôt a déjà été nettoyé et poussé avec succès sans les gros assets.
- `GuidelinesFR.pdf` est présent localement et pèse environ `8.1 MB`.
- Le dossier `Tools and templates PPT - FR/` est présent localement, contient `114` fichiers pour environ `238.9 MB`.
- Aucun fichier de ce dossier ne dépasse la limite GitHub de `100 MB`.
- Le blocage précédent venait des fichiers > `100 MB` dans `data/brandstore/`, pas de `GuidelinesFR.pdf` ni de `Tools and templates PPT - FR/`.
- Ces deux chemins sont actuellement ignorés dans `.gitignore`, donc ils ne peuvent pas etre inclus dans un commit tant que cette regle reste en place.

## Risque / point de decision

Le dossier `Tools and templates PPT - FR/` contient vraisemblablement quelques fichiers parasites ou temporaires :

- `.DS_Store`
- fichiers `._*`
- fichiers `.tmp`

Deux strategies sont possibles :

1. **Inclure strictement tout le dossier** tel quel, sans filtrage.
2. **Inclure le dossier utile** en excluant seulement les fichiers parasites evidents (`.DS_Store`, `._*`, `.tmp`, fichiers lock temporaires) pour garder un repo plus propre.

## Strategie recommandee

Preferer la strategie 2 :

- inclure `GuidelinesFR.pdf`
- inclure `Tools and templates PPT - FR/`
- exclure uniquement les fichiers parasites/temporaires evidents

Cela respecte l'intention utilisateur tout en evitant d'ajouter des dechets techniques inutiles au depot.

## Etapes d'implementation

1. Modifier `.gitignore` pour cesser d'ignorer :
   - `GuidelinesFR.pdf`
   - `Tools and templates PPT - FR/`
2. Ajouter, si retenu, des regles d'exclusion plus fines pour les fichiers parasites du dossier :
   - `.DS_Store`
   - `._*`
   - `*.tmp`
   - fichiers lock temporaires Office si presents
3. Verifier l'etat Git apres mise a jour des regles d'ignore.
4. Stager uniquement :
   - `.gitignore`
   - `GuidelinesFR.pdf`
   - `Tools and templates PPT - FR/`
5. Verifier la liste exacte des fichiers stages.
6. Verifier qu'aucun blob stage ne depasse `100 MB`.
7. Creer un commit dedie et explicite pour ces assets.
8. Executer `git push origin main`.
9. Confirmer que le remote contient bien ces fichiers et que le push est accepte par GitHub.

## Validation attendue

- `git status` ne montre en stage que les fichiers voulus.
- aucun fichier stage > `100 MB`.
- `git push origin main` reussit.
- un `git pull` sur un autre poste permet de recuperer :
  - `GuidelinesFR.pdf`
  - `Tools and templates PPT - FR/`

## Remarque

Si l'utilisateur exige explicitement d'inclure **strictement tout le dossier**, y compris fichiers parasites et temporaires, il faudra suivre cette instruction telle quelle tant qu'aucun fichier ne depasse la limite GitHub.
