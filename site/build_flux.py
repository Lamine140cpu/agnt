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
import datetime
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

# Un client se construit avec le même moteur et le même code : seuls la page
# source, le dossier de sortie et les dossiers d'images changent. C'est la
# preuve que la chaîne est réutilisable — si construire un second site
# demandait de dupliquer ce fichier, elle ne le serait pas.
CLIENT = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("client=")), None)
SOURCE = os.path.join(SITE, f"{CLIENT}.html" if CLIENT else "ultra-motion.html")

# `out=` et `fichier=` séparent la PAGE de son EMPLACEMENT. Trois directions
# artistiques du même site partagent une pellicule de 34 Mo : les publier dans
# trois dossiers en recopierait trois fois, pour rien. Elles cohabitent donc
# dans le même dossier sous trois noms de fichier, et se partagent
# « assets/film » sans qu'aucun chemin ne change dans le lecteur.
_OUTNOM = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("out=")), None)
OUT = os.path.join(SITE, "dist", _OUTNOM or (CLIENT if CLIENT else "flux"))
FICHIER = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("fichier=")), "index.html")


def _drapeau(nom, defaut):
    return next((int(a[len(nom):]) for a in sys.argv[1:] if a.startswith(nom)), defaut)


# LE MANIFESTE, quand il y en a un, l'emporte sur les défauts.
#
# Les défauts ne peuvent PAS servir deux sites : mesuré, la course du prologue
# vaut 26 100 px chez Trans Gold et 15 300 sur la vitrine. Une constante
# globale est donc juste pour l'un et fausse pour l'autre, en silence — c'est
# exactement ce qui s'est produit, dans les deux sens. Ces valeurs
# appartiennent au site, pas au script.
_MANIF = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("manifeste=")), None)
_M = None
if _MANIF:
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "generateur"))
    from manifeste import charger as _charger, champs as _champs, _valeur as _val, Faute as _Faute
    try:
        _M = _charger(_MANIF)
    except _Faute as e:
        sys.exit(f"CONTRAT ROMPU — {e}")


