#!/usr/bin/env python3
"""Construit le site Brief citoyen à partir de data/briefs/*.json.

Usage : python3 scripts/build.py
Produit : index.html (liste), <id>/index.html (un brief), feed.xml (flux RSS).
Uniquement la bibliothèque standard de Python.
"""
import html
import json
import re
import sys
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "briefs"
SITE_URL = "https://marccharton.github.io/Brief-Citoyen/"
SITE_NAME = "Brief citoyen"
SITE_DESC = ("Un sujet de politique française chaque matin de semaine, expliqué depuis les bases, "
             "avec les arguments des deux côtés et des sources pour creuser.")

MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
        "septembre", "octobre", "novembre", "décembre"]
JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
ID_RE = re.compile(r"^\d{4}-\d{2}-\d{2}(-[a-z0-9]+)?$")

# Type d'un brief et liste fermée des catégories (10 au maximum, 1 à 3 par brief)
TYPES = {"actualite": "Actualité", "institutions": "Comprendre les institutions"}
CATEGORIES = [
    ("Économie et budget", "Finances publiques, impôts, pouvoir d'achat, entreprises, emploi."),
    ("Protection sociale", "Retraites, santé, Sécurité sociale, chômage, aides sociales."),
    ("Vie démocratique", "Élections, partis, Parlement, Constitution, fonctionnement des institutions."),
    ("Justice et sécurité", "Justice, police, ordre public, libertés publiques."),
    ("Environnement et énergie", "Climat, biodiversité, énergie, agriculture."),
    ("Territoires et quotidien", "Collectivités locales, transports, logement, Toulouse et Occitanie."),
    ("Europe et international", "Union européenne, relations internationales, défense."),
    ("Éducation et culture", "École, université, recherche, culture, médias."),
    ("Société", "Mobilisations, égalité, immigration, numérique, vie quotidienne."),
]
CATEGORY_NAMES = [c for c, _ in CATEGORIES]
LEGACY_THEMES = {"Économie": ["Économie et budget"], "Economie": ["Économie et budget"], "Social": ["Protection sociale"],
                 "Institutions": ["Vie démocratique"], "National": ["Vie démocratique"], "Local": ["Territoires et quotidien"],
                 "Environnement": ["Environnement et énergie"], "Europe": ["Europe et international"]}


def btype(b):
    t = b.get("type")
    if t in TYPES:
        return t
    return "institutions" if b.get("theme") == "Institutions" and not lst((b.get("pro") or {}).get("args")) else "actualite"


def bcats(b):
    cats = [c for c in lst(b.get("categories")) if c in CATEGORY_NAMES][:3]
    return cats or LEGACY_THEMES.get(b.get("theme"), [])


def e(s):
    return html.escape(str(s if s is not None else ""), quote=True)


def lst(v):
    if isinstance(v, list):
        return [x for x in v if x not in (None, "", {})]
    return [v] if v else []


def parse_date(s):
    return datetime.strptime(str(s)[:10], "%Y-%m-%d")


def date_long(s):
    d = parse_date(s)
    return f"{JOURS[d.weekday()]} {d.day} {MOIS[d.month - 1]} {d.year}"


def date_short(s):
    d = parse_date(s)
    return f"{d.day} {MOIS[d.month - 1]}"


def is_https(u):
    return isinstance(u, str) and u.startswith("https://")


def load():
    briefs = []
    for f in sorted(DATA.glob("*.json")):
        bid = f.stem
        if not ID_RE.match(bid):
            print(f"ignoré (nom invalide) : {f.name}", file=sys.stderr)
            continue
        b = json.loads(f.read_text(encoding="utf-8"))
        if not b.get("date") or not b.get("title"):
            print(f"ignoré (date ou titre manquant) : {f.name}", file=sys.stderr)
            continue
        b["id"] = bid
        briefs.append(b)
    briefs.sort(key=lambda b: (b["date"], b["id"]), reverse=True)
    return briefs


