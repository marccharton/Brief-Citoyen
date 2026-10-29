#!/usr/bin/env python3
"""Récupère les briefs depuis Supabase et les écrit dans data/briefs/.

Supabase est la source de vérité : ce script crée ou met à jour un fichier
<id>.json par ligne de la table public.briefs, et supprime les fichiers locaux
qui n'existent plus en base. Python standard, sans dépendance.

Variables d'environnement :
  SUPABASE_URL   URL du projet, par exemple https://xxxx.supabase.co
  SUPABASE_KEY   clé publique (publishable) : la table est en lecture publique
"""
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "briefs"
ID_RE = re.compile(r"^\d{4}-\d{2}-\d{2}(-[a-z0-9]+)?$")
PAGE = 500


def fetch(url, key):
    rows, offset = [], 0
    while True:
        req = urllib.request.Request(
            f"{url}/rest/v1/briefs?select=id,data&order=id.asc&limit={PAGE}&offset={offset}",
            headers={"apikey": key, "Accept": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            page = json.loads(r.read().decode("utf-8"))
        rows.extend(page)
        if len(page) < PAGE:
            return rows
        offset += PAGE


def main():
    url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    key = os.environ.get("SUPABASE_KEY", "")
    if not url or not key:
        sys.exit("SUPABASE_URL et SUPABASE_KEY doivent être définies.")

    rows = fetch(url, key)
    if not rows:
        # Par prudence, on ne vide jamais le site sur une réponse vide.
        sys.exit("Aucun brief reçu de Supabase : rien n'est modifié.")

    DATA.mkdir(parents=True, exist_ok=True)
    seen, written = set(), 0
    for row in rows:
        bid, data = row.get("id", ""), row.get("data")
        if not ID_RE.match(bid) or not isinstance(data, dict):
            print(f"ignoré (ligne invalide) : {bid!r}", file=sys.stderr)
            continue
        data.pop("site", None)  # champ propre à l'artefact de secours
        seen.add(bid)
        path = DATA / f"{bid}.json"
        text = json.dumps(data, ensure_ascii=False, indent=1) + "\n"
        if not path.exists() or path.read_text(encoding="utf-8") != text:
            path.write_text(text, encoding="utf-8")
            written += 1

    removed = 0
    for f in DATA.glob("*.json"):
        if f.stem not in seen:
            f.unlink()
            removed += 1

    print(f"{len(seen)} briefs en base, {written} écrits ou mis à jour, {removed} supprimés.")


if __name__ == "__main__":
    main()