def _du_manifeste(chemin, defaut):
    """Une valeur du manifeste, ou le défaut. `chemin` en pointillés."""
    if not _M:
        return defaut
    n = _M
    for cle in chemin.split("."):
        if not isinstance(n, dict) or cle not in n:
            return defaut
        n = n[cle]
    return _val(n, chemin) if isinstance(n, dict) and "valeur" in n else n


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
# voit. La compression n'est plus le maillon faible, la source l'est.
#
# Le défaut valait 55 « comme marge » — et le site EN LIGNE est en q45. Vérifié
# au kilo-octet près : l'image f0100 du lot publié pèse 50,8 Ko, ce que q45
# reproduit exactement, quand q55 en fait 85,5. Personne ne construisait donc
# avec le défaut, et le jour où quelqu'un l'aurait fait sans y penser, la
# pellicule aurait grossi de deux tiers sans que rien ne le dise. Une marge
# qu'on n'utilise pas n'est pas une marge, c'est un piège. Le défaut dit
# désormais ce qui tourne.
QUALITE = _drapeau("q=", _du_manifeste("film.qualite", 45))
# Réécrit seulement index.html, sans toucher aux images déjà encodées.
PAGE_SEULE = "page" in sys.argv[1:]
# Ne réencoder qu'une série, en gardant l'autre telle quelle. Vingt minutes
# d'encodeur ne se redépensent pas pour un réglage qui ne touche qu'un côté.
SEULE = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("serie=")), None)
# Densité voulue, en pixels de défilement par image. C'est ELLE qu'on choisit ;
# le nombre d'images en découle.
PAR_IMAGE = _drapeau("parimage=", _du_manifeste("film.densite_visee", 33))
# Les CLÉS restent « accueil » et « accueil-etroit » : ce sont les noms que le
# lecteur emploie pour choisir sa série selon la forme de l'écran, et il n'a
# pas à savoir de quel client il s'agit. Seuls les DOSSIERS changent.
#
# `film=` sépare la PAGE de son FILM. Deux directions artistiques d'un même
# site partagent la même pellicule : il serait absurde de réencoder 1 318
# images parce qu'on a changé la couleur du fond. Sans ce drapeau, une page
# nommée « transgold-bord » irait chercher « assets/film/transgold-bord », qui
# n'existe pas — et la construction produirait une page noire sans rien dire,
# ce qui est déjà arrivé trois fois dans ce projet.
FILM = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("film=")), None) or CLIENT
_pref = FILM if FILM else "accueil"
_etroit = f"{FILM}-etroit" if FILM else "accueil-etroit"
# La série du téléphone vient du MÊME maître que celle du bureau, seulement
# moins large — elle n'est plus un recadrage.
#
# Elle l'était : « assets/film/<film>-etroit » contenait un rognage centré 9:16
# du maître 16:9, qui n'en gardait que 32 % de la largeur. Mesuré image par
# image contre un recadrage centré reconstruit ici, l'écart médian est de
# 1,4 sur 255 — c'est le bruit de recompression JPEG, autrement dit c'était
# bien un rognage, malgré la note qui affirmait le contraire.
#
# Et ce rognage ne servait à rien. En cadrage « couvrir », la part du film
# visible ne dépend que du rapport de la TOILE et de celui du maître :
# 0,462 / 1,778 = 26 %, que la série intermédiaire soit en 9:16, en 3:4, carrée
# ou en 16:9. Le rognage ne déplaçait pas le cadrage, il ne faisait que jeter
# des pixels — et le client a fini par le dire : « sur téléphone c'est trop
# zoomé ».
#
# `sortie` sépare donc le dossier SOURCE du dossier ÉCRIT. Sans elle, les deux
# séries lues dans le même dossier s'écriraient au même endroit.
SERIES = {
    "accueil":        dict(dossier=f"assets/film/{_pref}", sortie=_pref,
                           largeur=_drapeau("large=", 1920)),
    # 1440 px : la toile du téléphone fait 585 x 810 pixels d'appareil (390 CSS
    # de large, densité plafonnée à 1,5). Une image 1440x810 s'y pose au rapport
    # 1:1 en hauteur, sans agrandissement — en dessous elle serait floue, au
    # dessus on paierait des octets que personne ne voit.
    "accueil-etroit": dict(dossier=f"assets/film/{_pref}", sortie=_etroit,
                           largeur=_drapeau("etroit=", 1440)),
}
# Les courses mesurées dans un navigateur. Ce sont elles qui, divisées par la
# densité voulue, donnent le nombre d'images à livrer.
#
# Elles dépendent de la MISE EN PAGE, donc elles changent d'un site à l'autre :
# la vitrine tient ses actes sur trois écrans, un client peut en vouloir cinq.
# D'où les drapeaux, plutôt qu'une constante à retoucher — deux sites doivent
# pouvoir se construire le même jour sans se marcher dessus.
#
# ELLES SE MESURENT, ELLES NE SE DEVINENT PAS. Dans la page servie :
#
#     prologue.offsetHeight - innerHeight
#
# Prendre la plus GRANDE des fenêtres visées : une course plus courte que
# prévu donne une densité plus fine que voulue, l'inverse donne un film qui
# saute. Mesuré ici — bureau 1440x900 : 26 100 px ; 1280x800 : 23 200 ;
# téléphone 390x844 : 17 386 ; 360x740 : 15 244.
#
# Ces valeurs valaient 15 300 et 10 297 et n'ont pas suivi le passage des
# actes de 130 à 170 svh. Rien ne l'a signalé : la construction a livré 464 et
# 312 images en annonçant fièrement « 33,0 px de défilement par image », alors
# que la vraie densité tombait à 56 — un film deux fois plus saccadé, et le
# message qui affirmait le contraire. Une constante fausse qui sert aussi à
# calculer ce qu'on affiche ne peut pas se contredire toute seule.
def _course(cle, drapeau, defaut):
    """La course d'une série : le manifeste dit LAQUELLE des courses mesurées
    la concerne, par la taille d'écran. Sans manifeste, le drapeau, puis le
    défaut — qui n'est juste que pour la vitrine."""
    if _M:
        s = _champs(_M["film"]["series"]).get(cle, {})
        taille = s.get("course")
        if taille:
            return _drapeau(drapeau, _val(_champs(_M["page"]["courses"])[taille], ""))
    return _drapeau(drapeau, defaut)


COURSES = {"accueil": _course("accueil", "course=", 15300),
           "accueil-etroit": _course("accueil-etroit", "courseetroit=", 10297)}
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


