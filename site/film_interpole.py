#!/usr/bin/env python3
"""
Fabrique des images intermédiaires par flot optique.

Le lecteur redessine à la cadence de l'écran — soixante fois par seconde, cent
vingt sur un écran rapide. Ce n'est jamais la limite. La limite, c'est le
nombre d'images SOURCES qui passent par seconde, et il dépend de la vitesse à
laquelle le visiteur fait défiler : en défilement lent, la même image tient
plusieurs dizaines de millisecondes.

Le fondu du lecteur adoucit ce palier, mais il ne fait qu'un mélange : deux
images superposées en transparence, pas un mouvement. Ici on calcule le
DÉPLACEMENT de chaque pixel entre deux images consécutives, et on l'applique à
mi-chemin. Le résultat est une vraie image intermédiaire, pas une surimpression.

Ça ne remplace pas des images sources plus rapprochées, et ce n'est pas un
gain général : mesuré sur cette séquence, le flot bat le fondu sur les plans
lents et échoue exactement comme lui sur les plans rapides. Il sert donc à
rattraper les passages calmes, pas à doubler une séquence entière.

Et il y a plus simple, quand le poids le permet : les vidéos sources comptent
240 images chacune. Une séquence de 170 images tirée de quatre plans n'en
utilise qu'une sur six. Tant qu'on peut se le permettre, mieux vaut en extraire
davantage que d'en inventer.

    usage : python3 film_interpole.py <serie> [facteur]

    serie   : accueil, accueil-etroit, large, etroit
    facteur : 2 (défaut) insère une image entre chaque paire
              3 en insère deux

Les images intermédiaires portent des numéros décalés, et le dossier est
renuméroté d'un bloc à la fin : le lecteur n'a rien à savoir de leur origine.
"""
import os
import shutil
import sys
from glob import glob

import cv2
import numpy as np

SITE = os.path.dirname(os.path.abspath(__file__))

SERIE = sys.argv[1] if len(sys.argv) > 1 else sys.exit(__doc__)
FACTEUR = int(sys.argv[2]) if len(sys.argv) > 2 else 2
DOSSIER = os.path.join(SITE, "assets", "film", SERIE)

# Seuil calé sur mesure, pas sur estimation. Comparé côte à côte sur trois
# endroits de la séquence :
#
#   travelling dans la villa   écart 15,7   le flot est NETTEMENT meilleur que
#                                           le fondu — plante, bibliothèque et
#                                           canapé restent des objets nets là
#                                           où le mélange les dédouble ;
#   passage le long de la Golf écart 23,3   les deux échouent, on voit deux
#                                           arrières de voiture ;
#   passage derrière le mur    écart 25,6   bouillie dans les deux cas.
#
# Au-delà d'un écart de 18, le déplacement entre deux images dépasse ce qu'un
# flot sait suivre : il étire la matière au lieu de la déplacer. On recopie
# alors l'image de gauche — un palier franc vaut mieux qu'une image tordue,
# parce qu'un palier ne se remarque qu'en défilement lent alors qu'une
# déformation se voit tout le temps.
SEUIL_ECART = 18.0


def flot(a, b):
    """Déplacement de chaque pixel de a vers b."""
    ga = cv2.cvtColor(a, cv2.COLOR_BGR2GRAY)
    gb = cv2.cvtColor(b, cv2.COLOR_BGR2GRAY)
    dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
    return dis.calc(ga, gb, None)


def deplacer(img, f, t):
    """Applique une fraction t du flot f à l'image img."""
    h, w = img.shape[:2]
    gx, gy = np.meshgrid(np.arange(w, dtype=np.float32),
                         np.arange(h, dtype=np.float32))
    return cv2.remap(img, gx + f[..., 0] * t, gy + f[..., 1] * t,
                     cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)


def entre(a, b, t):
    """Image intermédiaire à la fraction t, vue des deux côtés.

    On avance depuis a ET on recule depuis b, puis on mélange en pondérant par
    la distance. Une seule direction laisserait un bord étiré du côté où la
    matière apparaît ; les deux se complètent."""
    fab, fba = flot(a, b), flot(b, a)
    va = deplacer(a, fab, t)
    vb = deplacer(b, fba, 1 - t)
    return cv2.addWeighted(va, 1 - t, vb, t, 0)


def main():
    fichiers = sorted(glob(os.path.join(DOSSIER, "*.jpg")))
    if not fichiers:
        sys.exit(f"aucune image dans {DOSSIER}")
    if FACTEUR < 2:
        sys.exit("facteur minimum : 2")

    print(f"{len(fichiers)} images · facteur {FACTEUR} -> "
          f"{(len(fichiers) - 1) * FACTEUR + 1} images")

    sortie = DOSSIER + "-interpole"
    shutil.rmtree(sortie, ignore_errors=True)
    os.makedirs(sortie)

    n, copiees = 0, 0
    precedente = cv2.imread(fichiers[0])
    for k in range(len(fichiers) - 1):
        suivante = cv2.imread(fichiers[k + 1])
        n += 1
        cv2.imwrite(os.path.join(sortie, f"f{n:04d}.jpg"), precedente,
                    [cv2.IMWRITE_JPEG_QUALITY, 94])

        ecart = float(np.abs(cv2.cvtColor(precedente, cv2.COLOR_BGR2GRAY).astype(np.float32)
                             - cv2.cvtColor(suivante, cv2.COLOR_BGR2GRAY).astype(np.float32)).mean())
        for j in range(1, FACTEUR):
            n += 1
            if ecart > SEUIL_ECART:
                img, copiees = precedente, copiees + 1
            else:
                img = entre(precedente, suivante, j / FACTEUR)
            cv2.imwrite(os.path.join(sortie, f"f{n:04d}.jpg"), img,
                        [cv2.IMWRITE_JPEG_QUALITY, 94])

        precedente = suivante
        if (k + 1) % 25 == 0:
            print(f"  {k + 1}/{len(fichiers) - 1}")

    n += 1
    cv2.imwrite(os.path.join(sortie, f"f{n:04d}.jpg"), precedente,
                [cv2.IMWRITE_JPEG_QUALITY, 94])

    poids = sum(os.path.getsize(os.path.join(sortie, f))
                for f in os.listdir(sortie)) / 1048576
    print(f"\nécrit {n} images dans {sortie} — {poids:.1f} Mo")
    if copiees:
        print(f"  {copiees} intermédiaire(s) recopiée(s) : écart trop grand pour "
              f"un flot — coupe ou passage derrière une masse")
    print(f"\npour l'employer : remplacer {DOSSIER} par ce dossier")


if __name__ == "__main__":
    main()
