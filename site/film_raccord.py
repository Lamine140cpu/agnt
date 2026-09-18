#!/usr/bin/env python3
"""
Extrait la dernière image d'un plan, pour amorcer le suivant.

C'est la pièce qui permet de dépasser les huit secondes d'un plan généré.
Les modèles vidéo acceptent une image de départ : on leur donne la dernière
image du plan précédent, et le nouveau plan commence exactement où l'autre
s'arrête. Enchaînés, six plans de huit secondes font une chorégraphie de
cinquante secondes sans raccord visible.

Sans ça, chaque plan repart d'une voiture légèrement différente — autre teinte
de gris, autres jantes, autre position d'ombre — et les jointures sautent aux
yeux au défilement.

    usage : python3 film_raccord.py plan1.mp4 [sortie.png]
"""
import os
import sys

import cv2

SOURCE = sys.argv[1] if len(sys.argv) > 1 else sys.exit(__doc__)
SORTIE = sys.argv[2] if len(sys.argv) > 2 else os.path.splitext(SOURCE)[0] + "-fin.png"

cap = cv2.VideoCapture(SOURCE)
if not cap.isOpened():
    sys.exit(f"illisible : {SOURCE}")

total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

# On remonte depuis la fin : certains encodages refusent le positionnement sur
# la toute dernière image. La première qui se lit est la bonne.
image = None
for rang in range(total - 1, max(total - 12, -1), -1):
    cap.set(cv2.CAP_PROP_POS_FRAMES, rang)
    ok, img = cap.read()
    if ok:
        image, trouve = img, rang
        break
cap.release()

if image is None:
    sys.exit("aucune image lisible en fin de fichier")

cv2.imwrite(SORTIE, image, [cv2.IMWRITE_PNG_COMPRESSION, 3])
h, w = image.shape[:2]
print(f"image {trouve + 1}/{total} · {w}×{h} → {SORTIE}")
print("\nà joindre comme image de départ du plan suivant.")