HEAD_FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
              '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
              '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Literata:ital,opsz,wght@0,7..72,500;0,7..72,650;1,7..72,500&family=Atkinson+Hyperlegible:wght@400;700&display=swap">')


def head(title, desc, url, prefix, og_type="website"):
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{e(url)}">
<meta property="og:site_name" content="{SITE_NAME}">
<meta property="og:type" content="{og_type}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{e(url)}">
<meta property="og:locale" content="fr_FR">
<meta name="twitter:card" content="summary">
<link rel="alternate" type="application/rss+xml" title="{SITE_NAME}" href="{prefix}feed.xml">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='7' fill='%231A2B42'/%3E%3Cpath d='M9 10h14M9 16h14M9 22h9' stroke='%23B0C4DE' stroke-width='2.6' stroke-linecap='round'/%3E%3C/svg%3E">
{HEAD_FONTS}
<link rel="stylesheet" href="{prefix}assets/style.css">
</head>
<body>"""


FOOT = """<footer class="foot"><div class="wrap">
<p>Brief citoyen est entièrement rédigé par une intelligence artificielle, à partir de sources publiques citées dans chaque brief. C'est un outil de vulgarisation : il peut contenir des imprécisions, et les sources font foi.</p>
<p><a href="{prefix}">Tous les briefs</a> · <a href="{prefix}comment-c-est-fait/">Comment c'est fait</a> · <a href="{prefix}feed.xml">Flux RSS</a> · <a href="https://marccharton.github.io/">Marc Charton</a></p>
</div></footer>
</body>
</html>
"""


def render_brief(b, prev_b, next_b):
    prefix = "../"
    url = f"{SITE_URL}{b['id']}/"
    is_inst = btype(b) == "institutions"
    title = f"{b['title']} · {SITE_NAME}"
    out = [head(title, b.get("subject") or SITE_DESC, url, prefix, "article")]

    theme = f'<span class="dot">·</span><span>{e(TYPES[btype(b)])}</span>' + "".join(f'<span class="dot">·</span><span>{e(c)}</span>' for c in bcats(b))
    out.append(f"""<header class="band"><div class="wrap">
