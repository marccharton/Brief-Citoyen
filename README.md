# Brief citoyen

Un sujet de politique française chaque matin de semaine, expliqué depuis les bases, avec les arguments des deux côtés et des sources pour creuser.

Site : https://marccharton.github.io/Brief-Citoyen/

## Fonctionnement

- `data/briefs/<AAAA-MM-JJ>.json` : un fichier par brief (la source de vérité).
- `scripts/build.py` : génère le site à partir des JSON (Python standard, sans dépendance).
- `index.html`, `<AAAA-MM-JJ>/index.html`, `feed.xml` : fichiers générés, publiés par GitHub Pages.
- `assets/` : style, script de la page, générateur de PDF (jsPDF).

Ajouter un brief : déposer son JSON dans `data/briefs/`, lancer `python3 scripts/build.py`, puis committer et pousser sur `main`. Une tâche planifiée Claude le fait chaque matin de semaine.

## Format d'un brief

```json
{"date": "AAAA-MM-JJ", "type": "actualite", "categories": ["Économie et budget"],
 "title": "...", "subject": "...",
 "basics": ["..."], "terms": [{"term": "...", "def": "..."}], "stakes": ["..."],
 "pro": {"label": "Pour", "who": "...", "args": ["..."]},
 "con": {"label": "Contre", "who": "...", "args": ["..."]},
 "local": ["..."], "sources": [{"lean": "Plutôt à gauche", "name": "...", "url": "https://...", "note": "..."}],
 "question": "...",
 "consulted": [{"name": "...", "url": "https://..."}],
 "generated": "AAAA-MM-JJ"}
```

`sources` : les 3 ou 4 sources mises en avant (« Sources à creuser »). `consulted` : toutes les pages consultées pour construire le brief, affichées en fin d'article.

`type` : « actualite » (lundi, mercredi, vendredi) ou « institutions » (mardi, jeudi).
`categories` : 1 à 3 valeurs, uniquement dans cette liste fermée (définie dans `scripts/build.py`, 10 au maximum) : Économie et budget, Protection sociale, Vie démocratique, Justice et sécurité, Environnement et énergie, Territoires et quotidien, Europe et international, Éducation et culture, Société.
