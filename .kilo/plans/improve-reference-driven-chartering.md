# Plan d'amelioration du chartering par references

## Contexte

L'approche actuelle "references uniquement" produit des resultats insuffisants :

- les styles appliques restent partiels sur de nombreux placeholders PPTX ;
- les profils derives des references sont trop grossiers (moyennes title/body/bullet), ce qui ecrase les nuances de mise en page ;
- le mapping n'exploite pas encore correctement un deck de reference tres proche quand il existe ;
- le document de test phishing genere bien un nom de sortie propre, mais le rendu reste loin d'un bon exemple attendu.

Le choix utilisateur pour la suite est :

- strategie prioritaire : **Hybride**
- prioriser un exemple de sortie proche si disponible : **Oui**

## Constats techniques

### Faiblesses principales du pipeline actuel

1. `src/nodes/style_mapper.py`
- ne recupere que quelques documents RAG et en extrait des profils agreges trop generiques ;
- le LLM choisit uniquement un nom de profil, puis le code applique un style moyen par type ;
- il n'y a pas de mecanisme de "reference deck matching" slide/bloc proche.

2. `src/reference_styles.py`
- agrège les styles par type d'element mais perd les relations structurelles :
  - position dans la slide
  - ordre des blocs
  - role du placeholder
  - variabilite inter-slides
- ne distingue pas bien des styles differents pourtant tous classes en `body` ou `heading`.

3. `src/rag/store.py`
- les exemplars de style sont limites a quelques runs et quelques paragraphes ;
- aucune extraction de geometrie ou de placeholder metadata ;
- aucune notion de deck de reference "proche" dans son ensemble.

4. `src/nodes/parser.py` et `src/nodes/charter_applier.py`
- le parser PPTX reste base sur `shape_idx` / `para_idx` et ignore des infos utiles comme :
  - placeholder type
  - nom de layout
  - geometrie de shape
- l'application PPTX agit run par run, mais ne reconstruit pas assez les paragraphes/frames quand le style est herite du masque ou absent des runs.

5. `scripts/run_validation.py`
- permet de verifier un echantillon de styles, mais pas encore une comparaison structurelle avec un deck de reference cible.

## Objectif

Ameliorer fortement la qualite visuelle du rendu en adoptant une strategie hybride :

1. chercher un deck de reference tres proche (prioritairement un exemple de bonne sortie connu si pertinent) ;
2. utiliser ce deck pour guider la structure et les styles slide par slide / bloc par bloc ;
3. tomber en fallback sur des profils generiques derives des references quand aucun bon match n'est trouve ;
4. renforcer l'application PPTX pour couvrir davantage de cas reels.

## Strategie proposee

### Axe 1. Introduire la notion de "deck de reference prioritaire"

But : ne plus se contenter de profils moyens, mais exploiter un deck entier proche du document cible.

Implementation proposee :

1. Ajouter une etape de selection de references prioritaires dans `style_mapper.py` :
- recuperer plus de candidats RAG ;
- classer les candidats par similarite semantique + meme extension + proximite de structure (nb slides, types dominants, titres) ;
- permettre de privilegier un deck de sortie existant tres proche quand il est detecte.

2. Construire un objet de contexte explicite contenant :
- `primary_reference_deck`
- `secondary_reference_examples`
- `reference_profiles_fallback`

3. Si un deck de reference prioritaire est trouve :
- extraire ses slides/shape exemplars de facon plus riche ;
- demander au LLM d'associer chaque element cible a un bloc de reference proche, pas seulement a un type abstrait.

### Axe 2. Enrichir l'extraction des references PPTX/DOCX

But : donner au mapper et a l'applier des informations actionnables, pas seulement quelques fonts moyennees.

Implementation proposee :

1. Dans `src/rag/store.py`, enrichir les exemplars extraits avec :
- geometrie de shape (x, y, width, height) ;
- type de placeholder si disponible ;
- nom/layout de slide ;
- niveau de paragraphe ;
- indicateurs de frame (word wrap, auto size si lisibles) ;
- infos de paragraph format quand disponibles.

2. Pour DOCX, enrichir avec :
- style paragraph plus fiable ;
- alignment, spacing avant/apres, indentation, numbering/bullet si accessibles.

