#!/usr/bin/env python3
"""
Télécharge du mobilier depuis Poly Haven.

Un architecte ne modélise pas ses chaises : il meuble une pièce vide avec des
modèles existants. C'est tout le métier de l'image d'architecture, et c'est ce
qui manquait à notre appartement — un canapé fabriqué à la main avec des boîtes
arrondies se lit comme un dessin, quelle que soit la lumière qu'on lui donne.

Poly Haven publie 521 modèles en CC0 : domaine public, usage commercial libre,
aucune attribution obligatoire. Les auteurs sont tout de même consignés dans
CREDITS.md — ils ont fait le travail.

    usage : python3 mobilier.py [nom …]        (défaut : le salon complet)
"""
import json
import os
import sys
import urllib.request

# Le CDN de Poly Haven refuse l'agent par défaut de Python — 403 sec, sans
# explication. Se nommer suffit.
ENTETE = {"User-Agent": "Ultra Motion (site de démonstration)"}


def ouvrir(url, secondes=120):
    return urllib.request.urlopen(
        urllib.request.Request(url, headers=ENTETE), timeout=secondes)


SITE = os.path.dirname(os.path.abspath(__file__))
SORTIE = os.path.join(SITE, "assets", "mobilier")
API = "https://api.polyhaven.com"

# Un salon cohérent : même époque, même registre. Mélanger un fauteuil gothique
# et une table basse contemporaine donne une brocante, pas un intérieur.
SALON = [
    "sofa_03",                  # canapé trois places
    "modern_coffee_table_01",   # table basse
    "mid_century_lounge_chair", # fauteuil
    "side_table_01",            # bout de canapé
    "Shelf_01",                 # étagère
    "potted_plant_01",          # plante
    "potted_plant_04",          # plante
    "ceramic_vase_01",          # vase
    "modern_ceiling_lamp_01",   # suspension
]

# 1k suffit : ces textures habillent des objets vus à deux mètres, et un site
# qui charge du 4k par meuble ne s'ouvre jamais.
RESOLUTION = "1k"


def recuperer(url, vers):
    os.makedirs(os.path.dirname(vers), exist_ok=True)
    if os.path.exists(vers):
        return 0
    with ouvrir(url) as r, open(vers, "wb") as f:
        octets = r.read()
        f.write(octets)
    return len(octets)


def prendre(nom):
    fichiers = json.load(ouvrir(f"{API}/files/{nom}", 60))
    gltf = fichiers.get("gltf", {}).get(RESOLUTION, {}).get("gltf")
    if not gltf:
        print(f"  {nom} : pas de glTF en {RESOLUTION}")
        return 0

    dossier = os.path.join(SORTIE, nom)
    poids = recuperer(gltf["url"], os.path.join(dossier, f"{nom}.gltf"))
    # les fichiers joints gardent leur chemin relatif, que le .gltf référence
    for relatif, d in gltf.get("include", {}).items():
        poids += recuperer(d["url"], os.path.join(dossier, relatif))

    info = json.load(ouvrir(f"{API}/info/{nom}", 60))
    return poids, info.get("name", nom), list(info.get("authors", {}))


def main():
    voulus = sys.argv[1:] or SALON
    os.makedirs(SORTIE, exist_ok=True)
    credits, total = [], 0

    for nom in voulus:
        r = prendre(nom)
        if not r:
            continue
        poids, titre, auteurs = r
        total += poids
        credits.append((nom, titre, auteurs))
        print(f"  {nom:<26} {titre:<24} {poids/1024:7.0f} Ko   {', '.join(auteurs)}")

    with open(os.path.join(SORTIE, "CREDITS.md"), "w", encoding="utf-8") as f:
        f.write("# Mobilier\n\n")
        f.write("Modèles de [Poly Haven](https://polyhaven.com), publiés en **CC0** :\n")
        f.write("domaine public, usage commercial libre, aucune attribution exigée.\n")
        f.write("Elle est faite ici parce que ces gens ont fait le travail.\n\n")
        for nom, titre, auteurs in sorted(credits):
            f.write(f"- **{titre}** (`{nom}`) — {', '.join(auteurs)}\n")

    print(f"\n{len(credits)} modèles, {total/1048576:.1f} Mo au total")


if __name__ == "__main__":
    main()
