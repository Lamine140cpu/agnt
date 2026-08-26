#!/usr/bin/env python3
"""
Assemble les refontes à partir du MÊME lecteur que la page d'origine.

Deux directions artistiques du site Trans Gold coexistent, plus la version
d'origine : trois pages, un seul moteur de défilement. Le recopier à la main
dans chacune serait la garantie qu'il diverge — c'est déjà arrivé dans ce
dépôt entre la vitrine et la première page client, et un correctif de fluidité
avait dû être porté trois fois de suite.

Chaque refonte est donc un fichier `refontes/NOM.part.html` complet — en-tête,
feuille de style, corps — où le lecteur est remplacé par un simple marqueur
`<!--MOTEUR-->`. Ce script y injecte le bloc <script> de transgold.html tel
quel, sans le relire ni le modifier.

    usage : python3 refonte.py [nom ...]

Sans argument, il assemble toutes les refontes connues.

Ce que la page assemblée doit fournir au lecteur, sous peine d'écran noir
silencieux — le pire mode de panne, déjà rencontré ici :

    #toile            la toile du film
    #prologue         contenant des <section> : ce sont les actes
    #suite            contenant les blocs révélés au défilement
    #voile #etape #jauge #pct     l'écran d'attente

Le script vérifie leur présence avant d'écrire. Une page qui compile mais ne
peut pas fonctionner ne doit pas sortir d'ici.
"""
import os
import re
import sys

SITE = os.path.dirname(os.path.abspath(__file__))
# La source unique. Elle n'est plus prise dans transgold.html : cette page est
# celle d'un client, et y puiser le lecteur faisait dépendre toutes les autres
# de ses modifications. Mesuré avant de couper le lien : six versions du même
# lecteur cohabitaient dans ce dépôt, divergeant de 8 à 13 % — les cinq
# refontes et la vitrine tournaient sans aucun des correctifs récents.
MOTEUR_SOURCE = os.path.join(SITE, "moteur", "lecteur.js")
# Les refontes partagent la pellicule de transgold : elles ne changent que la
# direction artistique, jamais le film.
FILM = "transgold"
# La page qui fait foi : c'est elle que les moteurs doivent trouver, jamais un
# essai.
CANONIQUE = "https://lamine140cpu.github.io/agnt/transgold/"
DOSSIER = os.path.join(SITE, "refontes")

# Le nom du fichier produit vaut aussi nom de construction : `build_flux.py
# client=transgold-bord film=transgold` fabrique la page à partir du film déjà
# encodé, sans en réencoder une seule image.
REFONTES = {
    "bord":   "transgold-bord.html",     # A — le tableau de bord
    "signal": "transgold-signal.html",   # B — la signalisation
    "plein":  "transgold-plein.html",    # le principe d'origine, poussé
    "hud":    "transgold-hud.html",      # le même format, en poste de pilotage
    "terminal": "transgold-terminal.html",  # refonte totale : caractères, couleur, course
}

EXIGENCES = ('id="toile"', 'id="prologue"', 'id="suite"',
             'id="voile"', 'id="etape"', 'id="jauge"', 'id="pct"')


def moteur():
    """Le lecteur, précédé des séries que CE film emploie.

    Le lecteur ne déclare plus ses séries : il lit `window.SERIES`, que la page
    doit poser avant lui. C'est ce qui l'a rendu générique — c'était son seul
    morceau propre à un site, sur huit cent soixante et une lignes.
    """
    if not os.path.exists(MOTEUR_SOURCE):
        sys.exit(f"{MOTEUR_SOURCE} est introuvable — c'est la source unique")
    code = open(MOTEUR_SOURCE, encoding="utf-8").read()
    # Les comptes et les DIMENSIONS écrits ici ne sont que des défauts pour le
    # mode replié : la construction les mesure sur les images livrées et les
    # remplace. Les poser quand même évite qu'une refonte ouverte sans
    # construction retombe sur l'ancienne règle de choix de série.
    series = (
        "window.SERIES = {\n"
        f"  accueil:          {{ chemin: 'assets/film/{FILM}/f',        "
        "images: 1152, largeur: 1920, hauteur: 1080 },\n"
        f"  'accueil-etroit': {{ chemin: 'assets/film/{FILM}-etroit/f',  "
        "images: 1152, largeur: 1440, hauteur: 810 },\n"
        "};\n"
    )
    return series + code


def assembler(nom, code):
    part = os.path.join(DOSSIER, f"{nom}.part.html")
    if not os.path.exists(part):
        sys.exit(f"{part} est introuvable")
    page = open(part, encoding="utf-8").read()

    if page.count("<!--MOTEUR-->") != 1:
        sys.exit(f"{nom} : le marqueur <!--MOTEUR--> doit apparaître une fois "
                 f"et une seule (trouvé {page.count('<!--MOTEUR-->')})")
    manque = [x for x in EXIGENCES if x not in page]
    if manque:
        sys.exit(f"{nom} : le lecteur ne trouverait pas {', '.join(manque)} — "
                 f"la page s'afficherait noire sans la moindre erreur")

    # UNE DIRECTION REJETÉE NE DOIT JAMAIS ÊTRE INDEXABLE.
    #
    # Les cinq refontes portaient « index, follow » et le MÊME titre que la page
    # du client, à une adresse voisine — deux pages concurrentes sur le même nom
    # d'entreprise, ce qui est exactement ce qu'un moteur de recherche pénalise.
    # Pire, leur adresse canonique désignait un fichier qui n'existe pas :
    # « /transgold/terminal.html » quand la page est publiée sous
    # « /transgold-terminal/ ». Une canonique cassée ne protège de rien.
    #
    # Ce sont des essais. On les rend invisibles aux moteurs et on désigne la
    # vraie page comme canonique — sans rien supprimer : elles restent
    # consultables par leur adresse directe, ce qui est leur seul usage.
    page = re.sub(r'<meta name="robots" content="[^"]*">',
                  '<meta name="robots" content="noindex, nofollow">', page)
    page = re.sub(r'<link rel="canonical" href="[^"]*">',
                  f'<link rel="canonical" href="{CANONIQUE}">', page)
    page = re.sub(r'<meta property="og:url" content="[^"]*">',
                  f'<meta property="og:url" content="{CANONIQUE}">', page)

    page = page.replace("<!--MOTEUR-->", "<script>" + code + "</script>")
    cible = os.path.join(SITE, REFONTES[nom])
    open(cible, "w", encoding="utf-8").write(page)
    return cible, len(page)


def main():
    demandes = [a for a in sys.argv[1:] if not a.startswith("-")] or list(REFONTES)
    inconnues = [d for d in demandes if d not in REFONTES]
    if inconnues:
        sys.exit(f"refonte inconnue : {', '.join(inconnues)} — "
                 f"au choix {', '.join(REFONTES)}")

    code = moteur()
    print(f"lecteur repris de moteur/{os.path.basename(MOTEUR_SOURCE)} "
          f"({len(code)/1024:.0f} Ko), séries du film « {FILM} »\n")
    for nom in demandes:
        cible, taille = assembler(nom, code)
        print(f"  {nom:8s} -> {os.path.basename(cible):26s} {taille/1024:6.0f} Ko")
    print("\nconstruire :  python3 build_flux.py client=transgold-bord "
          "film=transgold page")


if __name__ == "__main__":
    main()