3. Conserver une extraction legere mais plus representative :
- pas seulement les 10 premiers exemplars ;
- echantillonnage par slide/type pour couvrir plusieurs variantes visuelles.

### Axe 3. Remplacer les profils "moyens" par des profils structures et variantes

But : eviter qu'un seul profil `body` ecrase tous les styles reellement differents.

Implementation proposee :

1. Refondre `reference_styles.py` pour gerer :
- des profils par type + variante (`body_left`, `body_orange`, `title_cover`, etc.) ;
- des signatures de bloc basees sur placeholder/geometrie/role ;
- des profils derives d'un deck de reference prioritaire.

2. Ne plus faire uniquement une moyenne globale ;
- preferer le style du match le plus proche ;
- fallback sur des stats robustes si aucun match local n'est disponible.

3. Garder la possibilite de retomber sur les profils generiques si aucun reference deck pertinent n'est trouve.

### Axe 4. Renforcer le parser et l'application PPTX

But : que le style soit reellement applique, y compris quand le deck source utilise des placeholders ou des styles herites.

Implementation proposee :

1. Enrichir `parser.py` pour stocker sur chaque element PPTX :
- placeholder type/index si present ;
- nom de shape ;
- geometrie ;
- nom de slide/layout si accessible.

2. Etendre `charter_applier.py` pour :
- appliquer les styles au niveau paragraphe et run ;
- creer un run stylise minimal si aucun run utile n'existe ;
- appliquer alignment / paragraph-level formatting quand possible ;
- mieux couvrir les placeholders de titre/date/pied de page/page number ;
- preparer une strategie explicite pour les tableaux PPTX si presents.

3. Pour DOCX, conserver le mode actuel mais mieux exploiter les profils de table derives des references plutot qu'un fallback pauvre.

### Axe 5. Validation ciblee contre le deck de phishing

But : iterer avec un critere de succes concret sur le cas utilisateur.

Implementation proposee :

1. Faire du document :
`C:\Users\BJPS1817\Downloads\Client - Campagne de phishing Phishing Point - Implémentation.pptx`

le cas de test principal.

2. Utiliser comme cible visuelle prioritaire si exploitable :
`C:\Users\BJPS1817\Downloads\Campagne-de-phishing-2026-06-15_13-54-46.pptx`

3. Etendre `scripts/run_validation.py` pour produire :
- un resume de styles ;
- un resume structurel slide/shape ;
- si possible, une comparaison elementaire entre output et reference deck (fonts/couleurs/positions pour un echantillon).

4. Valider apres implementation :
- nom de sortie propre ;
- score qualite > actuel ;
- plus de champs `font_name/font_size/color` non null sur les blocs principaux ;
- meilleure proximite visuelle sur les slides critiques (cover, body slides).

## Ordre d'implementation recommande

1. Refondre l'extraction de references dans `src/rag/store.py`.
2. Refondre `src/reference_styles.py` pour gerer profils/variantes/matching local.
3. Refondre `src/nodes/style_mapper.py` pour la strategie hybride :
- reference deck prioritaire
- fallback profils generiques
4. Enrichir `src/nodes/parser.py` avec metadata PPTX utiles.
5. Renforcer `src/nodes/charter_applier.py` pour l'application PPTX.
6. Etendre `scripts/run_validation.py` pour comparer reellement les resultats.
7. Revalider sur le fichier phishing.

## Risques

- La complexite PPTX peut augmenter vite si on veut couvrir tous les placeholders/heredites.
- Les metadonnees de style disponibles dans les references peuvent etre partielles selon les decks.
- Il faudra veiller a ne pas sur-ajuster uniquement au document phishing ; d'ou l'interet du mode hybride et des fallbacks.

## Critere de succes

Le plan sera considere reussi si :

1. l'agent s'appuie prioritairement sur un deck de reference proche quand il existe ;
2. le document phishing genere une sortie nommee proprement du type :
`Campagne-de-phishing-YYYY-MM-DD_HH-MM-SS.pptx` ;
3. les blocs principaux du PPTX de sortie ont des styles effectivement renseignes et coherents ;
4. le rendu est sensiblement plus proche du bon exemple utilisateur qu'avec l'implementation actuelle.
