#!/usr/bin/env python3
"""
Replie la vitrine du studio en un seul fichier.

Deux choses à embarquer, pas une seule — c'est ce qui distingue cette
construction de celle du film :

  1. la séquence du prologue, déposée dans `window.__FILM.accueil` ;
  2. les vignettes éventuelles, qui sont des <img> pointant vers le disque.
     Servies telles quelles dans un fichier unique elles ne se résolvent plus,
     et une politique de sécurité stricte les bloquerait de toute façon. Elles
     deviennent donc des adresses `data:`.

    usage : python3 build_ultra.py [budget_Mo] [artefact] [q=N] [net=N] [mini=N]

C'EST LE BUDGET QUI COMMANDE, PAS UN PLAFOND ÉCRIT À LA MAIN.

La version précédente portait « 580 images en paysage, 360 en portrait »
en dur, avec un commentaire affirmant que cela donnait 4,7 px de défilement
par image. Le chiffre était faux d'un facteur cinq : la course du prologue
a été mesurée dans un navigateur à 15 300 px sur écran large et 10 297 px
sur téléphone, ce qui met 580 images à 26,4 px l'une et 360 à 28,6. C'est
exactement le grain que l'on voyait.

Le plafond est donc remplacé par un calcul en trois temps :

  1. on sonde — on encode un échantillon réparti sur toute la série, ce qui
     donne le coût MOYEN d'une image dans cette configuration ;
  2. on résout — le budget disponible, divisé par ce coût, donne le nombre
     d'images ; la répartition entre les deux séries suit le rapport de leurs
     courses, pour que la densité soit la MÊME sur les deux écrans ;
  3. on encode, en parallèle.

Un budget plus généreux, un écran plus grand, un plan de plus : le compte
suit tout seul. Personne n'a à retoucher un nombre.

Deux sorties, parce que deux hébergements attendent l'inverse l'un de l'autre :

  dist/ultra-motion.html           document complet — livré, ou ouvert d'un
                                   double-clic. Il lui faut son <!DOCTYPE>,
                                   son <html>, son <meta viewport>.

  dist/ultra-motion-artefact.html  fragment, écrit seulement avec « artefact ».
                                   L'hébergement fournit l'enveloppe ; les
                                   balises de structure y feraient doublon.
"""
import base64
import io
import json
import os
import re
import sys
from glob import glob
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageFilter

SITE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(SITE, "ultra-motion.html")
OUT = os.path.join(SITE, "dist", "ultra-motion.html")
OUT_ARTEFACT = os.path.join(SITE, "dist", "ultra-motion-artefact.html")


def _drapeau(nom, defaut):
    return next((int(a[len(nom):]) for a in sys.argv[1:] if a.startswith(nom)), defaut)


_libres = [a for a in sys.argv[1:] if a != "artefact" and "=" not in a]
ARTEFACT = "artefact" in sys.argv[1:]

# 15,6 Mo : la limite d'un artefact est 16 Mo pour la page RENDUE. On garde
# quatre cents kilo-octets de marge — le compte d'images est calculé sur une
# moyenne, et une série peut coûter un peu plus que son échantillon.
BUDGET = float(_libres[0]) if _libres else 15.6

# Qualité et netteté vérifiées à l'œil, pas choisies au hasard : la même image
# encodée à 760 px q45 et à 640 px q34, puis RAMENÉE À LA TAILLE QUE LA TOILE
# AFFICHE VRAIMENT (2 880 px sur un écran large, 585 sur un téléphone), est
# indiscernable. L'écart de définition disparaît dans l'agrandissement — la
# toile fait déjà quatre fois la largeur de la source. Il ne disparaît pas du
# poids : 9,7 Ko contre 5,6. Ces quatre kilo-octets par image achètent des
# images, et ce sont elles qui se voient.
QUALITE = _drapeau("q=", 34)
# Masque flou, appliqué APRÈS la réduction — qui est elle-même adoucissante.
# Seuil 3 : on ne renforce que ce qui est déjà un contour, pour ne pas réveiller
# le bruit de compression des aplats. Il a un prix mesuré : à 640 px q35 il
# coûte 5,50 -> 5,94 Ko l'image entre net=0 et net=45, soit huit pour cent du
# poids. On le ramène à 20, qui garde l'essentiel du mordant pour trois pour
# cent — le reste part en images.
NETTETE = _drapeau("net=", 20)
# Garde-fou : si la configuration ne permet plus d'atteindre ce compte, mieux
# vaut s'arrêter en le disant que livrer une séquence hachée sans prévenir.
MINI = _drapeau("mini=", 1000)

