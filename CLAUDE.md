# Brief citoyen

Site statique publié sur GitHub Pages : https://marccharton.github.io/Brief-Citoyen/
Un sujet de politique française chaque matin de semaine, expliqué depuis les bases, avec les arguments des deux côtés et des sources pour creuser. Les briefs sont entièrement rédigés par une IA (tâche planifiée Claude) et publiés automatiquement, sans relecture.

## Contexte privé : à lire en début de session

Ce fichier est public : il ne contient que la partie technique. L'intention du projet, l'historique et les décisions sont dans le Google Drive pro de Marc (connecteur Google Drive) :

- Document à lire en premier : `Outils / Claude / Mémoire globale / Dépôt · Brief-Citoyen / Contexte : Brief citoyen`
- Puis, pour le contexte général de Marc : `Outils / Claude / Mémoire globale / Mémoire globale (export)`, copie de sa mémoire Claude régénérée chaque nuit
- Convention générale : `Outils / Claude / Lisez-moi : organisation du contexte Claude`

Si le connecteur Drive n'est pas disponible, le signaler à Marc avant de prendre une décision éditoriale.

## Structure

```
data/briefs/<AAAA-MM-JJ>.json   un fichier par brief, source de vérité (suffixe -b si deux briefs le même jour)
scripts/build.py                générateur du site, Python standard sans dépendance
assets/style.css                style de toutes les pages (thème clair et sombre)
assets/brief.js                 boutons « Partager le lien » et « Télécharger le PDF »
assets/brief-pdf.js             générateur PDF (jsPDF 2.5.1 chargé depuis cdnjs)
index.html, <id>/index.html,    fichiers générés : ne pas les modifier à la main,
comment-c-est-fait/, feed.xml   relancer build.py
```

## Commandes

```
python3 scripts/build.py           # régénère tout le site depuis data/briefs/
python3 -m http.server 8000        # aperçu local sur http://localhost:8000/
```

## Format d'un brief

Voir le README pour le schéma complet. Champs : date, theme, title, subject, basics, terms, stakes, pro, con, local, sources (3 ou 4 sources « à creuser », avec lean), question, consulted (toutes les pages consultées), generated. Les briefs « Institutions » ont pro et con vides.

## Règles à respecter

- Une tâche planifiée publie un brief chaque matin de semaine vers 7 h 47 : elle écrit un JSON dans data/briefs/, lance build.py, commit et pousse sur main. Ne pas casser ce contrat (nom des champs, emplacement des fichiers, build.py sans argument).
- Toute modification de build.py doit garder la rétrocompatibilité avec les briefs existants (champs absents, anciens briefs sans consulted).
- Français correct avec tous les accents et toutes les apostrophes, dans le code comme dans les textes. Jamais le caractère « — ».
- Ton neutre et impersonnel dans tout texte affiché : pas de tutoiement ni de vouvoiement.
- Le site reste statique : aucune donnée privée dans ce dépôt public (pas d'adresses mail, de clés d'API ni de mots de passe).
- Le générateur PDF existe en deux copies : assets/brief-pdf.js (site) et l'artefact Claude « Briefs citoyens » (archive). Seule la copie du site évolue désormais.
