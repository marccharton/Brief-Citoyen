# Brief citoyen

Un sujet de politique française chaque matin de semaine, expliqué depuis les bases, avec les arguments des deux côtés et des sources pour creuser.

Site : https://marccharton.github.io/Brief-Citoyen/

## Fonctionnement

- Supabase, table `public.briefs` : la source de vérité. Une ligne par brief (`id`, `data` avec le JSON complet ; `date`, `type` et `categories` en sont recopiés automatiquement et contrôlés par la base). Lecture publique, écriture réservée au serveur.
- `scripts/fetch_supabase.py` : recopie la table dans `data/briefs/<id>.json` (Python standard, sans dépendance).
- `scripts/build.py` : génère `data/index.json` (liste légère des briefs), `feed.xml` et la page « Comment c'est fait ».
- `.github/workflows/build.yml` : GitHub Action qui enchaîne les deux scripts puis pousse sur `main` : du lundi au vendredi après la rédaction, un passage de rattrapage chaque jour à 17 h 23 UTC, à la demande (onglet Actions, « Run workflow ») ou par un `repository_dispatch` de type `brief-publie`.
- `index.html` et `brief/index.html` : coquilles statiques, écrites à la main. Elles chargent les JSON en JavaScript : la liste lit `data/index.json`, un brief s'affiche à l'adresse `brief/?id=AAAA-MM-JJ` et lit `data/briefs/<id>.json`.
- `404.html` : redirige les anciennes adresses `/<AAAA-MM-JJ>/` vers `brief/?id=AAAA-MM-JJ`.
- `assets/` : style et scripts des pages (`common.js`, `index.js`, `brief.js`).
- `methode/consignes.md` : consignes éditoriales données à l'IA, publiques et versionnées.

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
 "consulted": [{"n": 1, "name": "...", "url": "https://...", "type": "Presse nationale", "extrait": "..."}],
 "generated": "AAAA-MM-JJ",
 "fiche": {"modele": "...", "consignes": "v1", "genere_a": "7 h 52",
   "recherches": ["..."], "reperage": [{"name": "...", "url": "https://..."}],
   "candidats": [{"sujet": "...", "categorie": "...", "nb_sources": 6,
     "score": {"couverture": 3, "variete": 2, "deux_cotes": 1, "fraicheur": 2, "impact": 1, "local": 0, "repetition": 0},
     "total": 9, "decision": "retenu", "raison": "..."}],
   "progression": "", "choix": "..."}}
```

Repères de source : dans `basics`, `stakes`, `local`, `pro.args` et `con.args`, chaque phrase se termine par `[n]`, `[n,m]` ou `[IA]`. `n` renvoie au champ `n` de `consulted`. `extrait` est un court passage copié de la page, utilisé pour ouvrir la source au bon endroit. `fiche` est la fiche technique : pour un brief « institutions », `recherches`, `reperage` et `candidats` sont vides et `progression` indique la notion choisie. Les briefs antérieurs au 17/11/2026 n'ont ni repères ni `fiche`.

`sources` : les 3 ou 4 sources mises en avant (« Sources à creuser »). `consulted` : toutes les pages consultées pour construire le brief, affichées en fin d'article.

`type` : « actualite » (lundi, mercredi, vendredi) ou « institutions » (mardi, jeudi).
`categories` : 1 à 3 valeurs, uniquement dans cette liste fermée (définie dans `scripts/build.py`, 10 au maximum) : Économie et budget, Protection sociale, Vie démocratique, Justice et sécurité, Environnement et énergie, Territoires et quotidien, Europe et international, Éducation et culture, Société.
