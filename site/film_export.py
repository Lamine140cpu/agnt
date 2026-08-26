#!/usr/bin/env python3
"""
Rassemble une série d'images en une vidéo, pour la faire agrandir ailleurs.

Le chemin inverse de film_video.py. On l'emploie quand un outil externe —
un agrandisseur par réseau de neurones, en ligne — doit travailler sur la
suite complète plutôt que sur des images isolées.

POURQUOI UNE VIDÉO ET NON UN LOT D'IMAGES. Un agrandisseur d'images invente
du détail image par image, indépendamment : le grain de gravier qu'il
fabrique à l'image 431 n'est pas celui de l'image 432. Dans une vidéo lue à
trente images par seconde, personne ne le voit. Ici le visiteur s'arrête sur
une image et la regarde fixement, puis avance lentement — c'est exactement là
que le scintillement se remarque. Un agrandisseur VIDÉO regarde les images
voisines et impose une cohérence dans le temps. D'où la vidéo.

POURQUOI DEUX VIDÉOS ET NON UNE. Les vidéos d'origine n'existent plus ; il ne
reste que les deux séries d'images, et chacune est un rognage CENTRÉ dans un
sens différent. Aucune ne contient l'autre :

  accueil (16:9)          plans 1-2 : image entière, native
                          plans 3-6 : 31 % de la hauteur d'une source 9:16

  accueil-etroit (9:16)   plans 1-2 : 31 % de la largeur d'une source 16:9
                          plans 3-6 : image entière, réduite de 720 à 660

Agrandir une seule des deux et recadrer l'autre depuis elle donnerait bien
assez de pixels — un 4K paysage rogné en portrait fait encore 1215 x 2160,
largement au-dessus des 585 d'un téléphone. Ce n'est donc pas une question de
définition mais de CADRE : le burger est composé à la verticale, et sa
version paysage a déjà perdu le pain du haut. On ne le récupérera jamais en
agrandissant.

    usage : python3 film_export.py [série] [crf] [fps]

30 i/s : mesuré, non supposé. Les deux séries comptent 1 440 images dont 5
seulement sont des quasi-doublons — donc 1 440 images distinctes pour six
plans de huit secondes, soit trente par seconde. Les écrire en 24 étirerait
le mouvement d'un quart.

CRF 18 : l'agrandisseur amplifie ce qu'on lui donne, y compris les défauts
de compression, donc on encode bien au-dessus du nécessaire pour un simple
visionnage — la vidéo est un intermédiaire, pas une livraison. Mais serrer
davantage ne sert à rien, et c'est mesuré : contre les JPEG sources, CRF 14
donne 41,9 dB et CRF 21 en donne 40,1. Un virgule huit décibel pour trois
fois le poids. La raison est que la source est DÉJÀ du JPEG : l'encodeur
reproduit surtout les défauts qu'elle porte, et l'erreur bute sur ce
plancher-là bien avant d'être limitée par le débit. 18 tient sous les trente
mébioctets d'un envoi sans rien céder de visible.
"""
import os
import subprocess
import sys
from glob import glob

import cv2
import imageio_ffmpeg

SITE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(SITE, "dist", "export")
SERIES = {"accueil": "assets/film/accueil",
          "accueil-etroit": "assets/film/accueil-etroit"}

QUOI = sys.argv[1] if len(sys.argv) > 1 else "tout"
CRF = int(sys.argv[2]) if len(sys.argv) > 2 else 18
FPS = int(sys.argv[3]) if len(sys.argv) > 3 else 30


def exporter(nom, dossier):
    fichiers = sorted(glob(os.path.join(SITE, dossier, "*.jpg")))
    if not fichiers:
        print(f"  {nom} : aucune image")
        return None
    h, w = cv2.imread(fichiers[0]).shape[:2]
    # H.264 exige des dimensions paires. On ROGNE la ligne en trop plutôt que
    # d'ajouter une bordure : une ligne noire d'un pixel deviendrait quatre
    # après agrandissement, et l'agrandisseur la prendrait pour un contour.
    w2, h2 = w - (w % 2), h - (h % 2)
    chemin = os.path.join(OUT, f"{nom}.mp4")
    cmd = [
        imageio_ffmpeg.get_ffmpeg_exe(), "-y",
        "-framerate", str(FPS),
        "-pattern_type", "glob", "-i", os.path.join(SITE, dossier, "*.jpg"),
        "-vf", f"crop={w2}:{h2}:0:0",
        "-c:v", "libx264", "-preset", "slow", "-crf", str(CRF),
        # yuv420p : le JPEG est déjà sous-échantillonné en 4:2:0, on ne perd
        # donc rien de plus, et c'est le seul format que tous les outils en
        # ligne acceptent sans discuter.
        "-pix_fmt", "yuv420p", "-profile:v", "high",
        # +faststart : l'index passe en tête, un site peut lire le fichier
        # avant de l'avoir entièrement reçu.
        "-movflags", "+faststart",
        chemin,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr[-1500:])
        sys.exit(f"échec de l'encodage : {nom}")
    o = os.path.getsize(chemin)
    print(f"  {nom:15s} {len(fichiers)} images · {w2}x{h2} · "
          f"{len(fichiers)/FPS:.1f} s à {FPS} i/s · {o/1048576:.1f} Mo")
    return chemin


def main():
    os.makedirs(OUT, exist_ok=True)
    voulues = SERIES if QUOI == "tout" else {QUOI: SERIES[QUOI]}
    print(f"export CRF {CRF} · {FPS} i/s")
    for nom, dossier in voulues.items():
        exporter(nom, dossier)
    print(f"\nécrit dans {OUT}")


if __name__ == "__main__":
    main()
