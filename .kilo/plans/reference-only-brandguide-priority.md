# Plan pour privilegier uniquement les fichiers de reference et le brandguide

## Objectif utilisateur

L'utilisateur veut abandonner toute logique residuelle basee sur un JSON de charte et faire en sorte que l'agent respecte uniquement :

- les fichiers de reference
- le brandguide, qui est la source la plus importante

Cela implique que la generation, l'application de styles et le score de conformite doivent etre fortement pilotes par :

1. `GuidelinesFR.pdf` comme brandguide prioritaire
2. `Tools and templates PPT - FR/` comme source de templates / assets / exemples officiels
3. le BrandStore comme source de references metier secondaires

## Constat actuel

### Ce qui va deja dans le bon sens

- `src/nodes/style_mapper.py` indique deja explicitement de ne pas utiliser de charte JSON externe.
- `src/nodes/quality_checker.py` compare deja le `style_map` aux profils derives des references, pas a un JSON statique.
- `src/nodes/charter_applier.py` n'importe plus `ocd_charter.json`.

### Ce qui reste insuffisant ou ambigu

1. **Le brandguide n'est pas encore integre dans le pipeline**
- `GuidelinesFR.pdf` existe dans le repo, mais n'apparait pas dans `style_mapper.py`, `quality_checker.py` ou `reference_decks.py`.
- Donc aujourd'hui il n'est pas encore la source prioritaire qu'attend l'utilisateur.

2. **Le dossier `Tools and templates PPT - FR/` n'est pas encore traite comme source prioritaire explicite**
- il peut etre exploite indirectement si des fichiers y sont choisis manuellement plus tard, mais aucune logique claire ne le priorise aujourd'hui.

3. **Le score de conformite reste trop generique**
- `src/reference_styles.py` calcule un score sur typographie / couleurs / espacements / consistance a partir des references chargees.
- mais il ne distingue pas encore :
  - respect du brandguide
  - respect des templates officiels
  - respect des references metier

4. **La selection de reference primaire est encore trop basee sur proximite de deck**
- `src/reference_decks.py` ne considere pour l'instant que des `.pptx` voisins du document d'entree.
- cela ne garantit pas que la priorite aille au brandguide et aux templates officiels.

5. **Le rendu `copy_reference_deck` peut trop privilegier un exemple opportuniste**
- `src/nodes/charter_applier.py` peut copier un deck de reference voisin si le scoring le favorise.
- or l'utilisateur veut privilegier les fichiers de references et surtout le brandguide, pas une logique opportuniste basee sur n'importe quel deck proche.

## Intention fonctionnelle a implementer

Le comportement cible doit etre :

1. le brandguide sert a definir les regles les plus importantes de forme ;
2. les templates/outils officiels PPT-FR servent de reference structurelle et visuelle principale ;
3. les references metier du BrandStore servent a adapter la forme au type de livrable, sans jamais primer sur le brandguide ;
4. aucun JSON de charte ne doit etre utilise comme source de verite ;
5. le score de conformite doit surtout mesurer l'alignement avec le brandguide et les templates officiels.

## Strategie recommande

### Axe 1. Construire une couche de connaissance "brandguide + templates officiels"

But : rendre explicite une source de verite issue des fichiers et non d'un JSON code en dur.

Implementation recommandee :

1. Introduire un module dedie, par exemple `src/brand_knowledge.py`, charge de :
- extraire des regles exploitables depuis `GuidelinesFR.pdf`
- extraire des themes / layouts / polices / palettes depuis `Tools and templates PPT - FR/`
- produire une structure normalisee exploitable par le mapper, l'applier et le quality checker

2. Cette structure doit inclure au minimum :
- fonts dominantes / obligatoires
- couleurs autorisees / prioritaires
- tailles relatives title/subtitle/body/bullets
- familles de layouts/templates officiels
- indices de bonnes pratiques issus du guide utilisateur / best practice

3. Cette structure ne doit pas etre un JSON de charte "manuel" ;
- elle doit etre derivee des fichiers du repo a l'execution ou via une etape d'extraction/cache issue de ces fichiers.

### Axe 2. Faire du brandguide la priorite dans le style mapping

But : que `style_mapper.py` n'utilise plus seulement les references metier, mais raisonne dans cet ordre :

1. brandguide
2. templates officiels PPT-FR
3. BrandStore metier

Implementation recommandee :

