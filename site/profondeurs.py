#!/usr/bin/env python3
"""
Calcule une carte de profondeur par photographie, avec Depth Anything V2.

Une photographie plein cadre qu'on remplace par la suivante reste un
diaporama : rien ne bouge dans l'image. Avec sa profondeur, elle devient une
surface en relief — le premier plan se déplace plus vite que le fond quand la
caméra bouge, et le regard y lit un volume. Ce n'est pas encore une visite
libre, mais c'est un vrai déplacement dans une matière photographique.

Le modèle tourne sur le processeur, en ONNX : rien à installer côté carte
graphique, et le calcul se fait une fois pour toutes, hors ligne.

    usage : python3 profondeurs.py [numéro …]     (défaut : toutes)
"""
import os
import sys

import cv2
import numpy as np
import onnxruntime as ort

SITE = os.path.dirname(os.path.abspath(__file__))
PHOTOS = os.path.join(SITE, "assets", "photos")
MODELE = os.environ.get("DAV2_ONNX", "/tmp/dav2.onnx")

# multiple de 14 imposé par le découpage en tuiles du modèle
COTE = 518
MOYENNE = np.array([0.485, 0.456, 0.406], np.float32)
ECART = np.array([0.229, 0.224, 0.225], np.float32)


def profondeur(session, bgr):
    h, w = bgr.shape[:2]
    x = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
    x = cv2.resize(x, (COTE, COTE), interpolation=cv2.INTER_CUBIC)
    x = ((x - MOYENNE) / ECART).transpose(2, 0, 1)[None]

    brut = session.run(None, {"pixel_values": x})[0][0]
    carte = cv2.resize(brut, (w, h), interpolation=cv2.INTER_CUBIC)

    # Le modèle rend une disparité : grand au premier plan, petit au loin. On la
    # ramène en 0..1 en écartant les extrêmes, qu'un reflet ou une vitre suffit
    # à envoyer très loin et qui écraseraient tout le reste de l'échelle.
    bas, haut = np.percentile(carte, 1), np.percentile(carte, 99)
    return np.clip((carte - bas) / max(haut - bas, 1e-6), 0, 1)


def main():
    if not os.path.exists(MODELE):
        sys.exit(f"modèle introuvable : {MODELE}\n"
                 "  curl -L -o /tmp/dav2.onnx https://huggingface.co/"
                 "onnx-community/depth-anything-v2-small/resolve/main/onnx/model.onnx")

    voulus = set(sys.argv[1:])
    session = ort.InferenceSession(MODELE, providers=["CPUExecutionProvider"])

    for nom in sorted(os.listdir(PHOTOS), key=lambda n: (len(n), n)):
        if not nom.endswith(".jpg") or nom.endswith("-p.jpg"):
            continue
        num = nom[:-4]
        if voulus and num not in voulus:
            continue

        bgr = cv2.imread(os.path.join(PHOTOS, nom))
        carte = profondeur(session, bgr)

        # Un lissage qui respecte les contours : sans lui, le bruit du modèle
        # devient un relief granuleux, et les bords d'un meuble se déchirent.
        lisse = cv2.ximgproc.jointBilateralFilter(bgr, (carte * 255).astype(np.uint8), 9, 24, 9) \
            if hasattr(cv2, "ximgproc") else cv2.bilateralFilter((carte * 255).astype(np.uint8), 9, 40, 9)

        sortie = os.path.join(PHOTOS, f"{num}-p.jpg")
        cv2.imwrite(sortie, lisse, [cv2.IMWRITE_JPEG_QUALITY, 92])
        print(f"{num}-p.jpg  {lisse.shape[1]}x{lisse.shape[0]}  "
              f"{os.path.getsize(sortie)//1024} Ko")


if __name__ == "__main__":
    main()
