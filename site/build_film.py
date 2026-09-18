#!/usr/bin/env python3
"""
Replie le film en un seul fichier.

Les images arrivent du rendu en JPEG de haute qualité — bon pour archiver,
mauvais pour livrer. Elles repassent donc en WebP, qui divise leur poids par
trois à l'œil nu identique, puis sont embarquées en base64.

Le tableau embarqué se dépose dans `window.__FILM`, que le lecteur consulte au
démarrage. En développement, la variable n'existe pas et le lecteur va lire le
disque : le même fichier sert dans les deux cas.

    usage : python3 build_film.py [qualité] [largeur] [artefact] [net=N]

Deux sorties, parce que deux hébergements attendent deux choses opposées :

  dist/film.html           document complet — c'est ce qu'on livre au client
                           et ce qu'on ouvre en double-cliquant. Il lui faut
                           son <!DOCTYPE>, son <html>, son <meta viewport>.

  dist/film-artefact.html  fragment, écrit seulement si on passe « artefact ».
                           L'hébergement d'artefact fournit lui-même
                           l'enveloppe ; les balises de structure y feraient
                           doublon.

Le mot « artefact » ajoute la seconde sortie, il ne remplace pas la première.
"""
import base64
import io
import json
import os
import sys
from glob import glob

from PIL import Image, ImageFilter

SITE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(SITE, "dist", "film.html")
OUT_ARTEFACT = os.path.join(SITE, "dist", "film-artefact.html")

_args = [a for a in sys.argv[1:] if a != "artefact" and not a.startswith("net=")]
ARTEFACT = "artefact" in sys.argv[1:]
# Masque flou. Mesuré sur la vidéo générée : la source est molle AVANT toute
# compression, et la toile la réaffiche agrandie — jusqu'à 2,25 fois sur un
# écran dense. Passer la qualité WebP de 72 à 86 coûte 13 Ko l'image et ne
# gagne presque rien, parce que la compression n'était pas le goulot. Le
# masque, lui, coûte 2 Ko et sépare les détails fins. Il s'applique APRÈS la
# réduction, qui est elle-même adoucissante.
NETTETE = next((int(a[4:]) for a in sys.argv[1:] if a.startswith("net=")), 55)
sys.argv = [sys.argv[0]] + _args

QUALITE = int(sys.argv[1]) if len(sys.argv) > 1 else 76
# Largeur de livraison. Les images sont calculées plus grandes qu'elles ne
# seront servies : réduire après coup lisse le bruit du rendu et coûte moins
# cher qu'une image calculée directement à cette taille.
LARGEUR = int(sys.argv[2]) if len(sys.argv) > 2 else 1280

SERIES = {"large": "assets/film/large", "etroit": "assets/film/etroit"}


def encoder(dossier):
    """JPEG sur disque -> WebP en base64, dans l'ordre des numéros."""
    fichiers = sorted(glob(os.path.join(SITE, dossier, "*.jpg")))
    if not fichiers:
        return None, 0, 0
    sorties, avant, apres = [], 0, 0
    for f in fichiers:
        avant += os.path.getsize(f)
        im = Image.open(f).convert("RGB")
        if im.width > LARGEUR:
            im = im.resize((LARGEUR, round(LARGEUR * im.height / im.width)), Image.LANCZOS)
        if NETTETE:
            # seuil 3 : on ne renforce que ce qui est déjà un contour, pour ne
            # pas réveiller le bruit de compression des aplats.
            im = im.filter(ImageFilter.UnsharpMask(radius=1.1, percent=NETTETE, threshold=3))
        tampon = io.BytesIO()
        # method=6 : l'encodeur cherche plus longtemps. On construit une fois,
        # la page est servie des milliers de fois — le calcul est du bon côté.
        im.save(tampon, "WEBP", quality=QUALITE, method=6)
        apres += tampon.tell()
        sorties.append(base64.b64encode(tampon.getvalue()).decode())
    return sorties, avant, apres


def main():
    os.chdir(SITE)
    src = open("film.html", encoding="utf-8").read()

    film, total = {}, 0
    for nom, dossier in SERIES.items():
        images, avant, apres = encoder(dossier)
        if images is None:
            print(f"  {nom:8s} absente — ignorée")
            continue
        film[nom] = images
        total += apres
        print(f"  {nom:8s} {len(images):4d} images · "
              f"{avant/1048576:5.1f} Mo JPEG -> {apres/1048576:5.1f} Mo WebP {LARGEUR}px q{QUALITE} "
              f"({apres/len(images)/1024:.0f} Ko/image)")

    if not film:
        sys.exit("aucune image : lancer d'abord film_rendu.mjs")

    # Le lecteur lit ce que la construction dépose ; sans ça il ira sur le disque.
    charge = ("<script>window.__FILM = " + json.dumps(film, separators=(",", ":"))
              + ";</script>\n")

    # On garde le document ENTIER et on se contente d'injecter les images à la
    # fin de l'en-tête.
    #
    # La version précédente ne recopiait que le contenu de <head> et de <body>
    # et jetait le reste, parce qu'une enveloppe d'artefact fournit ses propres
    # <!DOCTYPE>, <html> et <body>. Mais ce fichier est aussi — et surtout —
    # servi tel quel chez le client, et là il lui manquait tout : sans DOCTYPE
    # le navigateur passe en mode « quirks », et sans <meta viewport> un
    # téléphone rend la page sur 980 px de large. La page ne s'affichait pas.
    #
    # Injecter avant </head> garantit aussi que window.__FILM existe quand le
    # script du lecteur s'exécute, plus bas dans le corps.
    if "</head>" not in src:
        sys.exit("film.html : </head> introuvable, injection impossible")
    page = src.replace("</head>", charge + "</head>", 1)

    # Les chemins disque ne servent plus, mais on les laisse : ils documentent
    # d'où viennent les images, et le repli sur fetch reste un filet.
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w", encoding="utf-8").write(page)
    poids = len(page) / 1048576
    print(f"\nécrit {OUT} — {poids:.2f} Mo "
          f"(dont {total*1.34/1048576:.2f} Mo d'images en base64)")

    if ARTEFACT:
        # On ne retire QUE les quatre balises de structure. Le <title> et les
        # <meta> restent : l'enveloppe les absorbe dans son propre en-tête, et
        # le titre doit rester dans les premiers kilo-octets pour être lu —
        # c'est pour ça que les images sont injectées après lui, pas avant.
        tete = page.split("<head>", 1)[1].split("</head>", 1)[0]
        corps = page.split("<body>", 1)[1].rsplit("</body>", 1)[0]
        fragment = tete.strip() + "\n" + corps.strip() + "\n"
        open(OUT_ARTEFACT, "w", encoding="utf-8").write(fragment)
        print(f"écrit {OUT_ARTEFACT} — {len(fragment)/1048576:.2f} Mo (fragment)")

    if poids > 15.5:
        print("  ATTENTION : au-delà de la limite d'un artefact, baisser la qualité")


if __name__ == "__main__":
    main()