<a class="back" href="{prefix}">← Tous les briefs</a>
<p class="eyebrow"><span>Brief citoyen</span><span class="dot">·</span><time datetime="{e(b['date'])}">{e(date_long(b['date']))}</time>{theme}</p>
<h1>{e(b['title'])}</h1>
{f'<p class="subject">{e(b["subject"])}</p>' if b.get('subject') else ''}
<div class="tools">
<button class="tool" type="button" id="share">Partager le lien</button>
<button class="tool" type="button" id="pdf">Télécharger le PDF</button>
<span class="toast" id="toast" role="status"></span>
</div>
</div></header>
<main class="wrap article">""")

    basics, terms = lst(b.get("basics")), [t for t in lst(b.get("terms")) if isinstance(t, dict) and t.get("term")]
    if basics or terms:
        out.append('<section class="basics' + (' with-terms' if terms else '') + '">')
        out.append(f'<div class="prose"><h2 class="kicker">{"L’éclairage" if is_inst else "Les bases"}</h2>')
        out += [f"<p>{e(p)}</p>" for p in basics]
        out.append("</div>")
        if terms:
            out.append('<aside class="terms"><h2 class="kicker">Les mots à connaître</h2><dl>')
            out += [f"<div><dt>{e(t['term'])}</dt><dd>{e(t.get('def', ''))}</dd></div>" for t in terms]
            out.append("</dl></aside>")
        out.append("</section>")

    stakes = lst(b.get("stakes"))
    if stakes:
        out.append(f'<section class="box stakes"><h2 class="kicker">{"Pourquoi ça compte" if is_inst else "Ce qui se joue"}</h2>')
        out += [f"<p>{e(p)}</p>" for p in stakes]
        out.append("</section>")

    pro, con = b.get("pro") or {}, b.get("con") or {}
    if lst(pro.get("args")) or lst(con.get("args")):
        out.append('<section class="sides">')
        for cls, s, default in (("pro", pro, "Pour"), ("con", con, "Contre")):
            if not lst(s.get("args")):
                continue
            out.append(f'<div class="side {cls}"><h2>{e(s.get("label") or default)}</h2>')
            if s.get("who"):
                out.append(f'<p class="who">{e(s["who"])}</p>')
            out.append("<ul>" + "".join(f"<li>{e(a)}</li>" for a in lst(s.get("args"))) + "</ul></div>")
        out.append("</section>")

    local = lst(b.get("local"))
    if local:
        out.append('<section class="box local"><h2 class="kicker">À Toulouse et en Occitanie</h2>')
        out += [f"<p>{e(p)}</p>" for p in local]
        out.append("</section>")

    sources = [s for s in lst(b.get("sources")) if isinstance(s, dict) and s.get("name")]
    if sources:
        out.append('<section class="sources"><h2 class="kicker">Sources à creuser</h2><ul>')
        for s in sources:
            lean = str(s.get("lean") or "")
            cls = "l" if "gauche" in lean.lower() else "r" if "droite" in lean.lower() else "n"
            name = (f'<a href="{e(s["url"])}" target="_blank" rel="noopener">{e(s["name"])}</a>'
                    if is_https(s.get("url")) else e(s["name"]))
            host = re.sub(r"^https://(www\.)?", "", s["url"]).split("/")[0] if is_https(s.get("url")) else ""
            out.append(f'<li class="{cls}"><span class="lean">{e(lean)}</span><span class="name">{name}</span>'
                       + (f'<span class="note">{e(s["note"])}</span>' if s.get("note") else "")
                       + (f'<span class="host">{e(host)}</span>' if host else "") + "</li>")
        out.append("</ul></section>")

    if b.get("question"):
        out.append(f'<section class="question"><h2 class="kicker">Pour se faire un avis</h2><p>{e(b["question"])}</p></section>')

    consulted = [s for s in lst(b.get("consulted")) if isinstance(s, dict) and s.get("name")]
    used, note = consulted, ""
    if not used:
        used = sources
        note = ("La liste complète des sources consultées n'a pas été conservée pour ce brief, publié avant "
                "l'ajout de cette rubrique : seules les sources citées plus haut sont indiquées.")
    if used:
        items = []
        for s in used:
            label = e(s["name"])
            if is_https(s.get("url")):
                host = re.sub(r"^https://(www\.)?", "", s["url"]).split("/")[0]
                items.append(f'<li><a href="{e(s["url"])}" target="_blank" rel="noopener">{label}</a> <span class="h">{e(host)}</span></li>')
            else:
                items.append(f"<li>{label}</li>")
        out.append('<section class="used"><h2 class="kicker">Sources utilisées pour ce brief</h2>'
                   + (f'<p class="note">{e(note)}</p>' if note else
                      '<p class="note">Toutes les pages consultées pour construire ce brief, y compris celles qui ne sont pas citées plus haut.</p>')
                   + '<ol>' + "".join(items) + '</ol></section>')

    nav = []
    if next_b:
        nav.append(f'<a class="nav-prev" href="{prefix}{next_b["id"]}/"><span>Brief suivant</span>{e(next_b["title"])}</a>')
    if prev_b:
        nav.append(f'<a class="nav-next" href="{prefix}{prev_b["id"]}/"><span>Brief précédent</span>{e(prev_b["title"])}</a>')
    if nav:
        out.append('<nav class="pager">' + "".join(nav) + "</nav>")
    out.append("</main>")

    data = {k: v for k, v in b.items() if k not in ("imported", "id")}
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    out.append(f"""<script type="application/json" id="brief-data">{payload}</script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js" defer></script>
<script src="{prefix}assets/brief-pdf.js" defer></script>
<script src="{prefix}assets/brief.js" defer></script>""")
    out.append(FOOT.format(prefix=prefix))
    return "\n".join(out)


def render_index(briefs):
    prefix = ""
    out = [head(f"{SITE_NAME} · un sujet politique expliqué chaque matin", SITE_DESC, SITE_URL, prefix)]
    used = {c for b in briefs for c in bcats(b)}
    cats = [c for c in CATEGORY_NAMES if c in used]
    type_chips = "".join(f'<button class="chip" type="button" data-type="{k}" aria-pressed="false">{e(v)}</button>' for k, v in TYPES.items())
    cat_chips = "".join(f'<button class="chip" type="button" data-cat="{e(c)}" aria-pressed="false">{e(c)}</button>' for c in cats)
    out.append(f"""<header class="band home"><div class="wrap">
