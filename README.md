# Brief citoyen

Un sujet de politique française chaque matin de semaine, expliqué depuis les bases, avec les arguments des deux côtés et des sources pour creuser.

Site : https://marccharton.github.io/Brief-Citoyen/

## Fonctionnement

- Supabase, table `public.briefs` : la source de vérité. Une ligne par brief (`id`, `data` avec le JSON complet ; `date`, `type` et `categories` en sont recopiés automatiquement et contrôlés par la base). Lecture publique, écriture réservée au serveur.
- `scripts/fetch_supabase.py` : recopie la table dans `data/briefs/<id>.json` (Python standard, sans dépendance).
- `scripts/build.py` : génère le site à partir des JSON.
- `.github/workflows/build.yml` : GitHub Action qui enchaîne les deux scripts puis pousse sur `main`, du lundi au vendredi après la rédaction, ou à la demande (onglet Actions, « Run workflow »).
- `index.html`, `<AAAA-MM-JJ>/index.html`, `feed.xml` : fichiers générés, publiés par GitHub Pages.
- `assets/` : style, script de la page, générateur de PDF (jsPDF).

Ajouter un brief : insérer une ligne dans la table `briefs` (`insert into public.briefs (id, data) values (...)`), puis attendre la GitHub Action ou la lancer à la main. Une tâche planifiée Claude rédige un brief chaque matin de semaine.

L'Action a besoin de deux secrets du dépôt (Settings, Secrets and variables, Actions) : `SUPABASE_URL` et `SUPABASE_KEY` (la clé publique « publishable » du projet).

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
