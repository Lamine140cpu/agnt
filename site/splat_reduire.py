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

    usage : python3 splat_reduire.py source nom [nombre] [rayon]

    La source est un fichier .splat, ou un dossier au format SOG
    (meta.json et ses images WebP).
"""
import os
import struct
import sys

import numpy as np

SITE = os.path.dirname(os.path.abspath(__file__))
SORTIE = os.path.join(SITE, "assets", "splats")

VOISINS = 6          # rang du voisin dont la distance sert de mesure de densité
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


def lire_sog(dossier):
    """Lit une scène au format SOG — celui de SuperSplat et de PlayCanvas.

    Cinq images WebP et un meta.json, au lieu d'un tableau de flottants : les
    positions y sont sur seize bits dans un espace logarithmique, les rotations
    en « trois plus petites composantes », les échelles et les couleurs par
    index dans un dictionnaire de 256 entrées. Vingt fois plus compact qu'un
    .ply, d'où son intérêt — et d'où ce décodeur.

    Les harmoniques sphériques d'ordre supérieur (shN) sont ignorées : elles ne
    décrivent que la variation de couleur selon l'angle de vue, dont le rendu
    ici ne tient pas compte.
    """
    import json
    from PIL import Image

    meta = json.load(open(os.path.join(dossier, "meta.json")))
    n = meta["count"]

    def plan(nom):
        im = np.asarray(Image.open(os.path.join(dossier, nom)).convert("RGBA"))
        return im.reshape(-1, 4)[:n]

    ml, mu = plan("means_l.webp"), plan("means_u.webp")
    q16 = (mu[:, :3].astype(np.uint32) << 8) | ml[:, :3].astype(np.uint32)
    mins = np.array(meta["means"]["mins"], np.float64)
    maxs = np.array(meta["means"]["maxs"], np.float64)
    lin = mins + (q16 / 65535.0) * (maxs - mins)
    # le logarithme est symétrique : on le défait des deux côtés de zéro
    pos = (np.sign(lin) * (np.exp(np.abs(lin)) - 1)).astype(np.float32)

    ech = np.exp(np.array(meta["scales"]["codebook"], np.float32)[plan("scales.webp")[:, :3]])

    sh0 = plan("sh0.webp")
    cb = np.array(meta["sh0"]["codebook"], np.float32)
    SH_C0 = 0.28209479177387814
    rgb = np.clip((0.5 + cb[sh0[:, :3]] * SH_C0) * 255.0, 0, 255)
    col = np.concatenate([rgb, sh0[:, 3:4].astype(np.float32)], axis=1).astype(np.uint8)

    qt = plan("quats.webp")
    abc = (qt[:, :3].astype(np.float32) / 255.0 - 0.5) * 2.0 / np.sqrt(2.0)
    reste = np.sqrt(np.maximum(0.0, 1.0 - (abc ** 2).sum(1)))
    mode = np.clip(qt[:, 3].astype(np.int32) - 252, 0, 3)
    quat = np.zeros((n, 4), np.float32)
    # les trois composantes conservées gardent l'ordre (w,x,y,z), celle qui
    # manque — la plus grande — reprend sa place, indiquée par le mode
    for m in range(4):
        ligne = mode == m
        gardees = [k for k in range(4) if k != m]
        for j, k in enumerate(gardees):
            quat[ligne, k] = abc[ligne, j]
        quat[ligne, m] = reste[ligne]

    return {
        "pos": pos,
        "ech": ech.astype(np.float32),
        "col": col,
        "rot": np.clip(quat * 128 + 128, 0, 255).astype(np.uint8),
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

    g = lire_sog(source) if os.path.isdir(source) else lire_splat(source)
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

    # 3. Les flotteurs.
    #
    #    Une reconstruction laisse toujours des gaussiennes suspendues dans le
    #    vide, souvent claires et bien visibles : ce sont des reflets ou des
    #    passants que le calcul n'a pas su placer. Elles se reconnaissent à ce
    #    qu'elles n'ont pas de voisines — la matière réelle, elle, est dense.
    from scipy.spatial import cKDTree
    arbre = cKDTree(g["pos"])
    voisin, _ = arbre.query(g["pos"], k=[VOISINS], workers=-1)
    voisin = voisin[:, 0]
    # Le seuil se prend sur la médiane, pas sur un centile haut : les flotteurs
    # forment des amas — ils se tiennent compagnie — et un centile calculé sur
    # l'ensemble les compterait comme normaux.
    seuil = np.median(voisin) * 6.0
    dense = voisin < seuil
    print(f"  flotteurs écartés : {int((~dense).sum()):,}")
    g = {k: v[dense] for k, v in g.items()}
    n = int(dense.sum())

    # 4. Redresser la scène.
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

    # Restent les amas de flotteurs, que la densité ne distingue pas : ils se
    # tiennent groupés. Mais ils ont trois traits communs — clairs, larges, et
    # suspendus dans le tiers haut de la scène, là où il n'y a rien à décrire
    # qu'un plafond. Les trois réunis ne se rencontrent pas dans la matière.
    y = g["pos"][:, 1]
    clair = g["col"][:, :3].mean(axis=1) > 190
    large = np.cbrt(np.prod(np.maximum(g["ech"], 1e-8), axis=1)) > np.percentile(
        np.cbrt(np.prod(np.maximum(g["ech"], 1e-8), axis=1)), 88)
    en_l_air = y > np.percentile(y, 72)
    fantome = clair & large & en_l_air
    print(f"  amas clairs écartés : {int(fantome.sum()):,}")
    g = {k: v[~fantome] for k, v in g.items()}
    n = int((~fantome).sum())

    # 5. quantification
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
    lourd = (sum(os.path.getsize(os.path.join(source, f)) for f in os.listdir(source))
             if os.path.isdir(source) else os.path.getsize(source))
    print(f"{nom}.ums : {n:,} gaussiennes sur {n0:,} — {poids/1048576:.1f} Mo "
          f"(source {lourd/1048576:.1f} Mo)")
    print(f"  boîte {np.round(bmin,2)} → {np.round(bmax,2)}")
    print(f"  centre de la scène {np.round((bmin+bmax)/2, 2)}")


if __name__ == "__main__":
    main()