<p class="eyebrow"><span>Politique française</span><span class="dot">·</span><span>{len(briefs)} brief{'s' if len(briefs) > 1 else ''}</span></p>
<h1>{SITE_NAME}</h1>
<p class="subject">{e(SITE_DESC)}</p>
<p class="howto"><a href="comment-c-est-fait/">Comment c'est fait, et ses limites →</a></p>
</div></header>
<main class="wrap">
<div class="filters" id="filters">
<div class="frow" data-group="type"><span class="flabel">Type</span><button class="chip" type="button" data-type="" aria-pressed="true">Tous</button>{type_chips}</div>
<div class="frow" data-group="cat"><span class="flabel">Catégorie</span><button class="chip" type="button" data-cat="" aria-pressed="true">Toutes</button>{cat_chips}</div>
</div>
<ol class="list" id="list">""")
    month = None
    for b in briefs:
        d = parse_date(b["date"])
        m = f"{MOIS[d.month - 1].capitalize()} {d.year}"
        if m != month:
            out.append(f'<li class="month">{e(m)}</li>')
            month = m
        out.append(f"""<li class="item" data-type="{btype(b)}" data-cats="{e('|'.join(bcats(b)))}"><a href="{b['id']}/">
<span class="when"><span class="d">{JOURS[d.weekday()][:3]}.</span><span class="n">{d.day}</span></span>
<span class="body"><span class="meta"><span class="type {btype(b)}">{e(TYPES[btype(b)])}</span>{''.join(f'<span class="cat">{e(c)}</span>' for c in bcats(b))}</span><span class="t">{e(b['title'])}</span><span class="s">{e(b.get('subject', ''))}</span></span>
</a></li>""")
    out.append("""</ol>
</main>
<script>
(function(){
  var box = document.getElementById('filters'); if (!box) return;
  var sel = {type: '', cat: ''};
  box.addEventListener('click', function(ev){
    var c = ev.target.closest('.chip'); if (!c) return;
    var row = c.closest('.frow'), g = row.getAttribute('data-group');
    sel[g] = c.getAttribute(g === 'type' ? 'data-type' : 'data-cat');
    row.querySelectorAll('.chip').forEach(function(x){ x.setAttribute('aria-pressed', String(x === c)); });
    document.querySelectorAll('#list .item').forEach(function(it){
      var okT = !sel.type || it.getAttribute('data-type') === sel.type;
      var okC = !sel.cat || it.getAttribute('data-cats').split('|').indexOf(sel.cat) >= 0;
      it.hidden = !(okT && okC);
    });
    document.querySelectorAll('#list .month').forEach(function(mo){
      var n = mo.nextElementSibling, any = false;
      while (n && !n.classList.contains('month')){ if (!n.hidden) any = true; n = n.nextElementSibling; }
      mo.hidden = !any;
    });
  });
})();
</script>""")
    out.append(FOOT.format(prefix=prefix))
    return "\n".join(out)


def render_feed(briefs):
    items = []
    for b in briefs[:30]:
        d = parse_date(b["date"]).replace(hour=7, minute=47, tzinfo=timezone.utc)
        items.append(f"""<item><title>{e(b['title'])}</title><link>{SITE_URL}{b['id']}/</link>
