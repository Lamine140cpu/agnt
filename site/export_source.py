#!/usr/bin/env python3
"""
Produit une copie de la page destinée à être lue — par un humain ou par un
autre modèle — plutôt qu'exécutée.

La version d'un seul fichier que produit build_artifact.py pèse plus de huit
mégaoctets : three.js minifié et les textures en base64. C'est parfait pour un
navigateur et inutilisable pour une lecture. Cette variante-ci fait l'inverse :
elle replie la configuration dans la page, laisse les images et la lib en
références externes, et fait précéder le tout du dossier du projet.

    usage : python3 export_source.py [page.html]
"""
import os
import re
import sys

SITE = os.path.dirname(os.path.abspath(__file__))
PAGE = sys.argv[1] if len(sys.argv) > 1 else "index.html"
OUT = os.path.join(SITE, "dist", "source-" + PAGE)
DOSSIER = os.path.join(SITE, "DOSSIER.md")


def main():
    os.chdir(SITE)
    page = open(PAGE, encoding="utf-8").read()

    config = open("site.config.js", encoding="utf-8").read()
    config = re.sub(r"\bexport\s+const\s+CONFIG", "const CONFIG", config)
    page = page.replace("import { CONFIG } from './site.config.js';", config)

    dossier = open(DOSSIER, encoding="utf-8").read()
    # Un commentaire HTML ne supporte pas la suite « -- » : on la neutralise.
    entete = "<!--\n" + dossier.replace("--", "––") + "\n-->\n"

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(entete + page)
    print(f"écrit {OUT} — {os.path.getsize(OUT)/1024:.0f} Ko")


if __name__ == "__main__":
    main()
