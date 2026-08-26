#!/usr/bin/env python3
"""
Remonte les étiquettes en résolution pour les gros plans.

Gemini plafonne à 1264 px de large. Ce n'est pas rédhibitoire ici : l'artwork
est composé d'aplats et de contours nets, pas de dégradés photographiques.
Un agrandissement par Lanczos suivi d'un masque flou restitue des bords francs,
là où la même opération sur une photo ne ferait qu'amplifier le bruit.

Le filtre bilatéral qui précède aplanit les artefacts de compression sans
toucher aux contours — il est réglé faible pour préserver les trames de points,
qui font partie du dessin.
"""
import os
import cv2
import numpy as np

SITE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(SITE, "assets", "labels")
DST = os.path.join(SITE, "assets", "web")
SCALE = 2.0
QUALITY = 86


def upscale(path):
    im = cv2.imread(path, cv2.IMREAD_COLOR)
    h, w = im.shape[:2]

    # nettoie la compression sans écraser les trames
    im = cv2.bilateralFilter(im, d=5, sigmaColor=18, sigmaSpace=5)

    big = cv2.resize(im, (int(w * SCALE), int(h * SCALE)), interpolation=cv2.INTER_LANCZOS4)

    # masque flou : redonne du mordant aux contours ramollis par l'interpolation
    blur = cv2.GaussianBlur(big, (0, 0), 2.0)
    sharp = cv2.addWeighted(big, 1.55, blur, -0.55, 0)

    # ne réapplique le gain que là où il y a un contour, pour ne pas granuler les aplats
    edges = cv2.Laplacian(cv2.cvtColor(big, cv2.COLOR_BGR2GRAY), cv2.CV_32F, ksize=3)
    mask = cv2.GaussianBlur(np.abs(edges), (0, 0), 1.5)
    mask = np.clip(mask / max(mask.max(), 1e-6) * 3.2, 0, 1)[..., None]

    return (sharp * mask + big * (1 - mask)).astype(np.uint8)


def main():
    os.makedirs(DST, exist_ok=True)
    total = 0
    for name in sorted(os.listdir(SRC)):
        if not name.startswith("label-"):
            continue
        out = os.path.join(DST, name.replace(".png", ".jpg"))
        img = upscale(os.path.join(SRC, name))
        cv2.imwrite(out, img, [cv2.IMWRITE_JPEG_QUALITY, QUALITY, cv2.IMWRITE_JPEG_PROGRESSIVE, 1])
        kb = os.path.getsize(out) // 1024
        total += kb
        print(f"{name:22s} -> {img.shape[1]}x{img.shape[0]}  {kb} Ko")
    print(f"total {total} Ko")


if __name__ == "__main__":
    main()
