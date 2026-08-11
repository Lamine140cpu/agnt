#!/usr/bin/env python3
"""
Replie le flacon en un seul fichier.

Le plus simple des trois : rien à embarquer. Le studio est dessiné dans un
canvas, l'objet est un profil de vingt nombres, la gravure est tracée au code.
Seul three.js a besoin d'être replié.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_artifact import wrap_core, wrap_module      # noqa: E402

SITE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(SITE, "dist", "flacon.html")


def main():
    os.chdir(SITE)
    src = open("flacon.html", encoding="utf-8").read()

    trois = (
        "/* three.js r185 — replié en place : voir build_artifact.py */\n"
        "const __threeCore = " + wrap_core(open("vendor/three.core.min.js").read()) + ";\n"
        "const THREE = " + wrap_module(open("vendor/three.module.min.js").read(), "__threeCore") + ";\n"
    )

    head = src.split("<head>", 1)[1].split("</head>", 1)[0]
    body = src.split("<body>", 1)[1].rsplit("</body>", 1)[0]
    head = re.sub(r'<meta charset[^>]*>\s*', "", head)
    head = re.sub(r'<meta name="viewport"[^>]*>\s*', "", head)
    page = head.strip() + "\n" + body.strip() + "\n"
    page = page.replace("import * as THREE from './vendor/three.module.min.js';", trois)

    for reste in ("vendor/", "assets/"):
        if reste in page:
            sys.exit(f"référence externe restante : {reste}")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w", encoding="utf-8").write(page)
    print(f"écrit {OUT} — {len(page)/1024:.0f} Ko")


if __name__ == "__main__":
    main()