<guid isPermaLink="true">{SITE_URL}{b['id']}/</guid><pubDate>{format_datetime(d)}</pubDate>
<description>{e(b.get('subject', ''))}</description>{''.join(f"<category>{e(c)}</category>" for c in bcats(b))}</item>""")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>{SITE_NAME}</title><link>{SITE_URL}</link>
<description>{e(SITE_DESC)}</description><language>fr-FR</language>
{''.join(items)}
</channel></rss>
"""


SOURCE_RULES = [
    ("n", "Les sources primaires d'abord",
     "Quand elles existent : le texte de loi, le rapport officiel, les données publiques, le communiqué de l'organisation concernée. C'est la base la plus sûre pour un chiffre ou une citation."),
    ("n", "Des médias identifiés",
     "Pour la presse, des médias avec une rédaction et une ligne éditoriale connues. Pas de réseaux sociaux, de blogs anonymes ni de sites sans auteur."),
    ("n", "Plusieurs sensibilités",
     "Chaque brief cite au moins une source perçue plutôt à gauche, une plutôt à droite et une neutre ou institutionnelle."),
    ("n", "Vérifiable par tous",
     "Chaque source citée a un lien vers l'article ou le document lui-même, pour que chacun puisse aller lire."),
]


def host_of(u):
    return re.sub(r"^https://(www\.)?", "", u).split("/")[0] if is_https(u) else ""


def classif_block():
    cats = "".join(f'<div><dt>{e(c)}</dt><dd>{e(d)}</dd></div>' for c, d in CATEGORIES)
    return f"""<section class="basics with-terms">
<div class="prose">
<h2 class="kicker">Deux types de briefs</h2>
<p><strong>Actualité</strong> (lundi, mercredi, vendredi) : un sujet du moment, expliqué depuis les bases, avec les arguments des deux côtés.</p>
<p><strong>Comprendre les institutions</strong> (mardi, jeudi) : une notion du fonctionnement de la Ve République expliquée simplement, de la Constitution au 49-3, sans débat pour ou contre.</p>
<p>Chaque brief est rangé dans une à trois catégories, choisies dans une liste courte et stable, pour retrouver facilement tout ce qui touche à un même domaine.</p>
</div>
<aside class="terms"><h2 class="kicker">Les catégories</h2><dl>{cats}</dl></aside>
</section>
"""


def sources_block(briefs):
    groups = [f'<div class="refgroup {cls}"><h3>{e(t)}</h3><p>{e(d)}</p></div>' for cls, t, d in SOURCE_RULES]
    counts, leans, total = {}, {"l": 0, "r": 0, "n": 0}, 0
    for b in briefs:
        for src in lst(b.get("sources")):
            if not isinstance(src, dict) or not src.get("name"):
                continue
            total += 1
            lean = str(src.get("lean") or "").lower()
            leans["l" if "gauche" in lean else "r" if "droite" in lean else "n"] += 1
            h = host_of(src.get("url")) or "sans lien"
            counts[h] = counts.get(h, 0) + 1
    rows = "".join(f'<li><span class="h">{e(h)}</span><span class="c">{c}</span></li>'
                   for h, c in sorted(counts.items(), key=lambda x: (-x[1], x[0])))
    def pct(n):
        return round(100 * n / total) if total else 0
    bar = (f'<div class="leanbar" role="img" aria-label="{leans["l"]} sources plutôt à gauche, {leans["n"]} neutres ou institutionnelles, {leans["r"]} plutôt à droite">'
           f'<span class="l" style="flex:{leans["l"] or 0.0001}"></span><span class="n" style="flex:{leans["n"] or 0.0001}"></span><span class="r" style="flex:{leans["r"] or 0.0001}"></span></div>'
           f'<p class="leanlegend"><span class="l">Plutôt à gauche : {leans["l"]} ({pct(leans["l"])} %)</span>'
           f'<span class="n">Neutres ou institutionnelles : {leans["n"]} ({pct(leans["n"])} %)</span>'
           f'<span class="r">Plutôt à droite : {leans["r"]} ({pct(leans["r"])} %)</span></p>')
    return f"""<section class="refs">
<h2 class="kicker">Où l'IA cherche ses informations</h2>
<div class="prose"><p>Il n'y a pas de liste de médias choisis à l'avance : chaque matin, l'IA fait des recherches sur le web à partir de l'actualité. Plutôt qu'une liste, elle suit des règles. Le classement d'une source à gauche ou à droite est indicatif : il reprend la perception courante de sa ligne éditoriale.</p></div>
<div class="refgrid">{''.join(groups)}</div>
</section>

<section class="refs used">
<h2 class="kicker">Les sources réellement citées</h2>
<div class="prose"><p>Calculé automatiquement à partir des {len(briefs)} briefs publiés : {total} sources citées au total. Ce décompte se met à jour à chaque nouveau brief.</p></div>
{bar}
<ul class="hosts">{rows}</ul>
</section>
"""


