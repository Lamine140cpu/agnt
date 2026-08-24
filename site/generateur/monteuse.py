#!/usr/bin/env python3
"""
La monteuse : des six plans au dossier d'images, sans intervention.

Elle fait ce qui a été fait à la main sur le film menuiserie, et elle le fait
dans le même ordre :

  1. écrit les six prompts depuis le gabarit et le métier
  2. commande les plans, chacun amorcé par la dernière image du précédent
  3. PROFILE ce qui revient — gel de fin, coupes internes
  4. MESURE quel plan continue quel autre, et n'en déduit rien d'autre
  5. découpe en images numérotées
  6. réécrit dans le manifeste ce qu'elle a RÉELLEMENT produit

    python3 monteuse.py <nom> plans=<dossier>          rejeu : des .mp4 déjà là
    python3 monteuse.py <nom> metier="menuiserie" api=kling cle=...

L'ÉTAPE 4 N'EST PAS UN LUXE. Sur le film menuiserie, l'ordre réel des plans
n'était PAS celui des prompts : c'était l'ordre de génération. Les six fichiers
portaient des noms trompeurs, et se fier au nom aurait donné un film qui saute
trois fois. On compare donc la dernière image de chaque plan à la première de
tous les autres — trente comparaisons — et la chaîne se déduit des chiffres.

CE QUI N'EST PAS TESTÉ ICI : l'appel au modèle vidéo. Il n'y avait pas de clé
dans l'environnement où ce fichier a été écrit, donc `commander()` n'a jamais
tourné en vrai. Tout le reste — profilage, chaînage, découpe, réécriture du
manifeste — a été vérifié sur les six plans du film menuiserie, en mode rejeu.
Le jour où une clé arrive, c'est cette fonction-là qu'il faut éprouver, et elle
seule.
"""
import glob
import json
import os
import subprocess
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(ICI)
sys.path.insert(0, ICI)
from manifeste import ecrire  # noqa: E402


def _drapeau(nom, defaut=None):
    for a in sys.argv[2:]:
        if a.startswith(nom + "="):
            return a.split("=", 1)[1]
    return defaut


# ---------------------------------------------------------------- les prompts

QUEUE = ("Cadre 16:9, sujet centré, marge autour du sujet. "
         "Rendu photographique réaliste, profondeur de champ modérée. "
         "Aucun texte, aucune inscription, aucun logo, aucun visage en gros plan.")

# Les six rôles d'une chorégraphie, dans l'ordre qui a marché trois fois.
# Ce sont des rôles, pas des sujets : le métier les remplit.
ROLES = [
    ("l'atelier",    "travelling latéral lent"),
    ("la matière",   "avancée lente"),
    ("le geste",     "travelling latéral lent qui suit le geste"),
    ("l'outil",      "travelling lent"),
    ("l'ouvrage",    "panoramique lent"),
    ("la sortie",    "avancée lente qui franchit la porte vers la lumière du jour"),
]


def prompts(sujets):
    """Six prompts complets. `sujets` donne la phrase de sujet de chaque plan.

    Les plans 2 à 6 sont formulés comme une CONTINUATION du mouvement, jamais
    comme une nouvelle scène. Mesuré : « Extend » prolonge le plan précédent
    une à deux secondes puis COUPE vers ce qu'on décrit. Décrire une scène
    neuve garantit donc une coupe ; décrire un mouvement qui découvre la
    laisse s'enchaîner.
    """
    if len(sujets) != 6:
        sys.exit(f"il faut six sujets, reçu {len(sujets)}")
    out = []
    for i, ((role, mouvement), sujet) in enumerate(zip(ROLES, sujets), 1):
        if i == 1:
            tete = f"{sujet}, filmé en plan continu de 8 secondes."
        else:
            tete = (f"La caméra poursuit son mouvement et découvre {sujet}. "
                    f"Plan continu de 8 secondes.")
        out.append(
            f"{tete} Mouvement de caméra : {mouvement}, vitesse constante, "
            f"une seule direction, aucun arrêt, aucune coupe. "
            f"Lumière constante pendant tout le plan. {QUEUE}")
    return out


# ------------------------------------------------------------- la commande

def commander(prompts_, dossier, api, cle, amorce_de=None):
    """Commande les six plans au modèle vidéo.

    NON ÉPROUVÉE — aucune clé n'était disponible quand ce fichier a été écrit.
    Le corps ci-dessous décrit l'appel tel qu'il doit être fait ; à valider
    contre la documentation du fournisseur avant le premier vrai passage, et à
    lancer une première fois SUR UN SEUL PLAN.

    Le paramètre qui compte est l'image de départ. Chez Kling c'est
    `type: "first_frame"` ; ailleurs le nom change, jamais le principe.
    """
    raise SystemExit(
        "commander() n'a jamais tourné : il n'y avait pas de clé dans "
        "l'environnement où ce fichier a été écrit.\n\n"
        "Avant de l'utiliser :\n"
        "  1. vérifier la forme exacte de l'appel dans la doc du fournisseur ;\n"
        "  2. l'essayer SUR UN SEUL PLAN, en regardant le fichier qui revient ;\n"
        "  3. seulement ensuite lancer les six.\n\n"
        "En attendant, le mode rejeu fait tout le reste :\n"
        "  python3 monteuse.py <nom> plans=<dossier de .mp4>")


# --------------------------------------------------------------- le profil

def profiler(chemin):
    """Ce que le plan contient vraiment : coupes, et immobilité de fin."""
    p = subprocess.run([sys.executable, os.path.join(SITE, "film_video.py"),
                        chemin, "profil"],
                       capture_output=True, text=True)
    coupes, images = [], 0
    for ligne in p.stdout.splitlines():
        if "coupes :" in ligne:
            reste = ligne.split("coupes :")[1].strip()
            if reste != "aucune":
                coupes = [int(x) for x in reste.strip("[]").split(",") if x.strip()]
        if "images, mouvement moyen" in ligne:
            images = int(ligne.split("—")[1].split("images")[0].strip())
    return {"images": images, "coupes": coupes}


