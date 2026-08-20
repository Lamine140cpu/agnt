#!/usr/bin/env python3
"""
Reconstruit les deux séries d'images depuis les rendus 4K agrandis.

Le retour de film_export.py. Les deux vidéos parties se faire agrandir
reviennent en 4K, et il faut en refaire des images numérotées — mais elles ne
reviennent pas telles qu'elles sont parties.

CE QUE CAPCUT A CHANGÉ, mesuré sur les fichiers rendus et non supposé :

  1. LA CADENCE. Les fichiers ont été écrits à 30 i/s ; CapCut les a lus comme
     du 24 et rendus en 30. Tout est donc étiré d'un facteur 30/24 = 1,25, et
     une image sur cinq est inventée. L'ajustement linéaire sur les rendus
     donne source = 0,79915 x image et 0,79992 x image — soit 0,8 des deux
     côtés, à un millième près. On ré-échantillonne pour revenir au compte
     d'origine ; les images inventées disparaissent d'elles-mêmes.

  2. UN OUTRO. Une soixantaine d'images de noir puis un logo, à la fin de
     chaque fichier. Le contenu utile s'arrête à l'image 599 et 1199.

  3. UNE PISTE AUDIO ajoutée. On l'ignore.

CE QUE LE MONTAGE A CHANGÉ. Les deux rendus ne se recouvrent pas, ils se
COMPLÈTENT : le paysage porte les plans 1-2, le portrait les plans 3-6 —
chaque plan agrandi une fois, dans l'orientation où il est natif, sans bande
noire. C'est le meilleur assemblage possible en une passe, et il suffit à
reconstruire les DEUX séries entières :

  accueil (16:9)        plans 1-2 : le rendu paysage tel quel
                        plans 3-6 : le rendu portrait recadré en 16:9,
                                    soit 2160x1215 de vrais pixels

  accueil-etroit (9:16) plans 1-2 : le rendu paysage recadré en 9:16,
                                    soit 1215x2160
                        plans 3-6 : le rendu portrait tel quel

Le recadrage est centré, exactement comme dans film_video.py — le cadre est
donc IDENTIQUE à celui des séries actuelles. Seule la définition change. Et
elle ne change jamais dans le mauvais sens : la plus petite source utilisée
fait 1215 px de petit côté, pour des sorties de 1080 et 1920. On réduit
partout, on n'agrandit nulle part.

    usage : python3 film_reconstruire.py [paysage.mov] [portrait.mov]
"""
import os
import shutil
import sys

import cv2

SITE = os.path.dirname(os.path.abspath(__file__))
IMAGES = 1440                     # le compte des séries d'origine, conservé

# Chaque segment dit : quelles images SOURCES il couvre, et quelles images du
# RENDU les portent. Les deux bornes ont été mesurées, pas devinées — voir
# l'en-tête. `source` est un intervalle semi-ouvert, `rendu` est inclusif.
SEGMENTS = [
    dict(cle="paysage",  source=(0, 480),    rendu=(0, 599)),
    dict(cle="portrait", source=(480, 1440), rendu=(0, 1199)),
]

# Sorties : bien au-dessus de ce que la page sert jamais (1280 px en flux,
# 640 dans le fichier unique), et toujours en dessous de la source.
SORTIES = {
    "accueil":        dict(rapport=16 / 9, largeur=1920),
    "accueil-etroit": dict(rapport=9 / 16, largeur=1080),
}
QUALITE_JPEG = 92


def recadrer(img, rapport):
    """Recadre au centre pour atteindre le rapport voulu, sans déformer.

    Copie conforme de film_video.py : c'est ce qui garantit que le cadre
    reconstruit est celui des séries actuelles, au pixel près."""
    h, w = img.shape[:2]
    actuel = w / h
    if abs(actuel - rapport) < 0.001:
        return img
    if actuel > rapport:
        nw = int(round(h * rapport))
        x = (w - nw) // 2
        return img[:, x:x + nw]
    nh = int(round(w / rapport))
    y = (h - nh) // 2
    return img[y:y + nh, :]


def poser(img, nom, indice):
    reg = SORTIES[nom]
    im = recadrer(img, reg["rapport"])
    larg = reg["largeur"]
    if im.shape[1] != larg:
        haut = round(larg * im.shape[0] / im.shape[1])
        # INTER_AREA en réduction : c'est le seul filtre qui moyenne
        # réellement les pixels supprimés au lieu d'en échantillonner un.
        interp = cv2.INTER_AREA if im.shape[1] > larg else cv2.INTER_CUBIC
        im = cv2.resize(im, (larg, haut), interpolation=interp)
    chemin = os.path.join(SITE, "assets", "film", nom, f"f{indice + 1:04d}.jpg")
    cv2.imwrite(chemin, im, [cv2.IMWRITE_JPEG_QUALITY, QUALITE_JPEG])


def traiter(segment, fichier):
    a, b = segment["source"]
    i0, i1 = segment["rendu"]
    # Pour chaque image source voulue, l'image du rendu qui la porte. La
    # relation est affine et croissante : une seule lecture séquentielle
    # suffit, et c'est ce qui rend l'opération rapide — chercher une image
    # précise dans un flux H.264 oblige à remonter à la clé précédente.
    voulues = [(j, i0 + round((j - a) * (i1 - i0) / (b - a - 1))) for j in range(a, b)]
    cap = cv2.VideoCapture(fichier)
    if not cap.isOpened():
        sys.exit(f"illisible : {fichier}")
    k, i, ecrites = 0, 0, 0
    dernier = None
    while k < len(voulues):
        ok, img = cap.read()
        if not ok:
            break
        while k < len(voulues) and voulues[k][1] == i:
            for nom in SORTIES:
                poser(img, nom, voulues[k][0])
            k += 1
            ecrites += 1
        dernier = i
        i += 1
    cap.release()
    if ecrites != len(voulues):
        sys.exit(f"{fichier} : {ecrites} images écrites sur {len(voulues)} "
                 f"attendues (dernière lue {dernier})")
    print(f"  {segment['cle']:9s} sources {a}-{b - 1} <- rendu {i0}-{i1} "
          f"· {ecrites} images")


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__.strip().splitlines()[-1])
    fichiers = {"paysage": sys.argv[1], "portrait": sys.argv[2]}
    for nom in SORTIES:
        d = os.path.join(SITE, "assets", "film", nom)
        shutil.rmtree(d, ignore_errors=True)
        os.makedirs(d)
    print(f"reconstruction de {IMAGES} images par série")
    for seg in SEGMENTS:
        traiter(seg, fichiers[seg["cle"]])
    for nom in SORTIES:
        d = os.path.join(SITE, "assets", "film", nom)
        n = len(os.listdir(d))
        h, w = cv2.imread(os.path.join(d, "f0001.jpg")).shape[:2]
        o = sum(os.path.getsize(os.path.join(d, f)) for f in os.listdir(d))
        print(f"  {nom:15s} {n} images · {w}x{h} · {o / 1048576:.0f} Mo")
        if n != IMAGES:
            sys.exit(f"{nom} : {n} images au lieu de {IMAGES}")


if __name__ == "__main__":
    main()
