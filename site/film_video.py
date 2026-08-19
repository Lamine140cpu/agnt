#!/usr/bin/env python3
"""
Découpe une vidéo en séquence d'images pour le lecteur.

C'est le chaînon qui manquait. Une vidéo générée — ou tournée — est déjà une
suite d'images cohérentes entre elles : c'est même la définition d'un modèle
vidéo, par opposition à un modèle d'images qui échantillonne chaque vue
indépendamment et fait donc frémir les détails d'une image à l'autre.

Le fichier sort au même format que film_rendu.mjs — des JPEG numérotés dans
assets/film/ — pour que build_film.py n'ait rien à savoir de leur provenance.

    usage : python3 film_video.py film.mp4 [images] [largeur] [serie]

    serie : « large » (défaut, recadrage paysage) ou « etroit » (portrait,
            pour les téléphones — c'est un recadrage, pas une réduction :
            une composition pensée en 16:9 ne tient pas debout en 9:16)
"""
import os
import sys

import cv2
import numpy as np
from PIL import Image

SITE = os.path.dirname(os.path.abspath(__file__))

SOURCE = sys.argv[1] if len(sys.argv) > 1 else sys.exit(__doc__)
IMAGES = int(sys.argv[2]) if len(sys.argv) > 2 else 150
LARGEUR = int(sys.argv[3]) if len(sys.argv) > 3 else 1440
SERIE = sys.argv[4] if len(sys.argv) > 4 else "large"

FORMATS = {"large": 16 / 9, "etroit": 9 / 16}
if SERIE not in FORMATS:
    sys.exit(f"série inconnue : {SERIE} (large ou etroit)")
CIBLE = FORMATS[SERIE]
SORTIE = os.path.join(SITE, "assets", "film", SERIE)


def recadrer(img, rapport):
    """Recadre au centre pour atteindre le rapport voulu, sans déformer."""
    h, w = img.shape[:2]
    actuel = w / h
    if abs(actuel - rapport) < 0.001:
        return img
    if actuel > rapport:                      # trop large : on rogne les côtés
        nw = int(round(h * rapport))
        x = (w - nw) // 2
        return img[:, x:x + nw]
    nh = int(round(w / rapport))              # trop haut : on rogne haut et bas
    y = (h - nh) // 2
    return img[y:y + nh, :]


def main():
    cap = cv2.VideoCapture(SOURCE)
    if not cap.isOpened():
        sys.exit(f"illisible : {SOURCE}")

    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"source : {total} images · {fps:.1f} i/s · {w}×{h} · "
          f"{total / fps if fps else 0:.1f} s")

    if total < IMAGES:
        print(f"  ATTENTION : la vidéo n'a que {total} images pour {IMAGES} demandées.\n"
              f"  Des images seront répétées, et le défilement marquera un temps.")

    os.makedirs(SORTIE, exist_ok=True)
    for f in os.listdir(SORTIE):
        if f.endswith(".jpg"):
            os.remove(os.path.join(SORTIE, f))

    # Répartition régulière sur toute la durée. On ne prend pas une image sur
    # n : si la vidéo est plus longue que prévu, ce serait tronquer la fin.
    rangs = np.linspace(0, max(total - 1, 0), IMAGES).round().astype(int)

    ecrites, precedent, saut = 0, None, 0
    for i, rang in enumerate(rangs):
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(rang))
        ok, img = cap.read()
        if not ok:
            # Certains encodages refusent le positionnement exact : on garde la
            # précédente plutôt que d'ouvrir un trou dans la séquence.
            if precedent is None:
                continue
            img, saut = precedent, saut + 1
        precedent = img

        img = recadrer(img, CIBLE)
        hh = int(round(LARGEUR / CIBLE))
        img = cv2.resize(img, (LARGEUR, hh), interpolation=cv2.INTER_AREA)
        Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)).save(
            os.path.join(SORTIE, f"f{i + 1:04d}.jpg"), "JPEG", quality=94, optimize=True)
        ecrites += 1

    cap.release()
    poids = sum(os.path.getsize(os.path.join(SORTIE, f))
                for f in os.listdir(SORTIE) if f.endswith(".jpg")) / 1048576
    print(f"écrit {ecrites} images {LARGEUR}×{int(round(LARGEUR / CIBLE))} "
          f"dans {SORTIE} — {poids:.1f} Mo")
    if saut:
        print(f"  {saut} image(s) répétée(s) faute de positionnement exact")
    print("\nensuite : python3 build_film.py 72 1280")


if __name__ == "__main__":
    main()