def lecteur(src):
    """Insère le lecteur unique à la place du marqueur.

    Le lecteur n'est pas chargé par <script src> : un site client tient sur une
    seule page, et une requête de plus avant que le film ne démarre coûterait un
    aller-retour à chaque visite pour un cache que personne ne réutiliserait. On
    veut donc les deux — une seule source sur le disque, zéro requête en ligne.

    Une page sans marqueur est laissée telle quelle : les anciennes pages
    portent encore leur lecteur en clair, et la migration se fait une par une.

    LE MARQUEUR SE RECONNAÎT À SA LIGNE, PAS À SON TEXTE. Cherché n'importe où
    dans la page, il se trouvait aussi dans le commentaire d'en-tête du lecteur
    lui-même — qui explique en toutes lettres qu'il est inséré « à la place du
    marqueur <!--LECTEUR--> ». Une page non migrée porte ce commentaire avec sa
    copie du lecteur : la construction prenait donc la CITATION pour le
    marqueur et injectait le lecteur neuf au milieu d'un commentaire, où il
    restait inerte. La page se construisait sans une seule erreur, s'ouvrait
    sans une seule erreur, et tournait sur l'ancien code. Un correctif de
    fluidité y a été livré et n'y a jamais tourné.

    On exige donc une ligne qui ne contient QUE le marqueur.
    """
    marqueur = re.compile(r"^[ \t]*<!--LECTEUR-->[ \t]*$", re.MULTILINE)
    trouves = marqueur.findall(src)
    if not trouves:
        return src
    if len(trouves) != 1:
        sys.exit(f"le marqueur <!--LECTEUR--> apparaît sur {len(trouves)} lignes "
                 f"— il en faut exactement une")
    if "window.SERIES" not in src:
        sys.exit("la page appelle le lecteur mais ne déclare pas window.SERIES : "
                 "la toile resterait noire")
    chemin = os.path.join(SITE, "moteur", "lecteur.js")
    if not os.path.exists(chemin):
        sys.exit(f"{chemin} est introuvable — c'est la source unique du lecteur")
    code = open(chemin, encoding="utf-8").read()
    print(f"  lecteur          {len(code)/1024:4.0f} Ko  <- moteur/lecteur.js")
    return marqueur.sub(lambda _: "<script>\n" + code + "\n</script>", src, count=1)


def socle(src):
    """Insère le socle de style à la place du marqueur.

    Même raison que pour le lecteur : une seule source. Les quatre-vingts
    règles qu'il contient étaient recopiées dans chaque site, et le jour où
    l'une a été corrigée d'un côté, l'autre a gardé le défaut — mesuré, le bas
    de la vitrine touchait le bord de l'écran sur téléphone.

    Il est posé EN TÊTE de la feuille du site, qui garde donc le dernier mot
    sur tout ce qu'elle redéclare : la palette, l'en-tête, le pied, la hauteur
    des actes. Une page sans marqueur passe telle quelle."""
    if "<!--SOCLE-->" not in src:
        return src
    if src.count("<!--SOCLE-->") != 1:
        sys.exit(f"le marqueur <!--SOCLE--> apparaît {src.count('<!--SOCLE-->')} "
                 f"fois — il en faut exactement un")
    chemin = os.path.join(SITE, "moteur", "socle.css")
    if not os.path.exists(chemin):
        sys.exit(f"{chemin} est introuvable — c'est la source unique du socle")
    css = open(chemin, encoding="utf-8").read()
    print(f"  socle            {len(css)/1024:4.0f} Ko  <- moteur/socle.css")
    return src.replace("<!--SOCLE-->", css)


