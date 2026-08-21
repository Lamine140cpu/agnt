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
import sys
import os
import re
import urllib.request

SITE = os.path.dirname(os.path.abspath(__file__))

# Un jeu de fontes par direction artistique. La vitrine et la première page
# client emploient « editorial » ; les deux refontes ont chacune le sien, parce
# qu'une direction artistique se joue d'abord dans le dessin des lettres — et
# qu'embarquer six familles pour n'en montrer que deux serait payer trois fois
# le même écran.
JEUX = {
    "editorial": ("ultra.css",
                  "?family=Instrument+Serif:ital@0;1"
                  "&family=IBM+Plex+Mono:wght@400;500"
                  "&family=IBM+Plex+Sans:wght@400;500"),
    # A — le tableau de bord : une grotesque à fort contraste de graisse pour
    # la structure, une mono pour tout ce qui est chiffré.
    "bord":      ("ultra-bord.css",
                  "?family=Archivo:wght@400;500;600;700"
                  "&family=IBM+Plex+Mono:wght@400;500"),
    # B — la signalisation : Anton pour les panneaux (condensée, très grasse,
    # c'est la parente directe des caractères de signalisation), Archivo pour
    # le texte courant, la mono pour les bornes.
    "signal":    ("ultra-signal.css",
                  "?family=Anton"
                  "&family=Archivo:wght@400;500;600"
                  "&family=IBM+Plex+Mono:wght@400;500"),
}

JEU = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("jeu=")), "editorial")
if JEU not in JEUX:
    raise SystemExit(f"jeu inconnu : {JEU} — au choix {', '.join(JEUX)}")

_fichier, _familles = JEUX[JEU]
DEMANDE = "https://fonts.googleapis.com/css2" + _familles + "&display=swap"
SORTIE = os.path.join(SITE, "assets", "fonts", _fichier)

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

    entete = (f"/* Fontes embarquées — jeu « {JEU} », SIL Open Font License 1.1.\n"
              "   Sous-ensembles latins uniquement. Produit par fontes_locales.py :\n"
              "   ne pas modifier à la main. */\n")
    os.makedirs(os.path.dirname(SORTIE), exist_ok=True)
    open(SORTIE, "w", encoding="utf-8").write(entete + "\n".join(sorties) + "\n")
    poids = os.path.getsize(SORTIE) / 1024
    print(f"\nécrit {SORTIE} — {poids:.0f} Ko "
          f"({total/1024:.0f} Ko de fontes, {len(sorties)} fontes)")


if __name__ == "__main__":
    main()
