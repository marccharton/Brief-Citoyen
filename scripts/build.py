#!/usr/bin/env python3
"""Construit le site Brief citoyen à partir de data/briefs/*.json.

Usage : python3 scripts/build.py
Produit : data/index.json (liste légère lue par index.html et brief/index.html),
feed.xml (flux RSS) et comment-c-est-fait/index.html.
Les pages index.html et brief/index.html sont des coquilles statiques écrites à la
main : elles chargent les JSON en JavaScript, build.py n'y touche pas.
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


def brief_url(bid):
    return f"{SITE_URL}brief/?id={bid}"


def render_index_json(briefs):
    """Liste légère, du plus récent au plus ancien, avec les libellés communs."""
    return json.dumps({
        "types": TYPES,
        "categories": [{"name": c, "desc": d} for c, d in CATEGORIES],
        "briefs": [{"id": b["id"], "date": b["date"], "title": b["title"], "subject": b.get("subject", ""),
                    "type": btype(b), "categories": bcats(b)} for b in briefs],
    }, ensure_ascii=False, indent=1) + "\n"


def render_feed(briefs):
    items = []
    for b in briefs[:30]:
        d = parse_date(b["date"]).replace(hour=7, minute=47, tzinfo=timezone.utc)
        items.append(f"""<item><title>{e(b['title'])}</title><link>{e(brief_url(b['id']))}</link>
