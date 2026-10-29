# Tableau de bord — Veille écologie & biodiversité

Tableau de bord interactif de veille scientifique en écologie, centré sur les pressions directes sur la biodiversité : fragmentation et destruction des habitats, changement climatique, pollutions dont pesticides, espèces invasives, chasse et pêche, et impacts des activités humaines.

## Publication

Le dépôt est conçu pour GitHub Pages :

- Branche : `main`
- Dossier publié : racine du dépôt
- URL : `https://<votre-compte>.github.io/dashboard-ecologie/`

Dans **Settings → Pages → Build and deployment**, choisir :

- Source : **Deploy from a branch**
- Branch : `main`
- Folder : `/ (root)`

## Actualisation tous les 15 jours

Le workflow `.github/workflows/update.yml` s’exécute automatiquement les 1er et 16 de chaque mois à 06 h 00 UTC, soit approximativement tous les 15 jours. Il peut aussi être lancé manuellement depuis **Actions → Mettre à jour la veille écologique → Run workflow**.

Il interroge OpenAlex, met à jour `data/articles.json`, commite les changements puis redéploie GitHub Pages.

Ajoutez un secret de dépôt recommandé :

- `OPENALEX_MAILTO` : votre adresse e-mail professionnelle, pour identifier poliment vos requêtes auprès d’OpenAlex.

## Revues suivies

Nature Climate Change, Global Change Biology, Frontiers in Ecology and the Environment, Trends in Ecology & Evolution, Ecology, Journal of Ecology, Journal of Applied Ecology, Oecologia, Landscape Ecology, Ecography, Naturae, Sciences Eaux & Territoires, Écologie & Politique, Revue d’Écologie (La Terre et la Vie).

## Structure

```text
.
├── index.html
├── data/articles.json
├── scripts/update_articles.py
├── .github/workflows/update.yml
├── README.md
└── LICENSE
```

## Qualité éditoriale

Le script OpenAlex remplit automatiquement les métadonnées et un classement provisoire. Avant publication, vérifiez notamment :

- le taxon et la zone géographique ;
- le résumé de médiation scientifique ;
- le focus et la pression principale ;
- la distinction entre résultats observés, modélisations et scénarios.
