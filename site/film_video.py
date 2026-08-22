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

    serie : « large » (défaut, paysage), « accueil » (paysage, prologue de
            la vitrine) ou « etroit » (portrait,
            pour les téléphones — c'est un recadrage, pas une réduction :
            une composition pensée en 16:9 ne tient pas debout en 9:16)

Un plan peut être rogné dans le temps en suffixant son nom :

    plan.mp4@0-200      ne garde que les images 0 à 200
    plan.mp4@12-        jette les douze premières
    plan.mp4@-200       jette tout après la 200e

C'est indispensable sur une vidéo générée : les modèles finissent presque
toujours sur un gel d'une à deux secondes. Gardé tel quel, ce gel occupe le
même espace de défilement que le reste — un cinquième de la page où plus rien
ne bouge.

    python3 film_video.py plan.mp4 profil

mesure l'écart entre images consécutives, signale les coupes et dit où le
mouvement s'arrête. À lancer avant toute extraction.
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
def _decouper(arg):
    """« fichier.mp4@12-200 » -> (fichier, 12, 200). Bornes absentes : None."""
    chemin, _, plage = arg.partition("@")
    if not os.path.isfile(chemin):
        return None
    a, _, b = plage.partition("-") if plage else ("", "", "")
    return chemin, int(a) if a.strip() else None, int(b) if b.strip() else None


_args = sys.argv[1:]
SOURCES = [c for c in map(_decouper, _args) if c]
_reste = [a for a in _args if _decouper(a) is None]
if not SOURCES:
    sys.exit(__doc__)
PROFIL = "profil" in _reste
_reste = [a for a in _reste if a != "profil"]

IMAGES = int(_reste[0]) if len(_reste) > 0 else 150
LARGEUR = int(_reste[1]) if len(_reste) > 1 else 1440
SERIE = _reste[2] if len(_reste) > 2 else "large"

# « accueil » est le prologue de la vitrine du studio : même cadrage que
# « large », mais un dossier à part, pour que les deux séquences puissent
# coexister sans que l'une écrase l'autre.
# « transgold » : le premier client. Dossiers à part, pour que sa séquence et
# celle de la vitrine coexistent sans qu'aucune n'écrase l'autre — les deux
# doivent rester livrables en même temps.
FORMATS = {"large": 16 / 9, "etroit": 9 / 16,
           "accueil": 16 / 9, "accueil-etroit": 9 / 16,
           "transgold": 16 / 9, "transgold-etroit": 9 / 16}
if SERIE not in FORMATS:
    sys.exit(f"série inconnue : {SERIE} — attendu : {', '.join(FORMATS)}")
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


def inspecter(chemin, a, b):
    """Ouvre un plan et rend (capture, première image, dernière image)."""
    cap = cv2.VideoCapture(chemin)
    if not cap.isOpened():
        sys.exit(f"illisible : {chemin}")
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    debut = max(a or 0, 0)
    fin = min(b if b is not None else total - 1, total - 1)
    if fin <= debut:
        sys.exit(f"plage vide sur {chemin} : {debut}-{fin}")
    rogne = f"  → garde {debut}-{fin}" if (debut, fin) != (0, total - 1) else ""
    print(f"  {os.path.basename(chemin):28s} {total:4d} images · {fps:4.1f} i/s · "
          f"{w}×{h} · {total / fps if fps else 0:5.1f} s{rogne}")
    return cap, debut, fin


def profil(chemin):
    """Écart moyen entre images consécutives : coupes et zones mortes.

    Une coupe est un pic isolé très au-dessus du voisinage. Une zone morte est
    une traînée proche de zéro — typiquement le gel de fin. Les deux sont
    invisibles en lecture normale et ruineuses au défilement, où elles
    occupent quand même leur part entière de la page."""
    cap = cv2.VideoCapture(chemin)
    if not cap.isOpened():
        sys.exit(f"illisible : {chemin}")
    ecarts, precedent = [], None
    while True:
        ok, img = cap.read()
        if not ok:
            break
        g = cv2.cvtColor(cv2.resize(img, (320, 180)), cv2.COLOR_BGR2GRAY).astype(np.float32)
        if precedent is not None:
            ecarts.append(float(np.abs(g - precedent).mean()))
        precedent = g
    cap.release()
    if not ecarts:
        sys.exit("aucune image lisible")

    d = np.array(ecarts)
    print(f"\n{os.path.basename(chemin)} — {len(d) + 1} images, "
          f"mouvement moyen {d.mean():.2f}")
    pas = max(len(d) // 24, 1)
    for i in range(0, len(d), pas):
        t = d[i:i + pas]
        print(f"  {i:4d}  {t.mean():6.2f}  {'#' * min(int(t.mean() * 5), 60)}")

    coupes = [i + 1 for i, v in enumerate(d) if v > d.mean() + 5 * d.std()]
    print(f"\ncoupes : {coupes if coupes else 'aucune'}")
    if coupes:
        print("  une coupe se remonte aussi mal qu'elle se descend. Si elle tombe")
        print("  là où un texte change, elle passe pour un changement de chapitre.")

    vivant = [i for i, v in enumerate(d) if v > 0.6]
    if vivant and vivant[-1] < len(d) - 4:
        print(f"\ngel de fin : plus rien ne bouge après l'image {vivant[-1]} "
              f"({len(d) - vivant[-1]} images)")
        print(f"  suggestion : {os.path.basename(chemin)}@{vivant[0]}-{vivant[-1] + 9}")


def main():
    if PROFIL:
        for chemin, _, _ in SOURCES:
            profil(chemin)
        return

    print(f"{len(SOURCES)} plan(s) :")
    plans = [inspecter(*s) for s in SOURCES]
    durees = [f - d + 1 for _, d, f in plans]
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
    for p, ((cap, debut, fin), quota) in enumerate(zip(plans, quotas)):
        if quota <= 0:
            cap.release()
            continue
        # Les plans enchaînés démarrent sur l'image de fin du précédent : la
        # reprendre la ferait tenir deux fois plus longtemps à l'écran, et le
        # défilement buterait à chaque jointure.
        if p > 0 and fin > debut:
            debut += 1
        rangs = np.linspace(debut, fin, quota).round().astype(int)

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
    # Fourchette mesurée : 20 Ko l'image sur une prise de vue réelle à fond
    # doux, 46 Ko sur nos rendus 3D, plus contrastés et plus détaillés. C'est
    # le chiffre qui décide de la longueur d'une chorégraphie, pas le temps
    # de calcul — d'où la fourchette plutôt qu'un nombre faussement précis.
    print(f"  soit {ecrites * 20 / 1024:.1f} à {ecrites * 46 / 1024:.1f} Mo une fois livrées, "
          f"selon le contraste de l'image")
    print("\nensuite : python3 build_film.py 72 1280")


if __name__ == "__main__":
    main()
