#!/usr/bin/env python3
"""
Replie la vitrine du studio en un seul fichier.

Deux choses à embarquer, pas une seule — c'est ce qui distingue cette
construction de celle du film :

  1. la séquence du prologue, déposée dans `window.__FILM.accueil` ;
  2. les quatre vignettes des pièces, qui sont des <img> pointant vers le
     disque. Servies telles quelles dans un fichier unique elles ne se
     résolvent plus, et une politique de sécurité stricte les bloquerait de
     toute façon. Elles deviennent donc des adresses `data:`.

    usage : python3 build_ultra.py [qualité] [largeur] [artefact] [net=N]

Deux sorties, parce que deux hébergements attendent l'inverse l'un de l'autre :

  dist/ultra-motion.html           document complet — livré, ou ouvert d'un
                                   double-clic. Il lui faut son <!DOCTYPE>,
                                   son <html>, son <meta viewport>.

  dist/ultra-motion-artefact.html  fragment, écrit seulement avec « artefact ».
                                   L'hébergement fournit l'enveloppe ; les
                                   balises de structure y feraient doublon.
"""
import base64
import io
import json
import os
import re
import sys
from glob import glob

from PIL import Image, ImageFilter

SITE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(SITE, "ultra-motion.html")
OUT = os.path.join(SITE, "dist", "ultra-motion.html")
OUT_ARTEFACT = os.path.join(SITE, "dist", "ultra-motion-artefact.html")
# Deux séries : le paysage pour les écrans larges, le portrait pour les
# téléphones tenus debout. La seconde n'est pas la première rognée — deux
# des quatre plans sont nativement en 9:16.
SERIES = {"accueil": "assets/film/accueil",
          "accueil-etroit": "assets/film/accueil-etroit"}

_libres = [a for a in sys.argv[1:] if a != "artefact" and not a.startswith("net=")]
ARTEFACT = "artefact" in sys.argv[1:]
# Masque flou, appliqué APRÈS la réduction — qui est elle-même adoucissante.
# Seuil 3 : on ne renforce que ce qui est déjà un contour, pour ne pas réveiller
# le bruit de compression des aplats.
NETTETE = next((int(a[4:]) for a in sys.argv[1:] if a.startswith("net=")), 45)
QUALITE = int(_libres[0]) if len(_libres) > 0 else 78
LARGEUR = int(_libres[1]) if len(_libres) > 1 else 1280


def en_webp(im, largeur, qualite):
    """Réduit, affûte, encode. Rend les octets."""
    if im.width > largeur:
        im = im.resize((largeur, round(largeur * im.height / im.width)), Image.LANCZOS)
    if NETTETE:
        im = im.filter(ImageFilter.UnsharpMask(radius=1.1, percent=NETTETE, threshold=3))
    tampon = io.BytesIO()
    # method=6 : l'encodeur cherche plus longtemps. On construit une fois, la
    # page est servie des milliers de fois — le calcul est du bon côté.
    im.save(tampon, "WEBP", quality=qualite, method=6)
    return tampon.getvalue()


def sequence(nom, dossier, largeur):
    fichiers = sorted(glob(os.path.join(SITE, dossier, "*.jpg")))
    if not fichiers:
        return None, 0
    sorties, avant, apres = [], 0, 0
    for f in fichiers:
        avant += os.path.getsize(f)
        octets = en_webp(Image.open(f).convert("RGB"), largeur, QUALITE)
        apres += len(octets)
        sorties.append(base64.b64encode(octets).decode())
    print(f"  {nom:15s} {len(sorties):4d} images · {avant/1048576:5.1f} Mo JPEG -> "
          f"{apres/1048576:5.1f} Mo WebP {largeur}px q{QUALITE} "
          f"({apres/len(sorties)/1024:.0f} Ko/image)")
    return sorties, apres


