#!/usr/bin/env python3
"""
Rapatrie les fontes Google et les fige en un seul fichier CSS local.

Pourquoi ne pas simplement garder le <link> vers fonts.googleapis.com :

  — une page qui dépend d'un hôte extérieur ne s'affiche pas comme prévu
    quand cet hôte est lent, bloqué ou inaccessible, et la substitution est
    silencieuse : on croit voir sa maquette, on voit sa police de secours ;
  — c'est une requête vers un tiers sur chaque visite, ce dont on peut se
    passer et qu'on préfère ne pas avoir à déclarer ;
  — et le fichier livré cesse d'être autonome, ce qui est tout l'intérêt.

Seul le sous-ensemble latin est gardé. Le fichier d'origine décrit aussi le
latin étendu, le cyrillique, le grec et le vietnamien — inutiles en français,
et ils quadrupleraient le poids.

Les deux familles employées sont sous licence libre (SIL Open Font License),
qui autorise explicitement la redistribution, y compris embarquée.

    usage : python3 fontes_locales.py
"""
import base64
import os
import re
import urllib.request

SITE = os.path.dirname(os.path.abspath(__file__))
SORTIE = os.path.join(SITE, "assets", "fonts", "ultra.css")

DEMANDE = ("https://fonts.googleapis.com/css2"
           "?family=Instrument+Serif:ital@0;1"
           "&family=IBM+Plex+Mono:wght@400;500"
           "&family=IBM+Plex+Sans:wght@400;500"
           "&display=swap")

# Sans en-tête moderne, Google renvoie du TrueType au lieu du WOFF2 — trois
# fois plus lourd, pour le même dessin.
NAVIGATEUR = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

# Le latin seul suffit au français : la plage Google « latin » contient déjà
# les accents et la ligature œ (U+0152-0153). Le latin étendu sert aux langues
# d'Europe centrale et coûtait 110 Ko pour rien.
GARDES = ("latin",)


def lire(url):
    req = urllib.request.Request(url, headers={"User-Agent": NAVIGATEUR})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def main():
    css = lire(DEMANDE).decode("utf-8")

    # Le fichier est une suite de « /* sous-ensemble */ @font-face {...} ».
    blocs = re.findall(r"/\*\s*([\w-]+)\s*\*/\s*(@font-face\s*\{.*?\})", css, re.S)
    if not blocs:
        raise SystemExit("format inattendu : aucun bloc @font-face reconnu")

    sorties, total = [], 0
    for sousensemble, bloc in blocs:
        if sousensemble not in GARDES:
            continue
        url = re.search(r"url\((https://[^)]+\.woff2)\)", bloc)
        if not url:
            continue
        octets = lire(url.group(1))
        total += len(octets)
        famille = re.search(r"font-family:\s*'([^']+)'", bloc).group(1)
        graisse = re.search(r"font-weight:\s*(\d+)", bloc)
        style = re.search(r"font-style:\s*(\w+)", bloc)
        print(f"  {famille:18s} {graisse.group(1) if graisse else '?':>3s} "
              f"{style.group(1) if style else '':8s} {sousensemble:10s} "
              f"{len(octets)/1024:6.1f} Ko")
        sorties.append(bloc.replace(
            url.group(0),
            "url(data:font/woff2;base64," + base64.b64encode(octets).decode() + ")"))

    entete = ("/* Fontes embarquées — Instrument Serif et IBM Plex, SIL Open Font\n"
              "   License 1.1. Sous-ensembles latins uniquement. Fichier produit par\n"
              "   fontes_locales.py : ne pas le modifier à la main. */\n")
    os.makedirs(os.path.dirname(SORTIE), exist_ok=True)
    open(SORTIE, "w", encoding="utf-8").write(entete + "\n".join(sorties) + "\n")
    poids = os.path.getsize(SORTIE) / 1024
    print(f"\nécrit {SORTIE} — {poids:.0f} Ko "
          f"({total/1024:.0f} Ko de fontes, {len(sorties)} fontes)")


if __name__ == "__main__":
    main()
