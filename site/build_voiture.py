#!/usr/bin/env python3
"""
Replie la page de location en un seul fichier.

Le modèle arrive déjà en GLB — tout est dans un bloc, rien à assembler. Mais
onze mégaoctets deviennent quinze une fois encodés en base64, et la page
dépasserait la limite d'un artefact.

Les textures n'y sont pourtant que pour 2,8 Mo : le reste est de la géométrie,
et sans décodeur Draco on ne peut pas la compresser sans embarquer un module
WebAssembly. On travaille donc sur ce qui se laisse faire — les images, toutes
livrées en PNG, format sans perte fait pour les captures d'écran et non pour
des cartes de matière. En JPEG à qualité 88, elles tombent à un cinquième.

Une exception : les images à canal alpha restent en PNG. Le JPEG n'a pas
d'alpha, et l'écraser transformerait un masque de découpe en aplat opaque.
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
from build_appareil import envelopper                  # noqa: E402

SITE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(SITE, "dist", "voiture.html")
GLB = os.path.join(SITE, "assets", "vehicule", "CarConcept.glb")
ENV = os.path.join(SITE, "assets", "studio", "hall-equirect.jpg")

COTE = 1024        # côté maximal d'une carte
QUALITE = 88


def cale(n, sur=4):
    """glTF exige des blocs alignés sur quatre octets."""
    return (sur - n % sur) % sur


def alleger(glb):
    """Réencode les images d'un GLB, et le réécrit."""
    jl = struct.unpack("<I", glb[12:16])[0]
    g = json.loads(glb[20:20 + jl])
    binaire = glb[20 + jl + 8:]

    vues = g["bufferViews"]
    images = {im["bufferView"]: i for i, im in enumerate(g.get("images", []))}

    # On reconstruit le tampon en gardant l'ordre : les vues non-image sont
    # recopiées telles quelles, les images sont remplacées par leur version
    # réencodée. Les décalages changent, donc toutes les vues sont réécrites.
    morceaux, total = [], 0
    avant = apres = 0

    def poser(octets):
        nonlocal total
        debut = total
        morceaux.append(octets)
        bourrage = cale(len(octets))
        if bourrage:
            morceaux.append(b"\0" * bourrage)
        total += len(octets) + bourrage
        return debut

    for i, vue in enumerate(vues):
        o = vue.get("byteOffset", 0)
        brut = binaire[o:o + vue["byteLength"]]
        if i in images:
            avant += len(brut)
            im = Image.open(io.BytesIO(brut))
            if max(im.size) > COTE:
                k = COTE / max(im.size)
                im = im.resize((max(1, round(im.width * k)), max(1, round(im.height * k))),
                               Image.LANCZOS)
            tampon = io.BytesIO()
            # L'alpha n'existe pas en JPEG : les masques restent en PNG.
            if im.mode in ("RGBA", "LA") and im.getchannel("A").getextrema()[0] < 255:
                im.save(tampon, "PNG", optimize=True)
                mime = "image/png"
            else:
                im.convert("RGB").save(tampon, "JPEG", quality=QUALITE, optimize=True)
                mime = "image/jpeg"
            brut = tampon.getvalue()
            apres += len(brut)
            g["images"][images[i]]["mimeType"] = mime
        vue["byteOffset"] = poser(brut)
        vue["byteLength"] = len(brut)
        vue.pop("byteStride", None) if i in images else None

    corps = b"".join(morceaux)
    g["buffers"] = [{"byteLength": len(corps)}]
    js = json.dumps(g, separators=(",", ":")).encode("utf-8")
    js += b" " * cale(len(js))

    entete = struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(corps))
    print(f"  images {avant/1048576:.2f} Mo -> {apres/1048576:.2f} Mo")
    return (entete
            + struct.pack("<II", len(js), 0x4E4F534A) + js
            + struct.pack("<II", len(corps), 0x004E4942) + corps)


def main():
    os.chdir(SITE)
    src = open("voiture.html", encoding="utf-8").read()

    glb = alleger(open(GLB, "rb").read())
    b64 = base64.b64encode(glb).decode()
    print(f"  GLB {os.path.getsize(GLB)/1048576:.2f} Mo -> {len(glb)/1048576:.2f} Mo "
          f"-> base64 {len(b64)/1048576:.2f} Mo")

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

    page = page.replace(
        "  const gltf = await new Promise((res, rej) =>\n"
        "    chargeur.load('assets/vehicule/CarConcept.glb', res, undefined, rej));",
        "  const __b = atob(MODELE_B64), __u = new Uint8Array(__b.length);\n"
        "  for (let i = 0; i < __b.length; i++) __u[i] = __b.charCodeAt(i);\n"
        "  const gltf = await new Promise((res, rej) =>\n"
        "    chargeur.parse(__u.buffer, '', res, rej));")
    # La panoramique passe en URL data:. Une balise <img> l'accepte — c'est
    # fetch() qu'une politique stricte refuse, pas le chargement d'une image.
    env64 = base64.b64encode(open(ENV, "rb").read()).decode()
    # L'ordre compte : const n'est pas hissé, et déclarer la chaîne après son
    # usage donnait « Cannot access ENV_B64 before initialization ».
    page = page.replace("const ENV_STUDIO = 'assets/studio/hall-equirect.jpg';",
                        "const ENV_B64 = " + json.dumps(env64) + ";\n"
                        "const ENV_STUDIO = 'data:image/jpeg;base64,' + ENV_B64;")
    print(f"  panoramique {len(env64)/1024:.0f} Ko en base64")

    page = page.replace("const chargeur = new GLTFLoader();",
                        "const MODELE_B64 = " + json.dumps(b64) + ";\n"
                        "  const chargeur = new GLTFLoader();", 1)

    page = page.replace("import * as THREE from './vendor/three.module.min.js';", trois)
    page = page.replace("import { GLTFLoader } from './vendor/GLTFLoader.js';", corps)

    for ligne in page.splitlines():
        if "assets/" in ligne and "//" not in ligne and "*" not in ligne:
            sys.exit(f"référence externe restante : {ligne.strip()[:90]}")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w", encoding="utf-8").write(page)
    print(f"\nécrit {OUT} — {len(page)/1048576:.2f} Mo")


if __name__ == "__main__":
    main()