# Deux séries : le paysage pour les écrans larges, le portrait pour les
# téléphones tenus debout. La seconde n'est pas la première rognée — deux
# des plans ont été tournés nativement en 9:16.
#
# `course` est la distance de défilement que la série doit couvrir, mesurée
# dans un navigateur sur la mise en page correspondante (1600x900 et 390x844).
# C'est elle qui décide du partage : deux séries qui couvrent des distances
# différentes n'ont pas besoin du même nombre d'images pour paraître aussi
# fluides. À densité égale, le portrait en demande un tiers de moins.
#
# `largeur` n'est pas la même pour les deux, et pas pour la raison qu'on
# croit. Ce n'est pas que le téléphone mérite moins : c'est qu'il agrandit
# moins. Une toile de téléphone fait 585 px de large (390 points à 1,5 pixel
# physique, plafond imposé dans la page) — une source de 480 px y est
# agrandie de 1,2 fois, presque du un pour un. Sur un écran large la toile
# fait 2 880 px et une source de 640 px y est agrandie de 4,5 fois : la
# définition y est déjà perdue, autant ne pas la payer.
SERIES = {
    "accueil":        dict(dossier="assets/film/accueil",        largeur=640, course=15300),
    "accueil-etroit": dict(dossier="assets/film/accueil-etroit", largeur=480, course=10297),
}

# AVIF plutôt que WebP, sur mesure et non sur réputation. À qualité visuelle
# équivalente il pèse un tiers de moins, ce qui achète des images
# supplémentaires — et, contre toute attente, il se décode PLUS VITE ici :
# 7,06 ms contre 10,40 ms par image dans un navigateur. Son codec est plus
# lourd, mais comme il permet de descendre en définition à qualité égale, il y
# a moins de pixels à produire, et c'est ce terme-là qui l'emporte.
FORMAT = "AVIF"
# L'encodeur cherche longtemps : on construit une fois, la page est servie des
# milliers de fois. Mais l'effort a un rendement qui s'effondre — mesuré à
# 640 px q35 : speed=4 donne 5,94 Ko en 0,42 s, speed=2 donne 5,84 Ko en 1,11 s.
# Un virgule sept pour cent de gain pour presque trois fois le temps : non.
VITESSE = 4
# Le sous-échantillonnage de la teinte n'est pas décidé ici mais par l'encodeur
# (4:2:0 par défaut), et c'est le bon choix pour une image agrandie quatre fois.


def encoder_image(im, largeur, qualite):
    """Réduit, affûte, encode. Rend les octets."""
    if im.width > largeur:
        im = im.resize((largeur, round(largeur * im.height / im.width)), Image.LANCZOS)
    if NETTETE:
        im = im.filter(ImageFilter.UnsharpMask(radius=1.1, percent=NETTETE, threshold=3))
    tampon = io.BytesIO()
    reglages = {"speed": VITESSE} if FORMAT == "AVIF" else {"method": 6}
    im.save(tampon, FORMAT, quality=qualite, **reglages)
    return tampon.getvalue()


def en_webp(im, largeur, qualite):        # nom conservé : appelé pour les vignettes
    return encoder_image(im, largeur, qualite)


def _un(travail):
    """Encode un fichier. Vit au premier plan du module pour être expédiable
    à un autre processus — une fermeture ne se sérialise pas."""
    chemin, largeur = travail
    return encoder_image(Image.open(chemin).convert("RGB"), largeur, QUALITE)


