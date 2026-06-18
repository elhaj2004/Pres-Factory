# Plan cleanup git et push

## Objectif

Retirer du push tous les ajouts lourds et non souhaites actuellement presents sur la branche locale, eliminer les gros binaires qui bloquent GitHub, puis retenter un `git push` propre sur `origin/main`.

## Constat actuel

- La branche `main` est en avance sur `origin/main` de `2` commits.
- Le push echoue a cause de fichiers > 100 MB deja presents dans l'historique local.
- Un commit recent `42736ec` supprime bien les 4 gros `.pptx`, mais cela ne suffit pas car ils existent encore dans le commit precedent non pousse.
- Le commit local precedent ajoute un tres grand nombre de fichiers qui ne devraient vraisemblablement pas etre pushes :
  - `data/brandstore/**`
  - `Tools and templates PPT - FR/**`
  - `data/data/output/**`
  - `__pycache__/**`
  - plusieurs fichiers binaires et assets locaux

## Strategie retenue

Comme ces commits ne sont pas encore pushes, la solution la plus propre est de reconstituer un historique local propre sans les gros ajouts accidentels.

## Etapes d'implementation

1. Inspecter `git status`, `git log --oneline -10` et confirmer les 2 commits locaux a nettoyer.
2. Revenir a `origin/main` en conservant les fichiers dans le working tree :
   - utiliser un reset non destructif adapte (`git reset --mixed origin/main` ou equivalent) pour sortir les ajouts de l'historique local.
3. Nettoyer l'index Git de tout ce qui a ete ajoute mais ne doit pas etre versionne :
   - `data/brandstore/**`
   - `Tools and templates PPT - FR/**`
   - `data/data/output/**`
   - `__pycache__/**`
   - autres binaires locaux non souhaites si encore indexes
4. S'assurer que les 4 gros fichiers bloques ne sont plus suivis par Git et n'apparaissent plus dans l'historique a pousser.
5. Verifier le diff restant contre `origin/main` pour confirmer qu'il ne reste que les vrais fichiers de code/docs utiles.
6. Si necessaire, ajouter ou ajuster `.gitignore` pour eviter de reindexer ces assets lors des prochaines commandes `git add`.
7. Creer un nouveau commit propre avec uniquement les fichiers souhaites.
8. Retenter `git push origin main`.
9. Si le push echoue encore, identifier tout autre blob > 100 MB restant dans l'historique local et repeter le nettoyage avant nouveau push.

## Points d'attention

- Ne pas supprimer physiquement les fichiers locaux si l'utilisateur veut les conserver pour usage sur la machine.
- Retirer les fichiers de Git ne signifie pas les effacer du disque ; il faut privilegier le retrait de l'index et la reconstruction du commit.
- Comme il y a deja un commit de suppression des 4 gros fichiers, il faut nettoyer l'historique local en amont, pas seulement ajouter de nouvelles suppressions.
- Verifier que les modifications de code importantes ne sont pas perdues pendant le reset ; elles doivent rester dans le working tree puis etre recommittees proprement.

## Validation finale attendue

- `git status` propre ou limite aux changements voulus.
- `git diff origin/main..HEAD` ne contient plus les gros assets ni les dossiers locaux a exclure.
- aucun blob > 100 MB dans l'historique a pousser.
- `git push origin main` reussit.
