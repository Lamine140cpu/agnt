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


def matrices_rotation(quat):
    """uint8 (w,x,y,z) -> matrices de rotation, en lot."""
    q = (quat.astype(np.float32) - 128.0) / 128.0
    q /= np.maximum(np.linalg.norm(q, axis=1, keepdims=True), 1e-8)
    w, x, y, z = q[:, 0], q[:, 1], q[:, 2], q[:, 3]
    return np.stack([
        1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y),
        2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x),
        2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y),
    ], axis=1).reshape(-1, 3, 3)


def redresser(g):
    """Aligne la verticale de la scène sur +Y, positions et rotations comprises."""
    R = matrices_rotation(g["rot"])
    plat = np.argmin(g["ech"], axis=1)                     # l'axe le plus mince
    normales = R[np.arange(len(R)), :, plat]

    tri = np.sort(g["ech"], axis=1)
    aire = tri[:, 1] * tri[:, 2] * (g["col"][:, 3] / 255.0)   # les deux grands axes
    M = np.einsum("i,ij,ik->jk", aire, normales, normales)
    axes = np.linalg.eigh(M)[1].T

    # La direction la plus représentée n'est pas toujours la verticale : un mur
    # de bibliothèque peut totaliser plus de surface que le sol. Entre les trois
    # axes propres, on retient celui selon lequel la scène est la moins étendue
    # — une pièce est toujours plus large que haute.
    etendues = [np.percentile(g["pos"] @ a, 99) - np.percentile(g["pos"] @ a, 1)
                for a in axes]
    haut = axes[int(np.argmin(etendues))]

    # Reste le sens : l'axe est trouvé, pas orienté. Le sol est le plan
    # horizontal le plus dense d'une pièce, et il est sous le reste — si le pic
    # de densité tombe au-dessus du milieu, l'axe pointe vers le bas.
    proj = g["pos"] @ haut
    hist, bords = np.histogram(proj, bins=120)
    pic = (bords[np.argmax(hist)] + bords[np.argmax(hist) + 1]) / 2
    if pic > np.median(proj):
        haut = -haut

    cible = np.array([0.0, 1.0, 0.0])
    axe = np.cross(haut, cible)
    sin, cos = np.linalg.norm(axe), float(haut @ cible)
    if sin < 1e-6:
        return g, haut
    axe = axe / sin
    K = np.array([[0, -axe[2], axe[1]], [axe[2], 0, -axe[0]], [-axe[1], axe[0], 0]])
    Rot = np.eye(3) + K * sin + K @ K * (1 - cos)

    g["pos"] = g["pos"] @ Rot.T
    # la rotation se compose : R' = Rot · R, réencodée en quaternion
    Rn = np.einsum("ij,njk->nik", Rot, R)
    tr = Rn[:, 0, 0] + Rn[:, 1, 1] + Rn[:, 2, 2]
    w = np.sqrt(np.maximum(1 + tr, 0)) / 2
    d = np.maximum(4 * w, 1e-8)
    q = np.stack([w,
                  (Rn[:, 2, 1] - Rn[:, 1, 2]) / d,
                  (Rn[:, 0, 2] - Rn[:, 2, 0]) / d,
                  (Rn[:, 1, 0] - Rn[:, 0, 1]) / d], axis=1)
    q /= np.maximum(np.linalg.norm(q, axis=1, keepdims=True), 1e-8)
    g["rot"] = np.clip(q * 128 + 128, 0, 255).astype(np.uint8)
    return g, haut


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

    # 3. Redresser la scène.
    #
    #    Une reconstruction photogrammétrique sort dans le repère qu'a trouvé le
    #    calcul de pose, sans rapport avec la verticale : le sol penche, et rien
    #    ne paraît plus faux qu'une pièce de travers.
    #
    #    La verticale se lit dans les gaussiennes elles-mêmes. Celles qui
    #    reposent sur une surface plane sont des disques, dont le plus petit axe
    #    est la normale à cette surface. Dans une pièce, le sol et le plafond
    #    totalisent plus de surface que n'importe quel mur : la direction
    #    dominante de ces normales est la verticale. On la prend comme vecteur
    #    propre principal de la matrice des normales — ce qui évite d'avoir à
    #    leur choisir un sens.
    g, haut = redresser(g)
    print(f"  verticale trouvée : {np.round(haut, 3)}")

    # 4. quantification
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