def repartir(fichiers, combien):
    """Prélève `combien` fichiers RÉPARTIS sur toute la série.

    Prendre les N premiers donnerait une séquence qui s'arrête au quart du
    parcours ; prélever au hasard donnerait une vitesse qui bafouille. Seul un
    pas constant garde le mouvement constant."""
    if combien >= len(fichiers):
        return list(fichiers)
    idx = np.linspace(0, len(fichiers) - 1, combien).round().astype(int)
    return [fichiers[i] for i in idx]


def sonder(fichiers, largeur, echantillon=16):
    """Coût moyen d'une image, mesuré et non supposé.

    Un échantillon RÉPARTI, pas les seize premières : un plan de nuit et un
    plan de gravier ne coûtent pas le même prix, et c'est la moyenne sur toute
    la série qui décide du compte."""
    lot = repartir(fichiers, echantillon)
    with Pool() as p:
        tailles = [len(o) for o in p.map(_un, [(f, largeur) for f in lot])]
    return sum(tailles) / len(tailles)


def sequence(nom, fichiers, largeur, combien):
    """Encode `combien` images réparties, en parallèle. Rend les chaînes base64."""
    lot = repartir(fichiers, combien)
    avant = sum(os.path.getsize(f) for f in lot)
    with Pool() as p:
        octets = p.map(_un, [(f, largeur) for f in lot], chunksize=8)
    apres = sum(len(o) for o in octets)
    course = SERIES[nom]["course"]
    print(f"  {nom:15s} {len(lot):4d} images · {avant/1048576:5.1f} Mo JPEG -> "
          f"{apres/1048576:5.2f} Mo {FORMAT} {largeur}px q{QUALITE} "
          f"({apres/len(lot)/1024:4.1f} Ko/image) · "
          f"{course/max(len(lot)-1,1):4.1f} px de défilement par image")
    return [base64.b64encode(o).decode() for o in octets], apres


def vignettes(src):
    """Remplace chaque <img src="assets/..."> par son adresse data:."""
    poids = 0

    def remplacer(m):
        nonlocal poids
        chemin = os.path.join(SITE, m.group(1))
        if not os.path.exists(chemin):
            print(f"  ATTENTION : vignette absente — {m.group(1)}")
            return m.group(0)
        # 1100 px : ces images ne dépassent jamais la moitié de l'écran, les
        # servir en 1600 serait payer une définition que personne ne voit.
        octets = en_webp(Image.open(chemin).convert("RGB"), 1100, QUALITE)
        poids += len(octets)
        return ('src="data:image/webp;base64,'
                + base64.b64encode(octets).decode() + '"')

    src = re.sub(r'src="(assets/[^"]+)"', remplacer, src)
    if poids:
        print(f"  vignettes {poids/1048576:5.2f} Mo")
    return src, poids


def fontes(src):
    """Remplace le <link> vers la feuille des fontes par son contenu.

    Elle contient déjà les fontes en adresses `data:` — il ne reste qu'à la
    coller. Une feuille externe dans un fichier unique ne se résoudrait pas,
    et la page retomberait sur Georgia sans rien dire."""
    def remplacer(m):
        chemin = os.path.join(SITE, m.group(1))
        if not os.path.exists(chemin):
            sys.exit(f"feuille de fontes absente : {m.group(1)}\n"
                     f"  lancer d'abord : python3 fontes_locales.py")
        contenu = open(chemin, encoding="utf-8").read()
        print(f"  fontes    {len(contenu)/1048576:5.2f} Mo")
        return "<style>\n" + contenu + "</style>"

    return re.sub(r'<link rel="stylesheet" href="(assets/[^"]+\.css)">', remplacer, src)


def compter(disponible, couts):
    """Combien d'images de chaque série tiennent dans `disponible` octets ?

    À densité égale, une série couvrant une course deux fois plus courte
    demande deux fois moins d'images. On fixe donc une inconnue — la densité —
    et on la résout :

        somme sur les séries de  (course / densité) * coût  =  disponible

    d'où densité = somme(course * coût) / disponible, en pixels de défilement
    par image. Le même grain sur les deux écrans, quel que soit le prix de
    l'une ou de l'autre."""
    densite = sum(SERIES[n]["course"] * c for n, c in couts.items()) / disponible
    return {n: max(round(SERIES[n]["course"] / densite), 2) for n in couts}, densite


