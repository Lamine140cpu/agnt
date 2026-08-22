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
MOTEUR_SOURCE = os.path.join(SITE, "transgold.html")
DOSSIER = os.path.join(SITE, "refontes")

# Le nom du fichier produit vaut aussi nom de construction : `build_flux.py
# client=transgold-bord film=transgold` fabrique la page à partir du film déjà
# encodé, sans en réencoder une seule image.
REFONTES = {
    "bord":   "transgold-bord.html",     # A — le tableau de bord
    "signal": "transgold-signal.html",   # B — la signalisation
    "plein":  "transgold-plein.html",    # le principe d'origine, poussé
    "hud":    "transgold-hud.html",      # le même format, en poste de pilotage
}

EXIGENCES = ('id="toile"', 'id="prologue"', 'id="suite"',
             'id="voile"', 'id="etape"', 'id="jauge"', 'id="pct"')


def moteur():
    src = open(MOTEUR_SOURCE, encoding="utf-8").read()
    blocs = re.findall(r"<script>(.*?)</script>", src, re.S)
    if not blocs:
        sys.exit(f"aucun <script> dans {MOTEUR_SOURCE}")
    # Le lecteur est de loin le plus long : les autres sont des compléments de
    # mise en page propres à chaque direction.
    return max(blocs, key=len)


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
    print(f"lecteur repris de {os.path.basename(MOTEUR_SOURCE)} "
          f"({len(code)/1024:.0f} Ko)\n")
    for nom in demandes:
        cible, taille = assembler(nom, code)
        print(f"  {nom:8s} -> {os.path.basename(cible):26s} {taille/1024:6.0f} Ko")
    print("\nconstruire :  python3 build_flux.py client=transgold-bord "
          "film=transgold page")


if __name__ == "__main__":
    main()
