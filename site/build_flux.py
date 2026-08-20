#!/usr/bin/env python3
"""
Construit la vitrine en FLUX : la page d'un côté, les images de l'autre.

C'est la version d'un vrai hébergement — ou d'un lancement en local — et
c'est la seule qui lève le plafond de poids. Repliée en un fichier unique la
page doit tenir sous quinze mégaoctets et demi, ce qui force DEUX renoncements
à la fois : 640 px de large, et 1 039 images sur les 1 440 disponibles.

Servies séparément, les images changent de nature :

  — le navigateur les demande en parallèle et les décode en code natif, hors
    du fil principal, au lieu de traverser une chaîne base64 en JavaScript ;
  — il ne charge que celles dont la fenêtre glissante a besoin, au lieu de
    tout avaler avant la première image ;
  — il les met en cache, donc une seconde visite ne retéléchargera rien ;
  — et le poids cesse d'être une limite : on livre les 1 440.

Le lecteur n'a rien à changer. Il possède déjà les deux voies : si la page ne
trouve pas de tableau embarqué, il va chercher les fichiers sur le disque. Ici
on se contente de NE PAS embarquer.

    usage : python3 build_flux.py [q=N] [large=N] [etroit=N] [parimage=N]
                                 [serie=NOM] [page]

« page » réécrit index.html sans réencoder les images. L'encodage prend
quarante minutes ; une correction du lecteur n'a pas à les payer.

MOINS D'IMAGES, BEAUCOUP PLUS GRANDES. C'est l'échange, et la première
version l'avait fait à l'envers.

Elle servait 1 440 images de 1280 px, soit 10,6 px de défilement par image.
À mille pixels par seconde — un défilement ordinaire — cela réclame
QUATRE-VINGT-QUATORZE images décodées par seconde. Le résultat se mesurait :
l'image demandée était absente du cache 86 à 91 % du temps, et la page ne
faisait que reposer la voisine. Illisible.

Le site qui servait de référence fait exactement l'inverse, vérifié sur son
serveur : 2560x1440 en WebP, 135 à 220 Ko l'image, environ 800 images, soit
33 px de défilement par image. Huit fois plus d'octets par image, trois fois
moins d'images. À mille pixels par seconde cela ne demande plus que TRENTE
décodages — la cadence du cinéma, celle au-delà de laquelle l'oeil ne
distingue plus rien.

C'est là qu'était l'erreur de raisonnement : croire que la densité fait la
fluidité. Au-delà d'une trentaine de changements d'image par seconde elle
n'achète plus rien de visible, mais elle continue de taxer le décodeur et la
mémoire — et elle se paye en définition, qui, elle, se voit.

`parimage` fixe donc la densité, et le nombre d'images s'en déduit de la
course mesurée. 33 par défaut, comme la référence.

Le décodage, mesuré à nouveau machine au repos — la première mesure avait été
prise pendant un encodage et annonçait des chiffres deux à trois fois trop
pessimistes, ce qui avait fait choisir 1280 à tort :

     640 px   1,78 ms l'image   562 images par seconde
    1280 px   5,38 ms l'image   186
    1600 px   7,46 ms l'image   134
    1920 px  11,73 ms l'image    85

À 33 px par image il faut 30 décodages par seconde : le 1920 passe largement.

Le portrait est servi moins large que le paysage, et pas par condescendance :
la toile d'un téléphone fait 585 px (390 points à 1,5 pixel physique, plafond
imposé dans la page), donc 1080 y est déjà bien au-dessus du un pour un. Et
c'est l'appareil où la mémoire se ferme sans prévenir.

Sortie : dist/flux/ — un dossier à déposer tel quel sur un hébergement, ou à
servir en local par `python3 -m http.server` depuis l'intérieur du dossier.
Ouvrir index.html directement en double-cliquant NE MARCHE PAS : le protocole
file:// interdit d'aller chercher les images voisines.
"""
import io
import os
import re
import shutil
import sys
from glob import glob
from multiprocessing import Pool

import numpy as np
from PIL import Image

SITE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(SITE, "ultra-motion.html")
OUT = os.path.join(SITE, "dist", "flux")


def _drapeau(nom, defaut):
    return next((int(a[len(nom):]) for a in sys.argv[1:] if a.startswith(nom)), defaut)


# q=55 et non 32 comme dans le fichier unique : là-bas chaque kilo-octet
# économisé achetait une image, ici il n'achète rien du tout.
#
# Et c'est le bout du chemin, pas un compromis. Fidélité à la source, mesurée
# sur huit images réparties sur la série, en 1920 px :
#
#     q45   26,5 Ko   42,5 dB
#     q55   36,5 Ko   43,5 dB
#     q65   47,8 Ko   44,3 dB
#     q80   86,2 Ko   45,6 dB
#
# Au-delà de quarante décibels on est dans le visuellement sans perte, et q45
# y était déjà. Monter à q80 coûterait 3,3 fois les octets pour trois
# décibels — pour rien de visible, et pour un décodage plus lent, qui lui se
# voit. On prend 55 comme marge et on s'arrête là : la compression n'est plus
# le maillon faible, la source l'est.
QUALITE = _drapeau("q=", 55)
# Réécrit seulement index.html, sans toucher aux images déjà encodées.
PAGE_SEULE = "page" in sys.argv[1:]
# Ne réencoder qu'une série, en gardant l'autre telle quelle. Vingt minutes
# d'encodeur ne se redépensent pas pour un réglage qui ne touche qu'un côté.
SEULE = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("serie=")), None)
# Densité voulue, en pixels de défilement par image. C'est ELLE qu'on choisit ;
# le nombre d'images en découle.
PAR_IMAGE = _drapeau("parimage=", 33)
SERIES = {
    "accueil":        dict(dossier="assets/film/accueil",        largeur=_drapeau("large=", 1920)),
    "accueil-etroit": dict(dossier="assets/film/accueil-etroit", largeur=_drapeau("etroit=", 720)),
}
# Les courses mesurées dans un navigateur. Ce sont elles qui, divisées par la
# densité voulue, donnent le nombre d'images à livrer.
COURSES = {"accueil": 15300, "accueil-etroit": 10297}
# Pas d'affûtage : les images viennent d'un agrandissement 4K qui l'a déjà
# fait, et mieux. Voir la note de build_ultra.py.
FORMAT = "AVIF"
VITESSE = 4