def main():
    src = socle(lecteur(open(SOURCE, encoding="utf-8").read()))
    if not PAGE_SEULE and not SEULE:
        shutil.rmtree(OUT, ignore_errors=True)
        os.makedirs(OUT)
    elif SEULE:
        # Même piège que pour l'écriture : le dossier porte le nom de la SOURCE,
        # pas celui de la clé. Effacer d'après la clé ne supprimait rien, et la
        # création butait ensuite sur un dossier déjà là.
        shutil.rmtree(os.path.join(OUT, "assets", "film",
                                   os.path.basename(SERIES[SEULE]["dossier"])),
                      ignore_errors=True)
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
        # Le dossier de sortie est DÉCLARÉ, jamais déduit. Ni de la clé de
        # série — la page demande « assets/film/transgold/f » alors que la clé
        # vaut « accueil », et nommer d'après la clé écrivait les images à côté
        # de là où la page les cherche : toile vide, sans une seule erreur, le
        # pire mode de défaillance. Ni du dossier source, puisque les deux
        # séries lisent désormais le même maître et s'écraseraient l'une
        # l'autre.
        cible = os.path.join(OUT, "assets", "film", reg["sortie"])
        if PAGE_SEULE or (SEULE and nom != SEULE):
            # Une série jamais encodée n'est pas une trace de pile. Le mode
            # `page` suppose la pellicule déjà là ; quand elle ne l'est pas,
            # il faut le dire, pas planter sur un dossier introuvable.
            if not os.path.isdir(cible):
                sys.exit(
                    f"la série « {nom} » n'a jamais été encodée : "
                    f"{os.path.relpath(cible, SITE)} n'existe pas.\n"
                    f"Le mode `page` saute l'encodage, il ne le remplace pas.\n"
                    f"  - soit reconstruire sans `page` ;\n"
                    f"  - soit produire la pellicule : "
                    f"python3 generateur/monteuse.py <nom> plans=<dossier>")
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
        # Le motif se construit sur le dossier de SORTIE, celui que la page
        # écrit — pas sur la clé de série, pas sur le dossier source.
        #
        # Pas la clé : la page d'un client écrit « assets/film/transgold/f » là
        # où la vitrine écrit « assets/film/accueil/f », alors que la clé vaut
        # « accueil » dans les deux cas. Chercher la clé ne trouverait rien.
        #
        # Pas le dossier source : depuis que les deux séries lisent le même
        # maître, il est identique pour les deux. Les deux motifs visaient donc
        # la MÊME ligne, la seconde substitution écrasait la première, et la
        # ligne de l'autre série n'était jamais touchée — elle gardait le
        # compte du mode replié, 1152 au lieu de 527. Le lecteur répartissait
        # alors le défilement sur 1152 images dont 625 n'existaient pas : 404
        # en rafale et film figé au-delà du milieu du prologue, sur téléphone.
        # Le garde-fou n'a rien vu : il compte les correspondances, or chaque
        # substitution en trouvait bien exactement une — la même.
        dossier = SERIES[nom]["sortie"]
        src, combien = re.subn(
            rf"(chemin: *'assets/film/{re.escape(dossier)}/f', *images: *)\d+",
            rf"\g<1>{n}", src)
        if combien != 1:
            sys.exit(f"compte de {nom} : {combien} correspondance(s) dans la page "
                     f"au lieu d'une — lecteur modifié ?")

    # Les DIMENSIONS de chaque série, mesurées sur l'image livrée et écrites
    # dans la page. C'est le lecteur qui s'en sert pour choisir sa série : la
    # forme d'abord — un film monté en portrait doit être trouvé comme tel —
    # puis la plus petite qui couvre la toile sans agrandissement.
    #
    # Elles sont MESURÉES, jamais recopiées. Une dimension écrite à la main
    # rejoindrait la liste des constantes de ce dépôt qui ont cessé de décrire
    # la réalité sans que rien ne le signale : la course, la qualité, la nature
    # de la série téléphone, le compte d'images.
    # LE POIDS EST ÉCRIT AVEC LES DIMENSIONS, et il est aussi décisif qu'elles.
    #
    # Le lecteur choisissait sa série sur la forme et la définition seules. Un
    # visiteur mesuré : fenêtre 1280 x 551 en densité 1,5, donc 1920 pixels
    # demandés, donc la série lourde — 1200 images à 42,8 Ko. Sur sa ligne à
    # 10 Mbit/s il en aurait fallu 15 : 79 % de ses trames n'avaient AUCUNE
    # image à montrer. La série légère, elle, tenait dans 7 Mbit/s.
    #
    # La netteté avait donc été préférée au fait que le film se joue. Le lecteur
    # ne pouvait pas faire mieux : rien dans la page ne lui disait ce qu'une
    # série coûte à télécharger. C'est ce chiffre-là qu'on lui donne.
    from PIL import Image as _Im
    for nom in comptes:
        cible = os.path.join(OUT, "assets", "film", SERIES[nom]["sortie"])
        fichiers = sorted(os.listdir(cible))
        premiere = fichiers[0]
        with _Im.open(os.path.join(cible, premiere)) as im:
            l, h = im.size
        # Moyenne sur un échantillon régulier : les premières images d'un film
        # ne pèsent pas ce que pèsent les plus chargées, et c'est la moyenne
        # qui décide du débit tenu.
        ech = fichiers[:: max(1, len(fichiers) // 40)][:40]
        octets = round(sum(os.path.getsize(os.path.join(cible, f)) for f in ech) / len(ech))
        motif = (rf"(chemin: *'assets/film/{re.escape(SERIES[nom]['sortie'])}/f',"
                 rf"[^}}]*?images: *\d+)([^}}]*)")

        def _dim(m):
            reste = re.sub(r", *largeur: *\d+, *hauteur: *\d+(, *octets: *\d+)?", "", m.group(2))
            reste = re.sub(r", *octets: *\d+", "", reste)
            return f"{m.group(1)}, largeur: {l}, hauteur: {h}, octets: {octets}{reste}"

        src, n_dim = re.subn(motif, _dim, src, count=1)
        if n_dim != 1:
            sys.exit(f"{nom} : impossible d'écrire les dimensions dans la page")

    # Et on RELIT ce qu'on vient d'écrire, série par série. Compter les
    # substitutions ne prouve rien sur ce qui est dans le fichier : deux
    # substitutions réussies peuvent avoir visé la même ligne. Seule la
    # relecture le dit.
    for nom, n in comptes.items():
        ecrit = re.search(
            rf"chemin: *'assets/film/{re.escape(SERIES[nom]['sortie'])}/f', *images: *(\d+)",
            src)
        if not ecrit:
            sys.exit(f"{nom} : aucune déclaration de série pour "
                     f"« {SERIES[nom]['sortie']} » dans la page")
        if int(ecrit.group(1)) != n:
            sys.exit(f"{nom} : la page annonce {ecrit.group(1)} images, le "
                     f"dossier en contient {n}. Le lecteur répartirait le "
                     f"défilement sur un compte faux — images manquantes en "
                     f"404, ou dernier tiers du film figé.")

    # La feuille des fontes reste un fichier à part : elle est mise en cache une
    # fois pour toutes, et 216 Ko dans chaque page seraient 216 Ko à chaque
    # visite.
    # La feuille de fontes est celle que la PAGE demande, pas une constante :
    # chaque direction artistique a la sienne, et copier « ultra.css » pour une
    # page qui appelle « ultra-bord.css » donnait un 404 muet — la page
    # s'affichait, dans la fonte de secours, sans que rien ne le signale.
    os.makedirs(os.path.join(OUT, "assets", "fonts"), exist_ok=True)
    feuilles = sorted(set(re.findall(r"assets/fonts/([\w.-]+\.css)", src)))
    if not feuilles:
        sys.exit("la page n'appelle aucune feuille de fontes")
    for f in feuilles:
        depuis = os.path.join(SITE, "assets", "fonts", f)
        if not os.path.exists(depuis):
            sys.exit(f"la page demande {f}, absent de assets/fonts/ — "
                     f"le produire avec fontes_locales.py")
        shutil.copy(depuis, os.path.join(OUT, "assets", "fonts", f))
        print(f"  assets/fonts/{f}  {os.path.getsize(depuis)/1024:.0f} Ko")

    # Les fichiers d'« assets » cités en dur par la page — l'image de partage,
    # par exemple. On les recopie d'après ce que la page demande réellement,
    # pour ne pas avoir à tenir une liste à jour à la main : une vignette de
    # partage manquante ne casse rien de visible et ne se découvre que le jour
    # où quelqu'un colle le lien dans une conversation.
    for chemin in sorted(set(re.findall(r"assets/[\w./-]+\.(?:jpg|png|svg|webp|avif|ico)", src))):
        if "/film/" in chemin:
            continue
        depuis = os.path.join(SITE, chemin)
        if not os.path.exists(depuis):
            sys.exit(f"la page cite {chemin}, absent de {SITE}")
        vers = os.path.join(OUT, chemin)
        os.makedirs(os.path.dirname(vers), exist_ok=True)
        shutil.copy(depuis, vers)
        print(f"  {chemin}  {os.path.getsize(depuis)/1024:.0f} Ko")

    # robots.txt et sitemap.xml, déduits de l'adresse canonique déclarée par la
    # page. Sans eux un moteur finit par trouver le site, mais plus tard et sans
    # savoir quand il a changé. Deux fichiers de dix lignes.
    canon = re.search(r'<link rel="canonical" href="([^"]+)"', src)
    if canon and FICHIER == "index.html":
        base = canon.group(1).rstrip("/") + "/"
        jour = datetime.date.today().isoformat()
        open(os.path.join(OUT, "robots.txt"), "w", encoding="utf-8").write(
            "User-agent: *\nAllow: /\n\n"
            f"Sitemap: {base}sitemap.xml\n")
        open(os.path.join(OUT, "sitemap.xml"), "w", encoding="utf-8").write(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            f'  <url>\n    <loc>{base}</loc>\n'
            f'    <lastmod>{jour}</lastmod>\n'
            '    <changefreq>monthly</changefreq>\n'
            '    <priority>1.0</priority>\n  </url>\n</urlset>\n')
        print("  robots.txt · sitemap.xml")

    open(os.path.join(OUT, FICHIER), "w", encoding="utf-8").write(src)
    page = os.path.getsize(os.path.join(OUT, FICHIER)) / 1024
    print(f"\nécrit {OUT}/")
    print(f"  {FICHIER:12s} {page:6.0f} Ko  <- ce que le visiteur télécharge d'abord")
    print(f"  images       {total/1048576:6.1f} Mo  <- demandées au fil du défilement")
    print(f"\n  pour l'essayer :  cd {OUT} && python3 -m http.server 8000")


if __name__ == "__main__":
    main()
