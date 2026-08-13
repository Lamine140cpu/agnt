#!/usr/bin/env python3
"""
Replie la page de l'appareil en un seul fichier.

Même contrainte que le salon meublé : une politique de sécurité stricte refuse
fetch(), y compris vers une URL data:. Le glTF — un JSON, un .bin et neuf
textures — devient donc un **GLB**, le format binaire où tout tient dans un
seul bloc, et ce bloc se passe directement à GLTFLoader.parse().

Les textures sont ramenées à 1024 px : c'est un objet qu'on regarde de près,
contrairement au mobilier vu à deux mètres, mais 4k par carte pour une page
web ne se justifie nulle part.
"""
import base64
import io
import json
import os
import re
import struct
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_artifact import wrap_core, wrap_module      # noqa: E402
from build_appartement import cale, en_glb             # noqa: E402
import build_appartement                               # noqa: E402

SITE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(SITE, "dist", "appareil.html")
MODELE = os.path.join(SITE, "assets", "mobilier", "Camera_01")

# l'appareil est vu de très près : on garde plus de définition que le mobilier
build_appartement.COTE = 1024
build_appartement.QUALITE = 86


def envelopper(chemin, var, locaux):
    """Un module ES ramené à une IIFE qui rend ses exportations.

    Les envelopper une à une est indispensable : BufferGeometryUtils et
    GLTFLoader déclarent tous deux toTrianglesDrawMode, et les mettre côte à
    côte dans la même portée redéclarerait la même fonction.
    """
    s = open(chemin, encoding="utf-8").read()
    entetes = []

    def import_vers_const(m):
        propre = " ".join(m.group(1).split())
        source = m.group(2)
        if "three.module" in source:
            entetes.append(f"const {{{propre}}} = THREE;")
        else:
            entetes.append(f"const {{{propre}}} = {locaux[os.path.basename(source)]};")
        return ""

    s = re.sub(r"^import\s*\{([^}]*)\}\s*from\s*'([^']*)';",
               import_vers_const, s, flags=re.M)

    sorties = []
    for bloc in re.findall(r"^export\s*\{([^}]*)\};?", s, flags=re.M):
        sorties += [n.strip() for n in bloc.split(",") if n.strip()]
    s = re.sub(r"^export\s*\{[^}]*\};?", "", s, flags=re.M)
    s = re.sub(r"^export\s+(?=(function|class|const|let|var)\b)", "", s, flags=re.M)

    return (f"const {var} = (function(){{\n" + "\n".join(entetes) + "\n"
            + s + "\nreturn {" + ", ".join(sorties) + "};\n}})();\n").replace("}})();", "})();")


def main():
    os.chdir(SITE)
    src = open("appareil.html", encoding="utf-8").read()

    glb = en_glb(MODELE, "Camera_01")
    b64 = base64.b64encode(glb).decode()
    print(f"  Camera_01 → GLB {len(glb)/1024:7.0f} Ko")

    trois = (
        "/* three.js r185 — replié en place : voir build_artifact.py */\n"
        "const __threeCore = " + wrap_core(open("vendor/three.core.min.js").read()) + ";\n"
        "const THREE = " + wrap_module(open("vendor/three.module.min.js").read(), "__threeCore") + ";\n"
    )
    locaux = {"BufferGeometryUtils.js": "__bgu", "SkeletonUtils.js": "__sku"}
    corps = (envelopper("vendor/BufferGeometryUtils.js", "__bgu", locaux)
             + envelopper("vendor/SkeletonUtils.js", "__sku", locaux)
             + envelopper("vendor/GLTFLoader.js", "__gltf", locaux)
             + "const GLTFLoader = __gltf.GLTFLoader;\n")

    head = src.split("<head>", 1)[1].split("</head>", 1)[0]
    body = src.split("<body>", 1)[1].rsplit("</body>", 1)[0]
    head = re.sub(r'<meta charset[^>]*>\s*', "", head)
    head = re.sub(r'<meta name="viewport"[^>]*>\s*', "", head)
    page = head.strip() + "\n" + body.strip() + "\n"

    # parse() plutôt que load() : la scène est déjà là, en binaire
    page = page.replace(
        "  const gltf = await new Promise((res, rej) =>\n"
        "    chargeur.load('assets/mobilier/Camera_01/Camera_01.gltf', res, undefined, rej));",
        "  const __b = atob(MODELE_B64), __u = new Uint8Array(__b.length);\n"
        "  for (let i = 0; i < __b.length; i++) __u[i] = __b.charCodeAt(i);\n"
        "  const gltf = await new Promise((res, rej) =>\n"
        "    chargeur.parse(__u.buffer, '', res, rej));")
    page = page.replace("const chargeur = new GLTFLoader();",
                        "const MODELE_B64 = " + json.dumps(b64) + ";\n"
                        "  const chargeur = new GLTFLoader();", 1)

    page = page.replace("import * as THREE from './vendor/three.module.min.js';", trois)
    page = page.replace("import { GLTFLoader } from './vendor/GLTFLoader.js';", corps)

    # La vérification porte sur notre code : les bibliothèques vendorisées citent
    # des chemins d'exemple dans leurs commentaires.
    for ligne in page.splitlines():
        if "assets/" in ligne and "//" not in ligne and "*" not in ligne:
            sys.exit(f"référence externe restante : {ligne.strip()[:90]}")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w", encoding="utf-8").write(page)
    print(f"\nécrit {OUT} — {len(page)/1048576:.2f} Mo")


if __name__ == "__main__":
    main()