def _un(travail):
    chemin, largeur, cible = travail
    im = Image.open(chemin).convert("RGB")
    if im.width > largeur:
        im = im.resize((largeur, round(largeur * im.height / im.width)), Image.LANCZOS)
    tampon = io.BytesIO()
    im.save(tampon, FORMAT, quality=QUALITE, speed=VITESSE)
    octets = tampon.getvalue()
    # Extension .jpg mais contenu AVIF : le lecteur compose son chemin avec
    # .jpg, et un navigateur reconnaît le format aux octets, pas au nom.
    open(cible, "wb").write(octets)
    return len(octets)


def main():
    src = open(SOURCE, encoding="utf-8").read()
    if not PAGE_SEULE and not SEULE:
        shutil.rmtree(OUT, ignore_errors=True)
        os.makedirs(OUT)
    elif SEULE:
        shutil.rmtree(os.path.join(OUT, "assets", "film", SEULE), ignore_errors=True)
    elif not os.path.isdir(OUT):
        sys.exit(f"« page » suppose une construction existante : {OUT} est absent")

    comptes, total = {}, 0
    for nom, reg in SERIES.items():
        fichiers = sorted(glob(os.path.join(SITE, reg["dossier"], "*.jpg")))
        if not fichiers:
            print(f"  {nom:15s} absente — ignorée")
            continue
        # Sous-échantillonnage RÉGULIER sur toute la série. Prendre les N
        # premières donnerait une séquence qui s'arrête au premier tiers du
        # parcours ; il faut un pas constant pour que la vitesse le soit.
        voulu = max(round(COURSES.get(nom, len(fichiers) * PAR_IMAGE) / PAR_IMAGE), 2)
        if voulu < len(fichiers):
            idx = np.linspace(0, len(fichiers) - 1, voulu).round().astype(int)
            fichiers = [fichiers[i] for i in idx]
        cible = os.path.join(OUT, "assets", "film", nom)
        if PAGE_SEULE or (SEULE and nom != SEULE):
            comptes[nom] = len(os.listdir(cible))
            print(f"  {nom:15s} {comptes[nom]:4d} images déjà encodées")
            continue
        os.makedirs(cible)
        travaux = [(f, reg["largeur"], os.path.join(cible, f"f{i:04d}.jpg"))
                   for i, f in enumerate(fichiers, 1)]
        with Pool() as bassin:
            poids = sum(bassin.map(_un, travaux, chunksize=8))
        comptes[nom] = len(fichiers)
        total += poids
        dens = COURSES.get(nom, 0) / len(fichiers)
        print(f"  {nom:15s} {len(fichiers):4d} images · {poids/1048576:6.1f} Mo "
              f"({poids/len(fichiers)/1024:5.1f} Ko l'image, {reg['largeur']}px q{QUALITE})"
              + (f" · {dens:.1f} px de défilement par image" if dens else ""))

    if not comptes:
        sys.exit("aucune image : lancer d'abord film_reconstruire.py")

    # Les comptes écrits dans la page sont ceux du mode replié. En flux, c'est
    # le dossier qui fait foi : on les corrige, sinon le lecteur s'arrêterait au
    # compte d'origine et le reste du défilement resterait figé.
    for nom, n in comptes.items():
        # On compte les REMPLACEMENTS, pas les différences. Vérifier que le
        # texte a changé paraît équivalent et ne l'est pas : quand la page
        # porte déjà le bon compte — ce qui est le cas dès que le disque et le
        # fichier unique s'accordent — la substitution est un non-changement,
        # et le test criait à l'échec sur une opération parfaitement réussie.
        src, combien = re.subn(
            rf"(chemin: *'assets/film/{re.escape(nom)}/f', *images: *)\d+",
            rf"\g<1>{n}", src)
        if combien != 1:
            sys.exit(f"compte de {nom} : {combien} correspondance(s) dans la page "
                     f"au lieu d'une — lecteur modifié ?")

    # La feuille des fontes reste un fichier à part : elle est mise en cache une
    # fois pour toutes, et 216 Ko dans chaque page seraient 216 Ko à chaque
    # visite.
    os.makedirs(os.path.join(OUT, "assets", "fonts"), exist_ok=True)
    shutil.copy(os.path.join(SITE, "assets", "fonts", "ultra.css"),
                os.path.join(OUT, "assets", "fonts", "ultra.css"))

    open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(src)
    page = os.path.getsize(os.path.join(OUT, "index.html")) / 1024
    print(f"\nécrit {OUT}/")
    print(f"  index.html   {page:6.0f} Ko  <- ce que le visiteur télécharge d'abord")
    print(f"  images       {total/1048576:6.1f} Mo  <- demandées au fil du défilement")
    print(f"\n  pour l'essayer :  cd {OUT} && python3 -m http.server 8000")


if __name__ == "__main__":
    main()
