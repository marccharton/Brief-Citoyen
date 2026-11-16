# Brief citoyen

Site statique publié sur GitHub Pages : https://marccharton.github.io/Brief-Citoyen/
Un sujet de politique française chaque matin de semaine, expliqué depuis les bases, avec les arguments des deux côtés et des sources pour creuser. Les briefs sont entièrement rédigés par une IA (tâche planifiée Claude) et publiés automatiquement, sans relecture.

## Contexte privé : à lire en début de session

Ce fichier est public : il ne contient que la partie technique. L'intention du projet, l'historique et les décisions sont dans le Google Drive pro de Marc (connecteur Google Drive) :

- Document à lire en premier : `Outils / Claude / Mémoire globale / Dépôt · Brief-Citoyen / Contexte : Brief citoyen`
- Puis, pour le contexte général de Marc : `Outils / Claude / Mémoire globale / memoire-globale.md`, copie de sa mémoire Claude régénérée chaque nuit
- Convention générale : `Outils / Claude / Lisez-moi : organisation du contexte Claude`

Si le connecteur Drive n'est pas disponible, le signaler à Marc avant de prendre une décision éditoriale.

## Structure

```
Supabase public.briefs          source de vérité : une ligne par brief (id, data jsonb ; date, type,
                                categories recopiés par trigger et contrôlés par contraintes)
data/briefs/<AAAA-MM-JJ>.json   copie locale de la table, réécrite par fetch_supabase.py
                                (suffixe -b si deux briefs le même jour)
data/index.json                 liste légère (id, date, title, subject, type, categories) et libellés,
                                générée par build.py
scripts/fetch_supabase.py       Supabase vers data/briefs/, Python standard sans dépendance
scripts/build.py                génère data/index.json, feed.xml et comment-c-est-fait/, Python standard
.github/workflows/build.yml     fetch + build + push sur main (lun-ven 7 h 10 et 8 h 40 UTC, rattrapage
                                quotidien 17 h 23 UTC, à la main ou par repository_dispatch « brief-publie »)
index.html                      coquille statique de la liste, remplie par assets/index.js
brief/index.html                coquille statique d'un brief (brief/?id=AAAA-MM-JJ), remplie par assets/brief.js
404.html                        redirige les anciennes adresses /<id>/ vers brief/?id=<id>
assets/style.css                style de toutes les pages (thème clair et sombre)
assets/common.js                outils partagés (échappement, dates, chargement JSON)
assets/index.js                 liste et filtres de la page d'accueil
assets/brief.js                 rendu d'un brief, boutons « Partager le lien » et « Télécharger le PDF »
assets/brief-pdf.js             générateur PDF (jsPDF 2.5.1 chargé depuis cdnjs)
data/index.json, feed.xml,      fichiers générés : ne pas les modifier à la main,
comment-c-est-fait/             relancer build.py
```

## Commandes

```
python3 scripts/fetch_supabase.py  # recopie Supabase dans data/briefs/ (SUPABASE_URL, SUPABASE_KEY)
python3 scripts/build.py           # régénère tout le site depuis data/briefs/
python3 -m http.server 8000        # aperçu local sur http://localhost:8000/
```

## Format d'un brief

Voir le README pour le schéma complet. Champs : date, type (« actualite » ou « institutions »), categories (1 à 3, liste fermée définie dans scripts/build.py, jamais plus de 10 catégories au total), title, subject, basics, terms, stakes, pro, con, local, sources (3 ou 4 sources « à creuser », avec lean), question, consulted (toutes les pages consultées), generated. Les briefs de type « institutions » ont pro et con vides. Le champ theme des anciens briefs est remplacé par type et categories ; build.py garde une correspondance pour les données anciennes.

## Règles à respecter

- Une tâche planifiée rédige un brief chaque matin de semaine vers 7 h 47 et l'insère dans la table Supabase briefs ; la GitHub Action le publie ensuite. Ne pas casser ce contrat (nom des champs, table et colonnes, build.py et fetch_supabase.py sans argument).
- Ne jamais modifier un brief directement dans data/briefs/ : la prochaine exécution de l'Action l'écraserait avec la version de Supabase. Corriger la ligne en base.
- Projet Supabase « brief-citoyen » (organisation New Focus, région eu-west-3). Seule la clé publique sert, et uniquement via les secrets GitHub ; aucune clé dans le dépôt.
- Le rendu d'un brief est dans assets/brief.js (plus dans build.py) : c'est lui qui doit rester rétrocompatible avec les anciens briefs (champs absents, anciens briefs sans consulted). Les libellés de type et de catégorie viennent de data/index.json, donc de build.py.
- Toute modification de build.py doit garder la rétrocompatibilité avec les briefs existants (champs absents, anciens briefs sans consulted).
- Français correct avec tous les accents et toutes les apostrophes, dans le code comme dans les textes. Jamais le caractère « — ».
- Ton neutre et impersonnel dans tout texte affiché : pas de tutoiement ni de vouvoiement.
- Le site reste statique : aucune donnée privée dans ce dépôt public (pas d'adresses mail, de clés d'API ni de mots de passe).
- Le générateur PDF existe en deux copies : assets/brief-pdf.js (site) et l'artefact Claude « Briefs citoyens » (archive). Seule la copie du site évolue désormais.
