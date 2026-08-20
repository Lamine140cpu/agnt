#!/usr/bin/env python3
"""
Construit la vitrine en FLUX : la page d'un côté, les images de l'autre.

C'est la version d'un vrai hébergement, et c'est la seule qui lève le plafond.
Repliée en un fichier unique, la page doit tenir sous quinze mégaoctets et demi
— ce qui limite la séquence à environ cent soixante-dix images, alors que les
vidéos sources en contiennent neuf cent soixante. On n'en livrait que 18 %.

Servies séparément, les images changent de nature :

  — le navigateur les demande en parallèle et les décode en code natif, hors du
    fil principal, au lieu de traverser une chaîne base64 en JavaScript ;
  — il ne charge que celles dont la fenêtre glissante a besoin, au lieu de tout
    avaler avant la première image ;
  — il les met en cache, donc une seconde visite ne retéléchargera rien ;
  — et le poids total cesse d'être une limite : on peut livrer les 960.

Le lecteur n'a rien à changer. Il possède déjà les deux voies : si la page ne
trouve pas de tableau embarqué, il va chercher les fichiers sur le disque. Ici
on se contente de NE PAS embarquer.

    usage : python3 build_flux.py [qualité] [largeur]

Sortie : dist/flux/ — un dossier à déposer tel quel sur un hébergement.
"""
import io
import os
import shutil
import sys
from glob import glob

from PIL import Image, ImageFilter

SITE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(SITE, "ultra-motion.html")
OUT = os.path.join(SITE, "dist", "flux")
SERIES = {"accueil": "assets/film/accueil",
          "accueil-etroit": "assets/film/accueil-etroit"}

QUALITE = int(sys.argv[1]) if len(sys.argv) > 1 else 80
LARGEUR = int(sys.argv[2]) if len(sys.argv) > 2 else 1280
NETTETE = 45


def en_webp(im, largeur):
    if im.width > largeur:
        im = im.resize((largeur, round(largeur * im.height / im.width)), Image.LANCZOS)
    if NETTETE:
        im = im.filter(ImageFilter.UnsharpMask(radius=1.1, percent=NETTETE, threshold=3))
    tampon = io.BytesIO()
    im.save(tampon, "WEBP", quality=QUALITE, method=6)
    return tampon.getvalue()


def main():
    src = open(SOURCE, encoding="utf-8").read()
    shutil.rmtree(OUT, ignore_errors=True)
    os.makedirs(OUT)

    comptes, total = {}, 0
    for nom, dossier in SERIES.items():
        fichiers = sorted(glob(os.path.join(SITE, dossier, "*.jpg")))
        if not fichiers:
            print(f"  {nom:15s} absente — ignorée")
            continue
        # Le portrait est servi moins large : la toile d'un téléphone est
        # plafonnée à 1,5 pixel physique, soit 585 px sur un écran de 390.
        largeur = LARGEUR if nom == "accueil" else min(LARGEUR, 660)
        cible = os.path.join(OUT, "assets", "film", nom)
        os.makedirs(cible)
        poids = 0
        for i, f in enumerate(fichiers, 1):
            octets = en_webp(Image.open(f).convert("RGB"), largeur)
            poids += len(octets)
            # Extension .jpg mais contenu WebP : le lecteur compose son chemin
            # avec .jpg, et un navigateur reconnaît le format aux octets, pas au
            # nom. Renommer supposerait de toucher au lecteur pour rien.
            open(os.path.join(cible, f"f{i:04d}.jpg"), "wb").write(octets)
        comptes[nom] = len(fichiers)
        total += poids
        print(f"  {nom:15s} {len(fichiers):4d} images · {poids/1048576:6.1f} Mo "
              f"({poids/len(fichiers)/1024:.0f} Ko/image, {largeur}px q{QUALITE})")

    if not comptes:
        sys.exit("aucune image : lancer d'abord film_video.py")

    # Les comptes écrits dans la page sont ceux du mode replié. En flux, c'est
    # le dossier qui fait foi : on les corrige, sinon le lecteur s'arrêterait au
    # compte d'origine et le reste du défilement resterait figé.
    for nom, n in comptes.items():
        avant = src
        src = src.replace(f"'assets/film/{nom}/f',", f"'assets/film/{nom}/f',", 1)
        # remplace le nombre qui suit « images: » sur la ligne de cette série
        import re
        src = re.sub(rf"(chemin: 'assets/film/{re.escape(nom)}/f',\s*images:\s*)\d+",
                     rf"\g<1>{n}", src)
        if src == avant:
            print(f"  ATTENTION : compte de {nom} non trouvé dans la page")

    # La feuille des fontes reste un fichier à part : elle est mise en cache une
    # fois pour toutes, et 216 Ko dans chaque page seraient 216 Ko à chaque
    # visite.
    os.makedirs(os.path.join(OUT, "assets", "fonts"), exist_ok=True)
    shutil.copy(os.path.join(SITE, "assets", "fonts", "ultra.css"),
                os.path.join(OUT, "assets", "fonts", "ultra.css"))

    open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(src)
    page = os.path.getsize(os.path.join(OUT, "index.html")) / 1024
    print(f"\nécrit {OUT}/")
    print(f"  index.html      {page:.0f} Ko   ← ce que le visiteur télécharge d'abord")
    print(f"  images          {total/1048576:.1f} Mo  ← demandées au fil du défilement")
    n = comptes.get("accueil", 0)
    if n:
        print(f"\n  {n} images pour 2700 px de prologue = {2700/n:.1f} px par image")


if __name__ == "__main__":
    main()