def _ecart(a, b):
    import cv2
    a = cv2.resize(cv2.cvtColor(a, cv2.COLOR_BGR2GRAY), (160, 90)).astype(float)
    b = cv2.resize(cv2.cvtColor(b, cv2.COLOR_BGR2GRAY), (160, 90)).astype(float)
    return abs(a - b).mean()


def _image(chemin, n):
    import cv2
    cap = cv2.VideoCapture(chemin)
    if n < 0:
        n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) + n
    cap.set(cv2.CAP_PROP_POS_FRAMES, n)
    ok, fr = cap.read()
    cap.release()
    return fr if ok else None


def chainer(plans, seuil=8.0):
    """L'ordre RÉEL des plans, déduit des images et non des noms de fichier.

    Sur le film menuiserie, l'ordre des prompts et l'ordre réel différaient :
    les fichiers portaient les noms des prompts, la chaîne suivait l'ordre de
    génération. Se fier au nom aurait donné un film qui saute trois fois.

    On compare la dernière image de chaque plan à la première de tous les
    autres. Une jointure vraie tient sous 6 sur 255 — c'est le bruit de
    recompression. Une fausse est au-dessus de 35.
    """
    fins = {p: _image(p, -1) for p in plans}
    debuts = {p: _image(p, 0) for p in plans}
    suivant, ecarts = {}, {}
    for a in plans:
        candidats = [(b, _ecart(fins[a], debuts[b])) for b in plans if b != a]
        b, e = min(candidats, key=lambda x: x[1])
        if e <= seuil:
            suivant[a], ecarts[(a, b)] = b, e

    # Le premier plan est celui que personne ne précède.
    precedes = set(suivant.values())
    tetes = [p for p in plans if p not in precedes]
    if len(tetes) != 1:
        return None, ecarts, (f"{len(tetes)} plan(s) sans prédécesseur — "
                              f"la chaîne est rompue ou circulaire")
    ordre, vu = [], set()
    p = tetes[0]
    while p and p not in vu:
        ordre.append(p); vu.add(p)
        p = suivant.get(p)
    if len(ordre) != len(plans):
        return None, ecarts, (f"seuls {len(ordre)} plans sur {len(plans)} "
                              f"s'enchaînent — les autres ne continuent rien")
    return ordre, ecarts, None


# --------------------------------------------------------------- la découpe

def decouper(ordre, film, images, largeur=1920):
    cmd = [sys.executable, os.path.join(SITE, "film_video.py")] + list(ordre) + \
          [str(images), str(largeur), film]
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        sys.exit(f"la découpe a échoué :\n{p.stderr[-800:]}")
    return p.stdout


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__.strip())
    nom = sys.argv[1]
    contrat = os.path.join(ICI, f"manifeste-{nom}.json")
    if not os.path.exists(contrat):
        sys.exit(f"{contrat} est introuvable — lancer d'abord nouveau.py")
    m = json.load(open(contrat, encoding="utf-8"))
    film = m["film"]["series"]["accueil"]["dossier"]["valeur"]

    dossier = _drapeau("plans")
    if not dossier:
        commander(None, None, _drapeau("api"), _drapeau("cle"))
    plans = sorted(glob.glob(os.path.join(dossier, "*.mp4")))
    if not plans:
        sys.exit(f"aucun .mp4 dans {dossier}")

    print(f"{len(plans)} plans\n")
    print("PROFIL")
    total = 0
    for p in plans:
        pr = profiler(p)
        total += pr["images"]
        print(f"  {os.path.basename(p):32s} {pr['images']:4d} images · "
              + (f"coupe(s) à {pr['coupes']}" if pr["coupes"] else "aucune coupe"))

    print("\nCHAÎNE — mesurée, jamais déduite des noms de fichier")
    ordre, ecarts, faute = chainer(plans)
    if faute:
        print(f"  ROMPUE : {faute}")
        print("  Les plans n'ont pas été enchaînés sur la dernière image du")
        print("  précédent. Les régénérer : un film dont les plans ne se")
        print("  suivent pas montre six ateliers différents.")
        sys.exit(1)
    for a, b in zip(ordre, ordre[1:]):
        print(f"  {os.path.basename(a):32s} -> {os.path.basename(b):32s} "
              f"{ecarts[(a, b)]:5.1f}/255")

    print(f"\nDÉCOUPE — {total} images en {film}")
    print(decouper(ordre, film, total).splitlines()[-3] if total else "")

    # Ce qui a RÉELLEMENT été produit, relu sur le disque.
    livrees = sorted(glob.glob(os.path.join(SITE, "assets", "film", film, "*.jpg")))
    if not livrees:
        sys.exit("aucune image écrite")
    from PIL import Image
    with Image.open(livrees[0]) as im:
        l, h = im.size
    for s in m["film"]["series"].values():
        if isinstance(s, dict) and "largeur" in s:
            s["largeur"]["origine"] = "mesure"
    m["film"]["_produit"] = {
        "plans": [os.path.basename(p) for p in ordre],
        "images_sources": len(livrees),
        "definition": f"{l}x{h}",
        "_": "Écrit par la monteuse d'après le disque, pas d'après ce qu'elle "
             "comptait produire.",
    }
    ecrire(m, contrat)
    print(f"\n{len(livrees)} images {l}x{h} — écrit dans manifeste-{nom}.json")
    print("\nensuite :  python3 generateur/chaine.py " + nom)


if __name__ == "__main__":
    main()
