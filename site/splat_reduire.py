#!/usr/bin/env python3
"""
Réduit et compacte une scène en splats gaussiens pour la livrer dans une page.

Une scène telle qu'elle sort d'un entraînement pèse une cinquantaine de
mégaoctets pour un million et demi de gaussiennes, en flottants simple
précision. C'est le format d'un fichier de travail, pas celui d'un site.

Deux opérations, donc :

**On élague.** Les scènes capturées portent un halo de gaussiennes lointaines
qui reconstruit ce qu'on apercevait par la fenêtre ; on s'en tient à une sphère
autour du sujet. Puis on garde les plus contributives — une gaussienne compte à
l'écran par son opacité et par sa surface, pas par son existence.

**On quantifie.** Les positions tiennent dans deux octets par axe rapportées à
la boîte englobante, les échelles dans un octet en échelle logarithmique.
Trente-deux octets par gaussienne tombent à dix-sept, sans différence visible.

    usage : python3 splat_reduire.py source.splat nom [nombre] [rayon]
"""
import os
import struct
import sys

import numpy as np

SITE = os.path.dirname(os.path.abspath(__file__))
SORTIE = os.path.join(SITE, "assets", "splats")

MAGIC = b"UMSP"
VERSION = 1


def lire_splat(chemin):
    """Format .splat : 32 octets par gaussienne — position, échelle, RGBA, quaternion."""
    brut = np.fromfile(chemin, dtype=np.uint8)
    if brut.size % 32:
        sys.exit(f"{chemin} : taille non multiple de 32, ce n'est pas un .splat")
    d = brut.reshape(-1, 32)
    n = len(d)
    return {
        "pos": np.frombuffer(d[:, 0:12].tobytes(), dtype=np.float32).reshape(n, 3),
        "ech": np.frombuffer(d[:, 12:24].tobytes(), dtype=np.float32).reshape(n, 3),
        "col": d[:, 24:28].copy(),
        "rot": d[:, 28:32].copy(),
    }


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__.strip().splitlines()[-1])
    source, nom = sys.argv[1], sys.argv[2]
    garder = int(sys.argv[3]) if len(sys.argv) > 3 else 400_000
    rayon = float(sys.argv[4]) if len(sys.argv) > 4 else 7.0

    g = lire_splat(source)
    n0 = len(g["pos"])

    # 1. l'arrière-plan lointain, reconstruit à travers les ouvertures
    centre = np.median(g["pos"], axis=0)
    proche = np.linalg.norm(g["pos"] - centre, axis=1) < rayon
    g = {k: v[proche] for k, v in g.items()}

    # 2. Les quasi-transparentes ne se voient pas, et les énormes ne sont que du
    #    remplissage. On écarte les deux, puis on tire au hasard dans le reste.
    #
    #    Garder « les plus contributives » paraissait plus fin : c'était une
    #    erreur. Trier par opacité multipliée par la taille revient à garder les
    #    plus grosses, c'est-à-dire les blocs de fond, et à jeter précisément le
    #    détail qu'on regarde. Un tirage uniforme conserve la distribution.
    alpha = g["col"][:, 3].astype(np.float32) / 255.0
    taille = np.cbrt(np.prod(np.maximum(g["ech"], 1e-8), axis=1))
    utile = (alpha > 0.06) & (taille < np.percentile(taille, 99.5))
    indices = np.flatnonzero(utile)
    if len(indices) > garder:
        indices = np.random.default_rng(1).choice(indices, garder, replace=False)
    indices.sort()                    # l'ordre du fichier, meilleur pour le cache
    g = {k: v[indices] for k, v in g.items()}
    n = len(indices)

    # 3. quantification
    bmin = g["pos"].min(axis=0)
    bmax = g["pos"].max(axis=0)
    etendue = np.maximum(bmax - bmin, 1e-6)
    pos = np.clip((g["pos"] - bmin) / etendue * 65535.0, 0, 65535).astype(np.uint16)

    lech = np.log(np.maximum(g["ech"], 1e-8))
    lmin, lmax = float(lech.min()), float(lech.max())
    ech = np.clip((lech - lmin) / (lmax - lmin) * 255.0, 0, 255).astype(np.uint8)

    os.makedirs(SORTIE, exist_ok=True)
    chemin = os.path.join(SORTIE, f"{nom}.ums")
    with open(chemin, "wb") as f:
        f.write(MAGIC)
        f.write(struct.pack("<II", VERSION, n))
        f.write(struct.pack("<6f", *bmin, *bmax))
        f.write(struct.pack("<2f", lmin, lmax))
        # entrelacé : une gaussienne par bloc de 17 octets, comme à la lecture
        bloc = np.empty((n, 17), dtype=np.uint8)
        bloc[:, 0:6] = pos.view(np.uint8).reshape(n, 6)
        bloc[:, 6:9] = ech
        bloc[:, 9:13] = g["col"]
        bloc[:, 13:17] = g["rot"]
        f.write(bloc.tobytes())

    poids = os.path.getsize(chemin)
    print(f"{nom}.ums : {n:,} gaussiennes sur {n0:,} — {poids/1048576:.1f} Mo "
          f"(source {os.path.getsize(source)/1048576:.1f} Mo)")
    print(f"  boîte {np.round(bmin,2)} → {np.round(bmax,2)}")
    print(f"  centre de la scène {np.round((bmin+bmax)/2, 2)}")


if __name__ == "__main__":
    main()