def render_about(briefs):
    prefix = "../"
    url = f"{SITE_URL}comment-c-est-fait/"
    desc = ("Comment Brief citoyen est fabriqué : une intelligence artificielle, des sources publiques, "
            "des sujets plutôt que des partis. Et les limites de l'exercice.")
    out = [head(f"Comment c'est fait · {SITE_NAME}", desc, url, prefix)]
    out.append(f"""<header class="band"><div class="wrap">
<a class="back" href="{prefix}">← Tous les briefs</a>
<p class="eyebrow"><span>Brief citoyen</span><span class="dot">·</span><span>À propos</span></p>
<h1>Comment c'est fait</h1>
<p class="subject">Une idée simple : comprendre un sujet avant de savoir qui le défend.</p>
</div></header>
<main class="wrap article about">

<section class="basics with-terms">
<div class="prose">
<h2 class="kicker">L'intention</h2>
<p>La politique arrive souvent par les partis, les personnalités et les petites phrases. Brief citoyen fait le chemin inverse : il part d'un sujet concret (un budget, une loi, une réforme, une institution) et l'explique depuis le début.</p>
<p>Chaque brief s'adresse à quelqu'un qui n'y connaît rien. Pas de prérequis, pas de sigle sans explication : le contexte d'abord, les mots ensuite, puis ce qui se joue vraiment.</p>
<p>Les arguments sont présentés pour ce qu'ils disent, pas pour le camp qui les porte. L'idée est de pouvoir se faire un avis sur une idée, une posture, une mesure, avant de la ranger quelque part sur l'échiquier politique ou de la rattacher à un parti. La politique vient après.</p>
</div>
<aside class="terms">
<h2 class="kicker">En trois principes</h2>
<dl>
<div><dt>Des sujets, pas des partis</dt><dd>On part d'une question concrète qui touche la vie quotidienne, pas d'une étiquette.</dd></div>
<div><dt>Partir de zéro</dt><dd>Chaque brief explique les bases et définit ses mots, pour que tout le monde puisse suivre.</dd></div>
<div><dt>Se faire un avis d'abord</dt><dd>Les arguments des deux côtés, à égalité. Qui les porte n'est indiqué qu'en second, pour situer.</dd></div>
</dl>
</aside>
</section>

<section class="box stakes">
<h2 class="kicker">Entièrement rédigé par une IA</h2>
<p>Les briefs sont écrits par Claude, une intelligence artificielle développée par Anthropic. Une tâche automatique se lance chaque matin de semaine : elle choisit un sujet, fait ses recherches, rédige le brief et le publie ici. Aucun humain ne relit chaque brief avant sa publication.</p>
</section>

<section>
<h2 class="kicker">Le processus, en cinq étapes</h2>
<ol class="steps">
<li><strong>Choisir un sujet.</strong> Le lundi, le mercredi et le vendredi, un sujet d'actualité des derniers jours, en variant les thèmes et en évitant ceux déjà traités. Le mardi et le jeudi, un « Éclairage Institutions » qui explique une notion de base : la Constitution, le 49-3, le Sénat…</li>
<li><strong>Se documenter.</strong> L'IA fait des recherches sur le web en suivant les règles décrites plus bas : sources primaires d'abord, médias identifiés, plusieurs sensibilités. Pour le contexte général (comment fonctionne une institution, l'histoire d'une réforme), elle s'appuie aussi sur ses propres connaissances, apprises avant sa mise en service : cette partie-là n'est pas sourcée article par article.</li>
<li><strong>Rédiger.</strong> Les bases, les mots à connaître, ce qui se joue, les arguments pour et contre avec ceux qui les portent, un angle local sur Toulouse et l'Occitanie quand c'est pertinent, des sources pour creuser et une question ouverte.</li>
<li><strong>Contrôler la forme.</strong> Des vérifications automatiques portent sur le format, l'orthographe et le ton neutre. Elles ne vérifient pas les faits.</li>
<li><strong>Publier.</strong> Le brief arrive sur ce site vers 8 h, avec son propre lien et une version PDF à partager.</li>
</ol>
</section>

{classif_block()}
{sources_block(briefs)}
<section class="sides limits">
<div class="side con">
<h2>Les limites</h2>
<p class="who">À garder en tête en lisant un brief</p>
<ul>
<li>Une IA peut se tromper : un chiffre inexact, une date, une citation approximative, une position attribuée à la mauvaise personne.</li>
<li>Elle peut mal résumer une source, ou simplifier au point de perdre une nuance importante.</li>
<li>L'actualité bouge vite : un brief peut être dépassé quelques jours après sa publication.</li>
<li>L'équilibre entre « pour » et « contre » est un effort de présentation, pas une mesure objective de qui a raison.</li>
</ul>
</div>
<div class="side pro">
<h2>Le bon usage</h2>
<p class="who">Ce que Brief citoyen est, et n'est pas</p>
<ul>
<li>Un point de départ pour comprendre un sujet, pas une source de référence.</li>
<li>Les sources citées font foi : pour un chiffre ou une citation, c'est elles qu'il faut lire.</li>
<li>Il ne remplace pas le travail des journalistes, qui enquêtent, recoupent et vérifient.</li>
<li>Il ne donne pas de consigne de vote et ne défend aucun parti.</li>
</ul>
</div>
</section>

<section class="question">
<h2 class="kicker">Une erreur, un oubli ?</h2>
<p>Les signalements sont bienvenus : ils permettent de corriger le brief concerné.</p>
<a class="cta" href="https://github.com/marccharton/Brief-Citoyen/issues/new" target="_blank" rel="noopener">Signaler une erreur sur GitHub</a>
</section>

<p class="credit">Brief citoyen est un projet personnel de <a href="https://marccharton.github.io/">Marc Charton</a>, à Toulouse. Le code du site est public sur <a href="https://github.com/marccharton/Brief-Citoyen">GitHub</a>.</p>
</main>""")
    out.append(FOOT.format(prefix=prefix))
    return "\n".join(out)


def main():
    briefs = load()
    if not briefs:
        sys.exit("Aucun brief trouvé dans data/briefs/")
    keep = {b["id"] for b in briefs}
    for d in ROOT.iterdir():
        if d.is_dir() and ID_RE.match(d.name) and d.name not in keep:
            (d / "index.html").unlink(missing_ok=True)
            try:
                d.rmdir()
            except OSError:
                pass
    for i, b in enumerate(briefs):
        nxt = briefs[i - 1] if i > 0 else None
        prv = briefs[i + 1] if i + 1 < len(briefs) else None
        page = ROOT / b["id"] / "index.html"
        page.parent.mkdir(exist_ok=True)
        page.write_text(render_brief(b, prv, nxt), encoding="utf-8")
    (ROOT / "index.html").write_text(render_index(briefs), encoding="utf-8")
    (ROOT / "feed.xml").write_text(render_feed(briefs), encoding="utf-8")
    about = ROOT / "comment-c-est-fait" / "index.html"
    about.parent.mkdir(exist_ok=True)
    about.write_text(render_about(briefs), encoding="utf-8")
    print(f"{len(briefs)} briefs construits.")


if __name__ == "__main__":
    main()
