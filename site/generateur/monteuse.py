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

    python3 monteuse.py <nom> api=<descripteur> cle=<clé>   génération
    python3 monteuse.py <nom> plans=<dossier>               rejeu : des .mp4 là
    python3 monteuse.py essai plans=<dossier>               éprouve la boucle

LE MODÈLE VIDÉO A LE DROIT DE RATER ; IL N'A PAS LE DROIT DE PASSER.

On ne peut pas obliger un modèle vidéo à enchaîner : on lui donne la dernière
image du plan précédent, il rend ce qu'il veut. Alors on ne lui demande pas de
réussir, on MESURE — la jointure avec le plan d'avant, et la continuité du plan
lui-même. Un plan qui rate est jeté et recommandé ; au bout de `essais`
tentatives, on s'arrête. Ce n'est donc pas le modèle qui garantit la
continuité, c'est la boucle. Voir `produire()`.

L'ORDRE NE SE LIT PAS SUR LES NOMS DE FICHIER. En génération il est connu par
construction. En rejeu il est MESURÉ : sur le film menuiserie, l'ordre réel
n'était pas celui des prompts mais celui de la génération, et se fier au nom
donnait un film qui saute trois fois. On compare donc la dernière image de
chaque plan à la première de tous les autres — trente comparaisons.

CE QUI EST ÉPROUVÉ, ET COMMENT. La boucle de reprise et les deux contrôles :
`monteuse.py essai` les fait tourner contre un fournisseur qui rate exprès —
sans ça, six plans qui passent du premier coup ne font jamais tourner la
boucle et on ne saurait pas si elle marche. La mécanique réseau : voir
`fournisseur.py essai`. Ce qui n'est PAS éprouvé : les valeurs d'un descripteur
de vrai fournisseur, faute de clé — d'où le refus de tourner tant que son
`"verifie"` n'a pas été basculé à la main après un essai sur UN plan.
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

