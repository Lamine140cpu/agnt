#!/usr/bin/env python3
"""
Découpe une ou plusieurs vidéos en séquence d'images pour le lecteur.

C'est le chaînon qui manquait. Une vidéo générée — ou tournée — est déjà une
suite d'images cohérentes entre elles : c'est même la définition d'un modèle
vidéo, par opposition à un modèle d'images qui échantillonne chaque vue
indépendamment et fait donc frémir les détails d'une image à l'autre.

Plusieurs fichiers sont traités comme un seul plan continu. C'est nécessaire :
un plan généré fait huit secondes, une chorégraphie en fait cinquante. Les
images demandées sont réparties au prorata de la durée de chaque plan, pour
que la vitesse reste la même de bout en bout — répartir également entre des
plans de durées différentes accélérerait sur les courts.

Le fichier sort au même format que film_rendu.mjs — des JPEG numérotés dans
assets/film/ — pour que build_film.py n'ait rien à savoir de leur provenance.

    usage : python3 film_video.py plan1.mp4 [plan2.mp4 ...] [images] [largeur] [serie]

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

# Les fichiers d'abord, les réglages ensuite. On les sépare en regardant le
# disque plutôt qu'en comptant les positions : ça laisse passer un nombre
# quelconque de plans sans que l'appel change de forme.
_args = sys.argv[1:]
SOURCES = [a for a in _args if os.path.isfile(a)]
_reste = [a for a in _args if not os.path.isfile(a)]
if not SOURCES:
    sys.exit(__doc__)

IMAGES = int(_reste[0]) if len(_reste) > 0 else 150
LARGEUR = int(_reste[1]) if len(_reste) > 1 else 1440
SERIE = _reste[2] if len(_reste) > 2 else "large"

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


def inspecter(chemin):
    """Ouvre un plan et rend (capture, nombre d'images, i/s)."""
    cap = cv2.VideoCapture(chemin)
    if not cap.isOpened():
        sys.exit(f"illisible : {chemin}")
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"  {os.path.basename(chemin):28s} {total:4d} images · {fps:4.1f} i/s · "
          f"{w}×{h} · {total / fps if fps else 0:5.1f} s")
    return cap, total, fps


def main():
    print(f"{len(SOURCES)} plan(s) :")
    plans = [inspecter(s) for s in SOURCES]
    durees = [t for _, t, _ in plans]
    somme = sum(durees)
    if somme < IMAGES:
        print(f"  ATTENTION : {somme} images disponibles pour {IMAGES} demandées.\n"
              f"  Des images seront répétées, et le défilement marquera un temps.")

    # Prorata de la durée : un plan deux fois plus long reçoit deux fois plus
    # d'images, donc la vitesse apparente ne change pas d'un plan à l'autre.
    # Le reste de la division va aux plans les plus longs, pas au dernier.
    parts = [IMAGES * d / somme for d in durees]
    quotas = [int(p) for p in parts]
    for j in sorted(range(len(parts)), key=lambda k: parts[k] - quotas[k],
                    reverse=True)[:IMAGES - sum(quotas)]:
        quotas[j] += 1

    os.makedirs(SORTIE, exist_ok=True)
    for f in os.listdir(SORTIE):
        if f.endswith(".jpg"):
            os.remove(os.path.join(SORTIE, f))

    hh = int(round(LARGEUR / CIBLE))
    ecrites, saut = 0, 0
    for p, ((cap, total, _), quota) in enumerate(zip(plans, quotas)):
        if quota <= 0:
            cap.release()
            continue
        # Les plans enchaînés démarrent sur l'image de fin du précédent : la
        # reprendre la ferait tenir deux fois plus longtemps à l'écran, et le
        # défilement buterait à chaque jointure.
        debut = 1 if p > 0 and total > 1 else 0
        rangs = np.linspace(debut, max(total - 1, debut), quota).round().astype(int)

        precedent = None
        for rang in rangs:
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(rang))
            ok, img = cap.read()
            if not ok:
                # Certains encodages refusent le positionnement exact : on garde
                # la précédente plutôt que d'ouvrir un trou dans la séquence.
                if precedent is None:
                    continue
                img, saut = precedent, saut + 1
            precedent = img

            img = cv2.resize(recadrer(img, CIBLE), (LARGEUR, hh),
                             interpolation=cv2.INTER_AREA)
            ecrites += 1
            Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)).save(
                os.path.join(SORTIE, f"f{ecrites:04d}.jpg"),
                "JPEG", quality=94, optimize=True)
        cap.release()

    poids = sum(os.path.getsize(os.path.join(SORTIE, f))
                for f in os.listdir(SORTIE) if f.endswith(".jpg")) / 1048576
    if len(SOURCES) > 1:
        print("réparti " + " + ".join(str(q) for q in quotas) + f" = {ecrites} images")
    print(f"écrit {ecrites} images {LARGEUR}×{hh} dans {SORTIE} — {poids:.1f} Mo")
    if saut:
        print(f"  {saut} image(s) répétée(s) faute de positionnement exact")
    # 46 Ko l'image livrée, mesurés sur la première série. C'est le seul
    # chiffre qui décide de la longueur d'une chorégraphie.
    print(f"  soit environ {ecrites * 46 / 1024:.1f} Mo une fois livrées")
    print("\nensuite : python3 build_film.py 72 1280")


if __name__ == "__main__":
    main()
