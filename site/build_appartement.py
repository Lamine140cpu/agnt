#!/usr/bin/env python3
"""
Replie le salon meublé en un seul fichier.

Le mobilier arrive en glTF : un JSON, un .bin et des textures, soit une
quinzaine de fichiers par meuble. Une page autonome ne peut rien en faire — et
surtout, une politique de sécurité stricte refuse fetch(), y compris sur une
URL data:, ce qui exclut d'embarquer le glTF tel quel.

D'où la conversion en **GLB** : le format binaire de glTF, où le JSON, la
géométrie et les images tiennent dans un seul bloc. Ce bloc se passe
directement à GLTFLoader.parse(), sans la moindre requête.

Les textures sont au passage ramenées à 512 px : elles habillent des objets
vus à deux mètres, et 4 Mo de feuillage pour une plante en pot ne se justifient
nulle part.
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

SITE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(SITE, "dist", "appartement.html")
MOBILIER = os.path.join(SITE, "assets", "mobilier")

COTE = 512          # côté maximal d'une texture embarquée
QUALITE = 82


def cale(n, sur=4):
    """glTF exige des blocs alignés sur quatre octets."""
    return (sur - n % sur) % sur


def image_compacte(chemin):
    im = Image.open(chemin)
    if max(im.size) > COTE:
        k = COTE / max(im.size)
        im = im.resize((max(1, round(im.width * k)), max(1, round(im.height * k))),
                       Image.LANCZOS)
    tampon = io.BytesIO()
    im.convert("RGB").save(tampon, "JPEG", quality=QUALITE, optimize=True)
    return tampon.getvalue()


def en_glb(dossier, nom):
    """glTF + .bin + textures -> un seul GLB."""
    g = json.load(open(os.path.join(dossier, f"{nom}.gltf"), encoding="utf-8"))

    morceaux, total = [], 0

    def ajouter(octets):
        nonlocal total
        debut = total
        morceaux.append(octets)
        bourrage = cale(len(octets))
        if bourrage:
            morceaux.append(b"\0" * bourrage)
        total += len(octets) + bourrage
        return debut, len(octets)

    # le tampon de géométrie d'abord, les vues existantes y pointent déjà
    tampon = open(os.path.join(dossier, g["buffers"][0]["uri"]), "rb").read()
    base, _ = ajouter(tampon)
    for vue in g.get("bufferViews", []):
        vue["byteOffset"] = vue.get("byteOffset", 0) + base

    # puis chaque image, qui devient une vue de plus
    for img in g.get("images", []):
        uri = img.pop("uri")
        octets = image_compacte(os.path.join(dossier, uri))
        debut, longueur = ajouter(octets)
        g["bufferViews"].append({"buffer": 0, "byteOffset": debut, "byteLength": longueur})
        img["bufferView"] = len(g["bufferViews"]) - 1
        img["mimeType"] = "image/jpeg"

    binaire = b"".join(morceaux)
    g["buffers"] = [{"byteLength": len(binaire)}]

    js = json.dumps(g, separators=(",", ":")).encode("utf-8")
    js += b" " * cale(len(js))

    entete = struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(binaire))
    return (entete
            + struct.pack("<II", len(js), 0x4E4F534A) + js
            + struct.pack("<II", len(binaire), 0x004E4942) + binaire)


def main():
    os.chdir(SITE)
    src = open("appartement.html", encoding="utf-8").read()

    noms = re.findall(r"nom: '([\w]+)'", src)
    meubles = {}
    for nom in dict.fromkeys(noms):
        dossier = os.path.join(MOBILIER, nom)
        if not os.path.isdir(dossier):
            sys.exit(f"meuble absent : {nom}")
        glb = en_glb(dossier, nom)
        meubles[nom] = base64.b64encode(glb).decode()
        print(f"  {nom:<26} {len(glb)/1024:7.0f} Ko")

    trois = (
        "/* three.js r185 — replié en place : voir build_artifact.py */\n"
        "const __threeCore = " + wrap_core(open("vendor/three.core.min.js").read()) + ";\n"
        "const THREE = " + wrap_module(open("vendor/three.module.min.js").read(), "__threeCore") + ";\n"
    )

    def envelopper(chemin, var, locaux):
        """Un module ES ramené à une IIFE qui rend ses exportations.

        Les envelopper une à une est indispensable : BufferGeometryUtils et
        GLTFLoader déclarent tous deux toTrianglesDrawMode, et les mettre côte à
        côte dans la même portée redéclare la même fonction. Chacun garde donc
        la sienne, et ne voit des autres que ce qu'ils exportent.
        """
        s = open(chemin, encoding="utf-8").read()
        entetes = []

        def import_vers_const(m):
            noms, source = m.group(1), m.group(2)
            propre = " ".join(noms.split())
            if "three.module" in source:
                entetes.append(f"const {{{propre}}} = THREE;")
            else:
                base = os.path.basename(source)
                entetes.append(f"const {{{propre}}} = {locaux[base]};")
            return ""

        s = re.sub(r"^import\s*\{([^}]*)\}\s*from\s*'([^']*)';",
                   import_vers_const, s, flags=re.M)

        sorties = []
        for bloc in re.findall(r"^export\s*\{([^}]*)\};?", s, flags=re.M):
            sorties += [n.strip() for n in bloc.split(",") if n.strip()]
        s = re.sub(r"^export\s*\{[^}]*\};?", "", s, flags=re.M)
        s = re.sub(r"^export\s+(?=(function|class|const|let|var)\b)", "", s, flags=re.M)

        return (f"const {var} = (function(){{\n" + "\n".join(entetes) + "\n"
                + s + "\nreturn {" + ", ".join(sorties) + "};\n})();\n")

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

    # le parquet, seule texture de la coque
    parquet = base64.b64encode(image_compacte("assets/web/bois-parquet.jpg")).decode()
    page = page.replace("im.src = `assets/web/${fichier}.jpg`;",
                        "im.src = 'data:image/jpeg;base64,' + PARQUET_B64;")
    page = page.replace(
        "const charger = (nom) => new Promise((res, rej) =>\n"
        "  chargeur.load(`assets/mobilier/${nom}/${nom}.gltf`, res, undefined, rej));",
        "/* parse() plutôt que load() : la scène est déjà là, en binaire, et une\n"
        "   politique stricte refuserait la requête même vers une URL data:. */\n"
        "const charger = (nom) => new Promise((res, rej) => {\n"
        "  const b = atob(MEUBLES_B64[nom]), u = new Uint8Array(b.length);\n"
        "  for (let i = 0; i < b.length; i++) u[i] = b.charCodeAt(i);\n"
        "  chargeur.parse(u.buffer, '', res, rej);\n"
        "});")

    # La vérification porte sur notre code seul : les bibliothèques vendorisées
    # citent des chemins d'exemple dans leurs commentaires, et les signaler
    # reviendrait à crier au loup à chaque construction.
    temoin = page
    for ligne_import in ("import * as THREE from './vendor/three.module.min.js';",
                         "import { GLTFLoader } from './vendor/GLTFLoader.js';"):
        temoin = temoin.replace(ligne_import, "")   # remplacées juste après
    for reste in ("vendor/", "assets/"):
        if reste in temoin:
            ligne = next(l for l in temoin.splitlines() if reste in l)
            sys.exit(f"référence externe restante : {ligne.strip()[:90]}")

    page = page.replace("const chargeur = new GLTFLoader();",
                        "const MEUBLES_B64 = " + json.dumps(meubles) + ";\n"
                        "const chargeur = new GLTFLoader();", 1)
    page = page.replace("const canvas = document.getElementById('c');",
                        "const PARQUET_B64 = '" + parquet + "';\n"
                        "const canvas = document.getElementById('c');", 1)

    page = page.replace("import * as THREE from './vendor/three.module.min.js';", trois)
    page = page.replace("import { GLTFLoader } from './vendor/GLTFLoader.js';", corps)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w", encoding="utf-8").write(page)
    print(f"\nécrit {OUT} — {len(page)/1048576:.2f} Mo")


if __name__ == "__main__":
    main()