def derniere_image(mp4, jpg):
    """La dernière image d'un plan, sur le disque. C'est elle, l'amorce.

    C'est le seul lien entre deux plans. Un plan commandé sans elle montre un
    autre atelier — même prompt, même métier, autre lieu.
    """
    import cv2
    fr = _image(mp4, -1)
    if fr is None:
        raise RuntimeError(f"pas d'image lisible dans {mp4}")
    cv2.imwrite(jpg, fr, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
    return jpg


def produire(fournisseur, prompts_, travail, seuil=8.0, essais=3, journal=print,
             tolerer_coupes=False):
    """Les six plans, commandés dans l'ordre, VÉRIFIÉS à chaque pas.

    LE MODÈLE VIDÉO A LE DROIT DE RATER ; IL N'A PAS LE DROIT DE PASSER.

    C'est toute la logique de cette fonction. On ne peut pas obliger un modèle
    vidéo à enchaîner : on lui donne la dernière image du plan précédent et un
    prompt, il rend ce qu'il veut. Parfois ça continue, parfois ça coupe.

    Alors on ne lui demande pas de réussir, on MESURE ce qu'il rend :

      - le plan commence-t-il bien là où le précédent finit ? (la jointure)
      - le plan lui-même est-il continu, ou coupe-t-il en son milieu ?

    Un plan qui rate l'un des deux est jeté et RECOMMANDÉ. Ce n'est donc pas le
    modèle qui garantit la continuité, c'est la boucle. Et si après `essais`
    tentatives ça ne tient toujours pas, on s'arrête : mieux vaut pas de film
    qu'un film qui saute.

    Les seuils ne sont pas choisis, ils sont mesurés. Sur les six plans du film
    menuiserie, les vraies jointures tiennent entre 3,3 et 5,3 sur 255 — le
    bruit de recompression — et les fausses dépassent 35. Il n'y a pas de zone
    grise entre les deux, c'est ce qui rend le contrôle sûr.

    `tolerer_coupes` N'EXISTE QUE POUR LES CLIPS D'ESSAI, et il faut savoir
    pourquoi. Les six plans de référence viennent de « Extend », qui ne
    continue pas un plan : il le prolonge une à deux secondes puis COUPE vers
    ce qu'on décrit. Mesuré sur ces plans — coupes aux images 4, 33 et 38, de
    36 à 45 sur 255, soit quatre à six fois le mouvement normal ; sur un plan
    sain le maximum reste à 1,3 fois. Ce pont du début est justement ce qui
    fait tenir la jointure : le rogner ne supprime pas la coupe, il la déplace.
    Avec Extend, une coupure par plan est donc inévitable.

    Une vraie interface `first_frame` n'a pas ce défaut : le modèle part de
    l'image donnée et avance. C'est pour l'attraper si elle se comporte quand
    même comme Extend que le contrôle existe — alors en production il reste à
    faux, toujours.
    """
    plans, amorce, journal_essais = [], None, []
    for i, prompt in enumerate(prompts_, 1):
        for essai in range(1, essais + 1):
            chemin = os.path.join(travail, f"plan{i}.mp4")
            journal(f"  plan {i}/{len(prompts_)}"
                    + (f" — tentative {essai}" if essai > 1 else ""))
            fournisseur.generer(prompt, chemin, amorce=amorce)

            faute = None
            pr = profiler(chemin)
            if pr["coupes"] and not tolerer_coupes:
                faute = f"coupe interne à {pr['coupes']}"
            elif plans:
                e = _ecart(_image(plans[-1], -1), _image(chemin, 0))
                if e > seuil:
                    faute = f"ne suit pas le plan {i - 1} — {e:.1f}/255"
                else:
                    journal(f"    jointure {e:.1f}/255")
            journal_essais.append((i, essai, faute))
            if not faute:
                break
            journal(f"    REJETÉ : {faute}")
        else:
            raise RuntimeError(
                f"le plan {i} n'enchaîne toujours pas après {essais} "
                f"tentatives.\nDernière faute : {faute}\n\n"
                "On s'arrête là volontairement. Un film dont les plans ne se\n"
                "suivent pas montre six ateliers différents — c'est pire\n"
                "qu'un site sans film.")
        plans.append(chemin)
        amorce = derniere_image(chemin, os.path.join(travail, f"amorce{i}.jpg"))
    return plans, journal_essais


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


def _essai_boucle(dossier):
    """Éprouve la boucle de reprise, sans clé et sans réseau.

    Six plans qui s'enchaînent tous du premier coup ne font JAMAIS tourner la
    boucle : on ne saurait pas si elle marche. On se sert donc d'un fournisseur
    qui rate exprès, et on vérifie les deux sens — qu'elle rattrape un plan
    fautif, et qu'elle refuse quand ça ne tient toujours pas.

    Un garde-fou qu'on n'a jamais vu refuser n'est pas un garde-fou.
    """
    import tempfile
    sys.path.insert(0, ICI)
    from fournisseur import Capricieux

    plans = sorted(glob.glob(os.path.join(dossier, "*.mp4")))
    if len(plans) < 3:
        sys.exit(f"il faut au moins trois .mp4 dans {dossier}")

    print(f"{len(plans)} plans — on mesure d'abord leur ordre réel\n")
    vrai, _, faute = chainer(plans)
    if faute:
        sys.exit(f"les plans d'essai ne s'enchaînent pas : {faute}")
    for a, b in zip(vrai, vrai[1:]):
        print(f"  {os.path.basename(a):20s} -> {os.path.basename(b)}")

    ok = []

    def verifier(titre, condition, detail=""):
        ok.append(bool(condition))
        print(f"  {'ok  ' if condition else 'NON '} {titre}"
              + (f"  {detail}" if detail else ""))

    faux_sujets = ["un sujet"] * 6
    p6 = prompts(faux_sujets)[:len(vrai)]

    # Les clips de référence viennent d'« Extend » : trois d'entre eux portent
    # une coupe interne (images 4, 33, 38). On éprouve donc les deux règles
    # séparément — la jointure ici, la coupe juste après.
    coupus = [p for p in vrai if profiler(p)["coupes"]]
    print(f"\n  ({len(coupus)}/{len(vrai)} de ces clips portent une coupe "
          f"interne — signature d'« Extend »)")

    # 1. Le plan 3 rate deux fois, puis passe. La boucle doit rattraper.
    print("\nLE PLAN 3 RATE DEUX FOIS (essais=3)")
    t = tempfile.mkdtemp()
    f = Capricieux(vrai, rates={3: 2})
    rendu, journal = produire(f, p6, t, essais=3, journal=lambda *_: None,
                              tolerer_coupes=True)
    rejets = [(i, e) for i, e, faute in journal if faute]
    verifier("les six plans sortent quand même", len(rendu) == len(vrai),
             f"{len(rendu)}/{len(vrai)}")
    verifier("deux rejets, tous deux sur le plan 3",
             len(rejets) == 2 and all(i == 3 for i, _ in rejets), str(rejets))
    verifier("le fournisseur a bien été appelé deux fois de plus",
             f.appels == len(vrai) + 2, f"{f.appels} appels")
    ordres = [os.path.getsize(p) for p in rendu]
    attendus = [os.path.getsize(p) for p in vrai]
    verifier("l'ordre final est le bon", ordres == attendus)
    for a, b in zip(rendu, rendu[1:]):
        e = _ecart(_image(a, -1), _image(b, 0))
        if e > 8.0:
            verifier("toutes les jointures tiennent", False, f"{e:.1f}/255")
            break
    else:
        verifier("toutes les jointures tiennent", True)

    # 2. Le plan 3 rate plus souvent qu'on n'a d'essais. Doit REFUSER.
    print("\nLE PLAN 3 RATE TROIS FOIS (essais=2) — doit refuser")
    t = tempfile.mkdtemp()
    try:
        produire(Capricieux(vrai, rates={3: 3}), p6, t, essais=2,
                 journal=lambda *_: None, tolerer_coupes=True)
        verifier("la boucle s'arrête au lieu de livrer un film qui saute",
                 False, "elle a livré")
    except RuntimeError as e:
        verifier("la boucle s'arrête au lieu de livrer un film qui saute",
                 "plan 3" in str(e))
        verifier("et elle dit pourquoi", "ne suit pas" in str(e))

    # 3. L'autre règle : une coupe DANS un plan est fatale aussi.
    if coupus:
        print("\nUN PLAN QUI COUPE EN SON MILIEU — doit refuser aussi")
        t = tempfile.mkdtemp()
        # On place un plan coupé en tête : sa jointure n'est pas en cause,
        # seule sa coupe interne peut le faire rejeter.
        try:
            produire(Capricieux([coupus[0]]), p6[:1], t, essais=1,
                     journal=lambda *_: None)
            verifier("une coupe interne fait rejeter le plan", False,
                     "il est passé")
        except RuntimeError as e:
            verifier("une coupe interne fait rejeter le plan",
                     "coupe interne" in str(e), str(e).splitlines()[0][:60])

    print(f"\n{sum(ok)}/{len(ok)} — "
          + ("la boucle tient." if all(ok) else "IL RESTE UN DÉFAUT."))
    return 0 if all(ok) else 1


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__.strip())
    if sys.argv[1] == "essai":
        d = _drapeau("plans")
        if not d:
            sys.exit("python3 monteuse.py essai plans=<dossier de .mp4>")
        sys.exit(_essai_boucle(d))
    nom = sys.argv[1]
    contrat = os.path.join(ICI, f"manifeste-{nom}.json")
    if not os.path.exists(contrat):
        sys.exit(f"{contrat} est introuvable — lancer d'abord nouveau.py")
    m = json.load(open(contrat, encoding="utf-8"))
    film = m["film"]["series"]["accueil"]["dossier"]["valeur"]

    dossier = _drapeau("plans")
    api = _drapeau("api")

    # DEUX MODES, ET LA DIFFÉRENCE EST DANS L'ORDRE.
    #
    #   génération : on commande les plans un par un, chacun amorcé par la
    #                dernière image du précédent. L'ordre est connu PAR
    #                CONSTRUCTION, et chaque jointure est vérifiée au moment
    #                où elle arrive — un plan qui ne suit pas est recommandé.
    #
    #   rejeu      : six fichiers sont là, leur ordre est inconnu. On le
    #                MESURE. Sur le film menuiserie, l'ordre des noms n'était
    #                pas l'ordre réel — s'y fier donnait un film qui saute
    #                trois fois.
    if api:
        from fournisseur import ouvrir, Refus
        sujets = m["film"].get("sujets")
        if not sujets or len(sujets) != 6:
            sys.exit("le manifeste n'a pas ses six « sujets » de plan.\n"
                     "C'est l'architecte qui les écrit — un par plan, une "
                     "phrase chacun.")
        travail = os.path.join(SITE, "assets", "plans", nom)
        os.makedirs(travail, exist_ok=True)
        print(f"GÉNÉRATION — six plans, chacun amorcé par le précédent\n")
        try:
            f = ouvrir(api, _drapeau("cle"), journal=print)
            ordre, _ = produire(f, prompts(sujets), travail,
                                essais=int(_drapeau("essais", 3)))
        except Refus as e:
            sys.exit(f"\nle fournisseur vidéo refuse :\n{e}")
        plans = ordre
        print()
    else:
        if not dossier:
            sys.exit("ni `plans=` (rejeu) ni `api=` (génération) — "
                     "la monteuse ne sait pas d'où sortir les plans")
        plans = sorted(glob.glob(os.path.join(dossier, "*.mp4")))
        if not plans:
            sys.exit(f"aucun .mp4 dans {dossier}")
        ordre = None

    print(f"{len(plans)} plans\n")
    print("PROFIL")
    total = 0
    for p in plans:
        pr = profiler(p)
        total += pr["images"]
        print(f"  {os.path.basename(p):32s} {pr['images']:4d} images · "
              + (f"coupe(s) à {pr['coupes']}" if pr["coupes"] else "aucune coupe"))

    if ordre:
        print("\nCHAÎNE — vérifiée plan par plan pendant la génération")
        ecarts = {(a, b): _ecart(_image(a, -1), _image(b, 0))
                  for a, b in zip(ordre, ordre[1:])}
    else:
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
