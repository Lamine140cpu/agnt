#!/usr/bin/env python3
"""
Replie la visionneuse de pièce en un seul fichier, pour publication.

Même principe que build_artifact.py — three.js enveloppé dans une IIFE, puisque
la CSP d'un Artifact refuse aussi bien un hôte externe qu'un `import` depuis une
URL data:. S'y ajoutent splat.js, dont les `export` deviennent des déclarations
locales, et la scène elle-même en base64.
"""
import base64, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_artifact import wrap_core, wrap_module      # noqa: E402

SITE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(SITE, "dist", "piece.html")


def main():
    os.chdir(SITE)
    b64 = lambda p: base64.b64encode(open(p, "rb").read()).decode()

    trois = (
        "/* three.js r185 — replié en place : voir build_artifact.py */\n"
        "const __threeCore = " + wrap_core(open("vendor/three.core.min.js").read()) + ";\n"
        "const THREE = " + wrap_module(open("vendor/three.module.min.js").read(), "__threeCore") + ";\n"
    )

    # splat.js : les exports deviennent de simples déclarations
    splat = open("splat.js").read()
    splat = re.sub(r"^export\s+(async\s+)?function", r"\1function", splat, flags=re.M)
    splat = re.sub(r"^export\s+", "", splat, flags=re.M)

    src = open("piece.html").read()
    head = src.split("<head>", 1)[1].split("</head>", 1)[0]
    body = src.split("<body>", 1)[1].rsplit("</body>", 1)[0]
    head = re.sub(r'<meta charset[^>]*>\s*', "", head)
    head = re.sub(r'<meta name="viewport"[^>]*>\s*', "", head)
    page = head.strip() + "\n" + body.strip() + "\n"

    page = page.replace("import * as THREE from './vendor/three.module.min.js';", trois)
    page = page.replace(
        "import { chargerSplat, nuage, reglerQuaternion } from './splat.js';", splat)

    scene = "data:application/octet-stream;base64," + b64("assets/splats/piece.ums")
    page = page.replace("window.PIECE_URL || 'assets/splats/piece.ums'", "SCENE_B64")
    page = page.replace("const canvas = document.getElementById('c');",
                        "const SCENE_B64 = '" + scene + "';\nconst canvas = document.getElementById('c');", 1)

    for reste in ("'./vendor/", "'assets/", '"assets/'):
        if reste in page:
            sys.exit(f"référence externe restante : {reste}")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w", encoding="utf-8").write(page)
    print(f"écrit {OUT} — {len(page)/1048576:.2f} Mo")


if __name__ == "__main__":
    main()