<guid isPermaLink="true">{e(brief_url(b['id']))}</guid><pubDate>{format_datetime(d)}</pubDate>
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
    rows = "".join(f'<li><span class="h">{e(h)}</span><span class="c">{c} citation{"s" if c > 1 else ""}</span></li>'
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
<h3 class="hosts-t">Sites les plus cités, par nombre de citations</h3>
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
<li><strong>Choisir un sujet.</strong> Le lundi, le mercredi et le vendredi, un sujet d'actualité des derniers jours, choisi selon une <a href="#choix-du-sujet">règle de score publique</a>. Le mardi et le jeudi, un « Éclairage Institutions » qui explique une notion de base, dans l'ordre d'une progression fixe : la Constitution, le 49-3, le Sénat…</li>
<li><strong>Se documenter.</strong> L'IA fait des recherches sur le web en suivant les règles décrites plus bas : sources primaires d'abord, médias identifiés, plusieurs sensibilités. Pour le contexte général (comment fonctionne une institution, l'histoire d'une réforme), elle s'appuie aussi sur ses propres connaissances, apprises avant sa mise en service : ces phrases-là sont marquées « IA » dans le texte.</li>
<li><strong>Rédiger.</strong> Chaque phrase est reliée à la source dont elle vient. Les bases, les mots à connaître, ce qui se joue, les arguments pour et contre avec ceux qui les portent, un angle local sur Toulouse et l'Occitanie quand c'est pertinent, des sources pour creuser et une question ouverte.</li>
<li><strong>Contrôler la forme.</strong> Des vérifications automatiques portent sur le format, l'orthographe et le ton neutre. Elles ne vérifient pas les faits.</li>
<li><strong>Publier.</strong> Le brief arrive sur ce site dans la matinée, en général entre 8 h et 10 h, avec son propre lien et sa fiche technique, qui détaille comment le sujet a été choisi.</li>
</ol>
</section>

<section id="choix-du-sujet">
<h2 class="kicker">Comment le sujet est choisi</h2>
<div class="prose">
<p>Le choix du sujet est déjà une forme de biais : parler d'une chose, c'est ne pas parler d'une autre. Pour que ce choix ne soit pas une boîte noire, il suit une règle fixe, et chaque brief Actualité garde la trace de son application dans sa fiche technique.</p>
<p><strong>Repérage.</strong> L'IA lance toujours les mêmes recherches, avec la date du jour : l'actualité politique en France, l'Assemblée nationale et le Sénat cette semaine, les annonces du gouvernement, la politique à Toulouse et en Occitanie. Elle en retient 5 à 8 sujets candidats des 7 derniers jours, puis compte pour chacun les sources distinctes qui en parlent.</p>
<p><strong>Score.</strong> Chaque candidat est noté selon ces critères :</p>
</div>
<div class="scoregrid">
<div><strong>Couverture (0 à 3)</strong><span>Nombre de sources distinctes qui en parlent : 1 source donne 0, 2 ou 3 donnent 1, 4 ou 5 donnent 2, 6 et plus donnent 3.</span></div>
<div><strong>Variété des sources (0 à 2)</strong><span>Nombre de types de sources différents : officielles, agences, presse nationale ou régionale, médias publics, organisations.</span></div>
<div><strong>Couvert des deux côtés (0 ou 1)</strong><span>Un point si des sources perçues à gauche et à droite en parlent : un sujet porté par un seul bord marque moins.</span></div>
<div><strong>Fraîcheur (0 à 2)</strong><span>Fait nouveau depuis moins de 48 heures, ou dans la semaine.</span></div>
<div><strong>Impact concret (0 à 2)</strong><span>Effet direct sur l'argent, les services publics ou les droits. Ce critère reste un jugement de l'IA, expliqué en une phrase.</span></div>
<div><strong>Angle local (0 ou 1)</strong><span>Un effet identifiable à Toulouse ou en Occitanie.</span></div>
<div><strong>Répétition (0 ou −1)</strong><span>Un point de moins si la catégorie est celle du brief Actualité précédent, pour varier les domaines.</span></div>
</div>
<div class="prose">
<p><strong>Délai.</strong> Un sujet déjà traité dans les 14 derniers jours est écarté, sauf rebondissement majeur (un vote, une décision de justice, une décision officielle, un chiffre officiel nouveau), nommé dans la fiche.</p>
<p><strong>Décision.</strong> Le meilleur total l'emporte ; en cas d'égalité, la meilleure couverture, puis la meilleure fraîcheur. Ce score ne mesure pas l'importance réelle d'un sujet : il rend le choix explicable et comparable d'un jour à l'autre. Comme les sources elles-mêmes, il hérite de ce dont les médias parlent.</p>
</div>
</section>

<section>
<h2 class="kicker">Chaque phrase reliée à sa source</h2>
<div class="prose">
<p>Depuis le 17 novembre 2026, chaque phrase d'un brief est reliée à la source dont elle vient. Le bouton « Voir la source de chaque phrase » colore le texte : une couleur et un numéro par source, qui renvoient à la liste des sources utilisées en fin de brief, avec un court extrait et un lien qui ouvre la page au passage cité (selon le navigateur).</p>
<p>Les phrases qui viennent des connaissances générales de l'IA (contexte, définitions, transitions) sont soulignées en pointillés et marquées « IA ». Mieux vaut l'afficher que d'attribuer une phrase à tort à une source. La fiche technique indique la part du texte reliée à une source.</p>
<p>Ce marquage est fait par l'IA elle-même et n'est pas encore vérifié automatiquement : un repère peut être inexact. En cas de doute, la source fait foi.</p>
</div>
</section>

<section class="box stakes">
<h2 class="kicker">Ce qu'on demande à l'IA, en toutes lettres</h2>
<p>Un modèle d'IA apprend à partir d'énormes quantités de textes, choisis et pondérés par l'entreprise qui le développe. Ce qu'il en garde, ses tendances et ses angles morts, ne peut pas être vérifié de l'extérieur. C'est une limite réelle, et elle ne disparaît pas.</p>
<p>Ce qui peut être montré, c'est ce qu'on lui demande. Les consignes que l'IA reçoit chaque matin (le ton, le choix du sujet, le choix des sources, la façon de relier chaque phrase à sa source) sont publiées mot pour mot. Chacun peut vérifier qu'aucune consigne ne pousse vers un point de vue. Chaque modification change leur numéro de version, l'historique est public, et la fiche technique de chaque brief indique la version utilisée.</p>
<a class="cta" href="https://github.com/marccharton/Brief-Citoyen/blob/main/methode/consignes.md" target="_blank" rel="noopener">Lire les consignes données à l'IA</a>
</section>

<section class="postulat">
<h2 class="kicker">Le postulat de ce projet</h2>
<div class="prose">
<p>Toute information passe par des filtres avant de nous arriver. Les médias ont une ligne éditoriale, des contraintes de temps, parfois des intérêts : même avec une réelle volonté d'impartialité, chaque rédaction choisit ses sujets, ses mots et ses angles, et commet aussi des erreurs. Quand on s'informe soi-même en lisant plusieurs articles, notre mémoire, notre compréhension et nos propres opinions ajoutent encore leurs approximations.</p>
<p>Mon postulat, qui reste une opinion et peut être faux : dans cette chaîne, la reformulation par une IA qui reste très proche des sources qu'elle lit n'est pas le maillon le plus biaisé. L'essentiel des biais vient en amont, des sources elles-mêmes et du choix de ce dont on parle.</p>
<p>Ce postulat ne dispense pas de prudence. L'IA ajoute ses propres risques : se tromper d'attribution, omettre une information, cadrer un sujet par l'ordre ou les mots qu'elle choisit, présenter à égalité des positions qui ne le sont pas. Plutôt que de demander de la confiance, ce projet cherche à rendre son fonctionnement vérifiable : une règle de choix du sujet publique, une fiche technique par brief, chaque phrase reliée à sa source ou marquée comme rédigée par l'IA, et les consignes publiées mot pour mot.</p>
<p class="sig">Marc Charton, auteur du projet</p>
</div>
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
<li>Ce qu'un brief ne dit pas ne laisse pas de trace : le choix des informations retenues et leur ordre orientent aussi la lecture.</li>
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
    # Anciennes pages générées (<id>/index.html à la racine) : remplacées par brief/?id=<id>.
    for d in ROOT.iterdir():
        if d.is_dir() and ID_RE.match(d.name):
            (d / "index.html").unlink(missing_ok=True)
            try:
                d.rmdir()
            except OSError:
                pass
    (ROOT / "data" / "index.json").write_text(render_index_json(briefs), encoding="utf-8")
    (ROOT / "feed.xml").write_text(render_feed(briefs), encoding="utf-8")
    about = ROOT / "comment-c-est-fait" / "index.html"
    about.parent.mkdir(exist_ok=True)
    about.write_text(render_about(briefs), encoding="utf-8")
    print(f"{len(briefs)} briefs indexés.")


if __name__ == "__main__":
    main()
