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

    usage : python3 build_flux.py [q=N] [large=N] [etroit=N]

CE QUI DÉCIDE DE LA DÉFINITION N'EST PAS LE POIDS, C'EST LE DÉCODAGE.

Sans plafond de poids on pourrait servir le 1920 que porte le disque. On ne
le fait pas, et la raison est mesurée dans un vrai navigateur, sur soixante
images décodées en parallèle par `createImageBitmap` :

     640 px   1,89 ms l'image   529 images par seconde
    1280 px  12,39 ms l'image    81
    1600 px  26,66 ms l'image    38
    1920 px  29,76 ms l'image    34

Un défilement ordinaire consomme entre 70 et 100 images par seconde. À 1920
le navigateur en fournit 34 : il resterait bloqué sur la même image un tiers
du temps. 1280 est donc le plafond praticable — et c'est déjà 2,5 fois
d'agrandissement sur une toile de bureau au lieu de 5.

Le portrait est servi à 720 px et non 1280 : la toile d'un téléphone fait
585 px (390 points à 1,5 pixel physique, plafond imposé dans la page). 720 y
est déjà au-dessus du un pour un, et un téléphone décode plus lentement qu'un
ordinateur — c'est le seul endroit où le décodage se sent vraiment.

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

from PIL import Image

SITE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(SITE, "ultra-motion.html")
OUT = os.path.join(SITE, "dist", "flux")


def _drapeau(nom, defaut):
    return next((int(a[len(nom):]) for a in sys.argv[1:] if a.startswith(nom)), defaut)


# q=45 et non 32 comme dans le fichier unique : là-bas chaque kilo-octet
# économisé achetait une image, ici il n'achète rien du tout. Le seul coût
# d'un octet supplémentaire est un octet supplémentaire sur un disque.
QUALITE = _drapeau("q=", 45)
SERIES = {
    "accueil":        dict(dossier="assets/film/accueil",        largeur=_drapeau("large=", 1280)),
    "accueil-etroit": dict(dossier="assets/film/accueil-etroit", largeur=_drapeau("etroit=", 720)),
}
# Les courses mesurées dans un navigateur, qui servent à dire la densité
# obtenue — et non à la décider, puisqu'ici on livre TOUTES les images.
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
    shutil.rmtree(OUT, ignore_errors=True)
    os.makedirs(OUT)

    comptes, total = {}, 0
    for nom, reg in SERIES.items():
        fichiers = sorted(glob(os.path.join(SITE, reg["dossier"], "*.jpg")))
        if not fichiers:
            print(f"  {nom:15s} absente — ignorée")
            continue
        cible = os.path.join(OUT, "assets", "film", nom)
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
        avant = src
        src = re.sub(rf"(chemin: *'assets/film/{re.escape(nom)}/f', *images: *)\d+",
                     rf"\g<1>{n}", src)
        if src == avant:
            sys.exit(f"compte de {nom} non trouvé dans la page — lecteur modifié ?")

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
