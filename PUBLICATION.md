# Publication de la veille écologique

Dans Settings > Pages > Build and deployment, choisir Source : GitHub Actions.
Puis ouvrir Actions > Publier la veille écologique > Run workflow si nécessaire.
Adresse attendue après un déploiement réussi : https://cbastienmarie.github.io/veille-ecologie/

Le workflow prépare uniquement le site public dans _site : il corrige le chemin du JSON et le tri des années sans écraser les fichiers source. Seuls index.html, articles.json et .nojekyll sont publiés.
La base peut se trouver dans data/articles.json ou, à défaut, dans articles.json à la racine.
Chaque push sur main reconstruit le site. Le test doit être effectué à l'adresse HTTPS publiée, pas par double-clic sur le fichier local.

## Actualisation scientifique
Ce workflow publie les données présentes ; il ne collecte pas de nouveaux articles.
L'ancien script update_articles.py doit être audité avant toute activation automatique : identifiants des revues, authentification API, structure des mots-clés, pagination et conservation des corrections éditoriales.
Les références, DOI, résumés et classifications de la base initiale doivent également être vérifiés avant diffusion scientifique.
La collecte et sa cadence de 15 jours ne sont donc pas activées par ce correctif.