1. Modifier `src/nodes/style_mapper.py` pour construire trois blocs de contexte distincts :
- `brandguide_rules`
- `official_template_profiles`
- `domain_reference_examples`

2. Changer le prompt system/human pour expliciter clairement :
- la priorite absolue du brandguide
- l'interdiction d'inventer des styles hors des templates officiels
- le fait que les references metier servent a choisir la variante adaptee, pas a contredire le brandguide

3. Faire en sorte que `ocd_style` ou son equivalent soit resolu d'abord contre les profils issus des templates officiels, puis seulement contre les references metier si necessaire.

### Axe 3. Recentrer `reference_decks.py` sur les templates et references officielles

But : eviter qu'un simple deck voisin prenne le dessus sur les sources officielles.

Implementation recommandee :

1. Etendre `src/reference_decks.py` pour prendre en compte :
- `Tools and templates PPT - FR/` comme pool prioritaire de decks officiels
- potentiellement `OFR_Best_Practice.pptx`, `OFR_Guide_Utilisateur.pptx` et les `.potx` comme references privilegiees

2. Changer la logique de ranking :
- bonus fort si le candidat vient des templates officiels
- bonus fort si le candidat correspond a un layout/usage compatible avec le document cible
- seulement ensuite, prise en compte de la proximite metier / textuelle

3. Limiter ou encadrer la strategie `copy_reference_deck` pour qu'elle ne se declenche que sur un deck officiel ou une reference explicitement autorisee.

### Axe 4. Faire du quality score un score axe d'abord sur brandguide + templates

But : le score de conformite doit refleter la demande utilisateur.

Implementation recommandee :

1. Modifier `src/nodes/quality_checker.py` et `src/reference_styles.py` pour decomposer le score en composantes explicites :
- conformite au brandguide
- conformite aux templates officiels
- conformite aux references metier
- preservation du contenu / non alteration structurelle

2. Donner une ponderation forte a :
- brandguide
- templates officiels

Par exemple, au niveau conceptuel :
- 45% brandguide
- 35% templates officiels
- 20% references metier

3. Ajouter des verifications de preservation de contenu :
- meme texte (ou diff minimal nul sur le texte extrait)
- meme nombre global d'elements textuels principaux
- pas de modification de fond metier pendant le styling

### Axe 5. Mieux exploiter `GuidelinesFR.pdf`

But : rendre le brandguide concretement utilisable.

Implementation recommandee :

1. Ajouter une extraction du PDF via une lib de lecture PDF si necessaire.
2. Convertir le guide en regles simples exploitables, pas en texte brut seulement.
3. Identifier dans le guide :
- recommandations typographiques
- usages des couleurs
- bonnes pratiques slides / lisibilite / hierarchie visuelle
- contraintes de marque

4. Mettre ces regles a disposition :
- du prompt de `style_mapper.py`
- du scoring dans `quality_checker.py`

## Fichiers a modifier lors de l'implementation

- `src/nodes/style_mapper.py`
- `src/nodes/quality_checker.py`
- `src/reference_styles.py`
- `src/reference_decks.py`
- `src/nodes/charter_applier.py`
- `src/rag/store.py` si besoin d'extraction enrichie depuis templates officiels
- nouveau module probable : `src/brand_knowledge.py`
- `scripts/run_validation.py` pour exposer les nouvelles dimensions du score

## Garde-fous a conserver

- ne pas reintroduire `ocd_charter.json` comme source de verite
- ne pas s'appuyer sur une palette hardcodee de maniere arbitraire
- ne pas faire primer une reference metier sur le brandguide
- ne pas modifier le fond documentaire si le besoin reste seulement la mise en forme

## Validation attendue apres implementation

1. Le code ne fait plus aucune reference active a un JSON de charte pour piloter le styling.
2. Le brandguide `GuidelinesFR.pdf` est charge et influence reellement le style mapping.
3. Les templates du dossier `Tools and templates PPT - FR/` sont traites comme references officielles prioritaires.
4. Le score de conformite affiche clairement une forte part liee au brandguide et aux templates officiels.
5. Sur un cas reel, l'agent produit un rendu plus conforme aux templates et au guide que a une simple moyenne de references metier.

## Hypothese importante

Le besoin exprime ici porte sur la logique de conformite visuelle. Si l'utilisateur veut en plus imposer strictement que le texte, les images et les tableaux restent intacts, cette contrainte devra etre preservee explicitement dans l'implementation, mais elle n'est pas redemande ici de facon detaillee dans ce message precis.