def vignettes(src):
    """Remplace chaque <img src="assets/..."> par son adresse data:."""
    poids = 0

    def remplacer(m):
        nonlocal poids
        chemin = os.path.join(SITE, m.group(1))
        if not os.path.exists(chemin):
            print(f"  ATTENTION : vignette absente — {m.group(1)}")
            return m.group(0)
        # 1100 px : ces images ne dépassent jamais la moitié de l'écran, les
        # servir en 1600 serait payer une définition que personne ne voit.
        octets = en_webp(Image.open(chemin).convert("RGB"), 1100, QUALITE)
        poids += len(octets)
        return ('src="data:image/webp;base64,'
                + base64.b64encode(octets).decode() + '"')

    src = re.sub(r'src="(assets/[^"]+)"', remplacer, src)
    print(f"  vignettes {poids/1048576:5.2f} Mo")
    return src, poids


def fontes(src):
    """Remplace le <link> vers la feuille des fontes par son contenu.

    Elle contient déjà les fontes en adresses `data:` — il ne reste qu'à la
    coller. Une feuille externe dans un fichier unique ne se résoudrait pas,
    et la page retomberait sur Georgia sans rien dire."""
    def remplacer(m):
        chemin = os.path.join(SITE, m.group(1))
        if not os.path.exists(chemin):
            sys.exit(f"feuille de fontes absente : {m.group(1)}\n"
                     f"  lancer d'abord : python3 fontes_locales.py")
        contenu = open(chemin, encoding="utf-8").read()
        print(f"  fontes    {len(contenu)/1048576:5.2f} Mo")
        return "<style>\n" + contenu + "</style>"

    return re.sub(r'<link rel="stylesheet" href="(assets/[^"]+\.css)">', remplacer, src)


def main():
    src = open(SOURCE, encoding="utf-8").read()
    film, poids_seq = {}, 0
    for nom, dossier in SERIES.items():
        # Le portrait est servi moins large : il occupe l'écran d'un téléphone,
        # pas celui d'un bureau, et il s'ajoute au poids du paysage.
        largeur = LARGEUR if nom == "accueil" else min(LARGEUR, 720)
        images, poids = sequence(nom, dossier, largeur)
        if images is None:
            print(f"  {nom:15s} absente — ignorée")
            continue
        film[nom] = images
        poids_seq += poids
    if not film:
        sys.exit("aucune image : lancer d'abord film_video.py")

    src, poids_vig = vignettes(src)
    src = fontes(src)

    charge = ("<script>window.__FILM = "
              + json.dumps(film, separators=(",", ":")) + ";</script>\n")

    # On garde le document ENTIER et on injecte avant </head>. Ne recopier que
    # l'intérieur de <head> et <body> — comme le faisait la première version du
    # film — produit un fragment : sans DOCTYPE le navigateur passe en mode
    # « quirks », et sans <meta viewport> un téléphone rend la page sur 980 px.
    # Injecter APRÈS le <title> le laisse dans les premiers kilo-octets, seuls
    # lus pour le nommer.
    if "</head>" not in src:
        sys.exit("ultra-motion.html : </head> introuvable")
    page = src.replace("</head>", charge + "</head>", 1)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w", encoding="utf-8").write(page)
    poids = len(page) / 1048576
    print(f"\nécrit {OUT} — {poids:.2f} Mo "
          f"(dont {(poids_seq + poids_vig)*1.34/1048576:.2f} Mo d'images)")

    if ARTEFACT:
        tete = page.split("<head>", 1)[1].split("</head>", 1)[0]
        corps = page.split("<body>", 1)[1].rsplit("</body>", 1)[0]
        fragment = tete.strip() + "\n" + corps.strip() + "\n"
        open(OUT_ARTEFACT, "w", encoding="utf-8").write(fragment)
        print(f"écrit {OUT_ARTEFACT} — {len(fragment)/1048576:.2f} Mo (fragment)")

    if poids > 15.5:
        print("  ATTENTION : au-delà de la limite d'un artefact, baisser la qualité")


if __name__ == "__main__":
    main()