def main():
    src = open(SOURCE, encoding="utf-8").read()
    src, poids_vig = vignettes(src)
    src = fontes(src)

    dispo = {}
    for nom, reg in SERIES.items():
        f = sorted(glob(os.path.join(SITE, reg["dossier"], "*.jpg")))
        if f:
            dispo[nom] = f
        else:
            print(f"  {nom:15s} absente — ignorée")
    if not dispo:
        sys.exit("aucune image : lancer d'abord film_video.py")

    # Ce que la page pèse SANS les images : le document, les fontes recopiées,
    # les vignettes. C'est cela qu'il faut retrancher du budget, sinon on
    # dépasse de la taille des fontes — deux cent vingt kilo-octets.
    fixe = len(src.encode()) + len('<script>window.__FILM = {};</script>\n')
    budget = round(BUDGET * 1048576)
    if fixe >= budget:
        sys.exit(f"le document seul dépasse déjà le budget ({fixe/1048576:.2f} Mo)")
    # Le base64 gonfle de quatre tiers ; s'y ajoutent les guillemets et la
    # virgule de chaque entrée, plus le nom de la série.
    place = (budget - fixe) * 3 // 4 - sum(len(n) + 8 for n in dispo)

    print(f"budget {BUDGET:.1f} Mo · document et fontes {fixe/1048576:.2f} Mo · "
          f"reste {place/1048576:.2f} Mo d'images\nsondage…")
    couts = {n: sonder(dispo[n], SERIES[n]["largeur"]) for n in dispo}
    for n, c in couts.items():
        print(f"  {n:15s} {c/1024:4.1f} Ko l'image (sondé sur 16)")

    comptes, densite = compter(place, couts)
    total = sum(comptes.values())
    print(f"  -> {total} images au total, {densite:.1f} px de défilement "
          f"par image sur les deux écrans")
    for n in comptes:
        comptes[n] = min(comptes[n], len(dispo[n]))
    if max(comptes.values()) < MINI:
        sys.exit(f"la série la plus longue n'atteint que {max(comptes.values())} "
                 f"images, seuil demandé {MINI} — baisser q= ou monter le budget")

    print("encodage…")
    film, poids_seq = {}, 0
    for nom in dispo:
        images, poids = sequence(nom, dispo[nom], SERIES[nom]["largeur"], comptes[nom])
        film[nom] = images
        poids_seq += poids

    charge = ("<script>window.__FILM = "
              + json.dumps(film, separators=(",", ":")) + ";</script>\n")

    # On garde le document ENTIER et on injecte avant </head>. Ne recopier que
    # l'intérieur de <head> et <body> — comme le faisait la première version du
    # film — produit un fragment : sans DOCTYPE le navigateur passe en mode
    # « quirks », et sans <meta viewport> un téléphone rend la page sur 980 px.
    # Injecter APRÈS le <title> le laisse dans les premiers kilo-octets, seuls
    # lus pour le nommer.
    if "</head>" not in src:
        sys.exit("ultra-motion.html : </head> introuvable")
    page = src.replace("</head>", charge + "</head>", 1)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w", encoding="utf-8").write(page)
    poids = len(page.encode()) / 1048576
    print(f"\nécrit {OUT} — {poids:.2f} Mo · {sum(len(v) for v in film.values())} images")

    if ARTEFACT:
        tete = page.split("<head>", 1)[1].split("</head>", 1)[0]
        corps = page.split("<body>", 1)[1].rsplit("</body>", 1)[0]
        fragment = tete.strip() + "\n" + corps.strip() + "\n"
        open(OUT_ARTEFACT, "w", encoding="utf-8").write(fragment)
        print(f"écrit {OUT_ARTEFACT} — {len(fragment.encode())/1048576:.2f} Mo (fragment)")

    if poids > 15.9:
        print("  ATTENTION : au-delà de la limite d'un artefact, baisser le budget")


if __name__ == "__main__":
    main()
